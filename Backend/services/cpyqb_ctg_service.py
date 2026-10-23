"""
CPYQB (Chapter-wise PYQ Bank), Custom Test Generator (CTG) & NCERT Modules Service

Implements:
- Hierarchical PYQ browsing and granular filtering (year, shift, MCQ/NAT, difficulty,
  attempt status, revision zone)
- Single-Question Practice Mode with instant verification, NAT tolerance checking,
  gamification points, heatmap logging, and automatic Error Notebook population
- Multi-Step Custom Test Generator (Step 1, Step 2, Generate, Submit, Diagnostic Analysis)
- NEET NCERT Line-by-Line Modules & Revision Zones

Uses Firestore when available with a synchronized in-memory store for deterministic
low-latency access and test isolation.

Author: Mentor AI Team
Version: 1.0.0
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from models.marks_sathee_models import (
    CTGChapterInfo,
    CTGExamSummary,
    CTGGeneratedTestResponse,
    CTGGenerateRequest,
    CTGStep1Response,
    CTGStep2Request,
    CTGStep2Response,
    CTGSubjectSummary,
    CTGSubmitRequest,
    CTGSubmitResponse,
    NcertModuleItem,
    NcertModuleListResponse,
    PYQOption,
    PYQQuestionItem,
    PYQQuestionListResponse,
    PracticeAttemptRequest,
    PracticeAttemptResponse,
    UserAttemptState,
)

logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "pyq_and_colleges.json",
)

# Shared in-memory state (mirrored to Firestore when initialized)
_STATE: Dict[str, Any] = {
    "user_attempts": {},      # {student_id: {question_id: {status, selectedOption, numericalAnswer, isStarred}}}
    "custom_tests": {},       # {test_id: dict}
    "custom_attempts": {},    # {attempt_id: dict}
}


def _try_get_db():
    """Return Firestore client if initialized and reachable, else None."""
    try:
        from utils.firebase_config import get_firestore_client, is_firebase_initialized
        if is_firebase_initialized():
            return get_firestore_client()
    except Exception as exc:
        logger.debug(f"Firestore unavailable, using in-memory store: {exc}")
    return None


def load_pyq_dataset(path: str = DATA_FILE) -> Dict[str, Any]:
    """Load curated PYQ, NCERT module, and college cutoff dataset."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error(f"Failed to load {path}: {exc}")
        return {"pyq_questions": [], "ncert_modules": [], "colleges": []}


def evaluate_question_attempt(
    question: Dict[str, Any],
    selected_option: Optional[str],
    numerical_answer: Optional[float],
) -> Tuple[bool, int]:
    """
    Pure grading logic for Single-Correct MCQ and Numerical Answer Type (NAT).
    Returns (is_correct, marks_awarded).
    """
    q_type = (question.get("type") or "MCQ").upper()
    correct_marks = int(question.get("correctMarks", 4))
    negative_marks = int(question.get("negativeMarks", -1))

    if q_type == "NAT":
        if numerical_answer is None:
            return False, 0
        target = float(question.get("numericalAnswer", 0.0))
        tol = float(question.get("numericalTolerance", 0.1))
        is_correct = abs(float(numerical_answer) - target) <= tol
        return is_correct, (correct_marks if is_correct else 0)

    # MCQ
    if not selected_option:
        return False, 0
    is_correct = selected_option.strip().upper() == (question.get("correctOption") or "").strip().upper()
    return is_correct, (correct_marks if is_correct else negative_marks)


class CPYQBAndCTGService:
    """Service managing PYQ Bank, Practice Mode, Custom Test Generator, and NCERT modules."""

    def __init__(
        self,
        error_recorder: Optional[Callable[..., Dict[str, Any]]] = None,
        heatmap_recorder: Optional[Callable[[str, int], None]] = None,
    ):
        self.dataset = load_pyq_dataset()
        self.questions: List[Dict[str, Any]] = self.dataset.get("pyq_questions", [])
        self.questions_by_id: Dict[str, Dict[str, Any]] = {q["id"]: q for q in self.questions}
        self.ncert_modules: List[Dict[str, Any]] = self.dataset.get("ncert_modules", [])
        self.error_recorder = error_recorder
        self.heatmap_recorder = heatmap_recorder

    def _get_student_attempts(self, student_id: str) -> Dict[str, Dict[str, Any]]:
        return _STATE["user_attempts"].setdefault(student_id, {})

    def _to_pyq_item(
        self, q: Dict[str, Any], idx: int, student_attempts: Dict[str, Dict[str, Any]]
    ) -> PYQQuestionItem:
        att = student_attempts.get(q["id"], {})
        return PYQQuestionItem(
            id=q["id"],
            questionNumber=idx,
            examId=q["examId"],
            exam=q["exam"],
            subjectId=q["subjectId"],
            subject=q["subject"],
            chapterId=q["chapterId"],
            chapter=q["chapter"],
            topicId=q["topicId"],
            topic=q["topic"],
            year=int(q["year"]),
            shift=q["shift"],
            type=q["type"],
            difficulty=q.get("difficulty", "medium"),
            revisionZone=q.get("revisionZone", "high_yield"),
            ncertPages=q.get("ncertPages"),
            statementHtml=q["statementHtml"],
            options=[PYQOption(**opt) for opt in q.get("options", [])],
            hasVideoSolution=bool(q.get("hasVideoSolution", False)),
            videoContentId=q.get("videoContentId"),
            userAttempt=UserAttemptState(
                status=att.get("status", "unattempted"),
                selectedOption=att.get("selectedOption"),
                numericalAnswer=att.get("numericalAnswer"),
                isStarred=bool(att.get("isStarred", False)),
            ),
        )

    # ─── 1. Chapter-wise PYQ Bank ────────────────────────────────────────

    def list_questions(
        self,
        student_id: str,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        pyq_filter: str = "all",
        years: Optional[str] = None,
        q_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        revision_zone: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PYQQuestionListResponse:
        student_attempts = self._get_student_attempts(student_id)
        year_set = None
        if years:
            year_set = {
                int(y.strip()) for y in years.split(",") if y.strip().isdigit()
            }

        filtered: List[Dict[str, Any]] = []
        for q in self.questions:
            if exam_id and exam_id.lower() != "all" and q["examId"].lower() != exam_id.lower():
                continue
            if subject_id and subject_id.lower() != "all" and q["subjectId"].lower() != subject_id.lower():
                continue
            if chapter_id and chapter_id.lower() != "all" and q["chapterId"].lower() != chapter_id.lower():
                continue
            if topic_id and topic_id.lower() != "all" and q["topicId"].lower() != topic_id.lower():
                continue
            if year_set and int(q["year"]) not in year_set:
                continue
            if q_type and q["type"].lower() != q_type.lower():
                continue
            if difficulty and q.get("difficulty", "").lower() != difficulty.lower():
                continue
            if revision_zone and q.get("revisionZone", "").lower() != revision_zone.lower():
                continue

            att = student_attempts.get(q["id"], {})
            att_status = att.get("status", "unattempted")
            is_starred = bool(att.get("isStarred", False))

            pf = (pyq_filter or "all").lower()
            if pf == "unattempted" and att_status != "unattempted":
                continue
            if pf == "incorrect" and att_status != "incorrect":
                continue
            if pf == "correct" and att_status != "correct":
                continue
            if pf == "starred" and not is_starred:
                continue

            filtered.append(q)

        total = len(filtered)
        sliced = filtered[offset : offset + limit]
        items = [
            self._to_pyq_item(q, offset + i + 1, student_attempts)
            for i, q in enumerate(sliced)
        ]
        return PYQQuestionListResponse(
            totalCount=total,
            questions=items,
        )

    # ─── 2. Single-Question Practice Mode ────────────────────────────────

    def submit_practice_attempt(
        self, student_id: str, request: PracticeAttemptRequest
    ) -> PracticeAttemptResponse:
        q = self.questions_by_id.get(request.questionId)
        if not q:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question not found: {request.questionId}",
            )

        is_correct, marks = evaluate_question_attempt(
            q, request.selectedOption, request.numericalAnswer
        )
        points_earned = 5 if is_correct else 1

        student_attempts = self._get_student_attempts(student_id)
        prev = student_attempts.get(q["id"], {})
        student_attempts[q["id"]] = {
            "status": "correct" if is_correct else "incorrect",
            "selectedOption": request.selectedOption,
            "numericalAnswer": request.numericalAnswer,
            "timeSpentSeconds": request.timeSpentSeconds,
            "isStarred": prev.get("isStarred", False),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        # Update daily activity heatmap
        if self.heatmap_recorder:
            self.heatmap_recorder(student_id, 1)

        # Log to Error Notebook if incorrect
        logged_error = False
        error_id = None
        if not is_correct and self.error_recorder:
            mistake_type = request.mistakeTag or q.get("commonMistakeType", "conceptual")
            err = self.error_recorder(
                student_id=student_id,
                question=q,
                student_selected=request.selectedOption
                or (str(request.numericalAnswer) if request.numericalAnswer is not None else "unanswered"),
                mistake_type=mistake_type,
                test_name="CPYQB Practice Mode",
            )
            logged_error = True
            error_id = err.get("errorId")

        db = _try_get_db()
        if db:
            try:
                db.collection("pyq_attempts").document(f"{student_id}_{q['id']}").set(
                    {
                        "student_id": student_id,
                        "question_id": q["id"],
                        **student_attempts[q["id"]],
                    }
                )
            except Exception as exc:
                logger.debug(f"Firestore write skipped for pyq_attempts: {exc}")

        return PracticeAttemptResponse(
            questionId=q["id"],
            isCorrect=is_correct,
            correctOption=q.get("correctOption"),
            correctNumericalAnswer=q.get("numericalAnswer"),
            marksAwarded=marks,
            solutionHtml=q["solutionHtml"],
            userPointsEarned=points_earned,
            loggedToErrorNotebook=logged_error,
            errorId=error_id,
        )

    # ─── 3. Custom Test Generator (CTG) ──────────────────────────────────

    def get_ctg_step1(self) -> CTGStep1Response:
        exams_map: Dict[str, Dict[str, Any]] = {
            "jee_main": {"id": "jee_main", "name": "JEE Main", "subjects": {}},
            "jee_advanced": {"id": "jee_advanced", "name": "JEE Advanced", "subjects": {}},
            "neet": {"id": "neet", "name": "NEET-UG", "subjects": {}},
        }
        for q in self.questions:
            ex_id = q["examId"]
            if ex_id not in exams_map:
                exams_map[ex_id] = {"id": ex_id, "name": q["exam"], "subjects": {}}
            subj_map = exams_map[ex_id]["subjects"]
            s_id = q["subjectId"]
            if s_id not in subj_map:
                subj_map[s_id] = {"id": s_id, "name": q["subject"], "availableQuestions": 0}
            subj_map[s_id]["availableQuestions"] += 1

        # Ensure standard subjects appear even if sample count is small
        defaults = {
            "jee_main": [("physics", "Physics"), ("chemistry", "Chemistry"), ("mathematics", "Mathematics")],
            "jee_advanced": [("physics", "Physics"), ("chemistry", "Chemistry"), ("mathematics", "Mathematics")],
            "neet": [("physics", "Physics"), ("chemistry", "Chemistry"), ("biology", "Biology")],
        }
        for ex_id, subj_list in defaults.items():
            for s_id, s_name in subj_list:
                if s_id not in exams_map[ex_id]["subjects"]:
                    exams_map[ex_id]["subjects"][s_id] = {
                        "id": s_id,
                        "name": s_name,
                        "availableQuestions": sum(
                            1 for q in self.questions if q["subjectId"] == s_id
                        ),
                    }

        exams = [
            CTGExamSummary(
                id=ex["id"],
                name=ex["name"],
                subjects=[CTGSubjectSummary(**s) for s in ex["subjects"].values()],
            )
            for ex in exams_map.values()
        ]
        return CTGStep1Response(exams=exams)

    def get_ctg_step2(self, request: CTGStep2Request) -> CTGStep2Response:
        wanted_subjects = {s.lower() for s in request.subjectIds}
        chapters_map: Dict[str, Dict[str, Any]] = {}
        for q in self.questions:
            if q["subjectId"].lower() not in wanted_subjects:
                continue
            ch_id = q["chapterId"]
            if ch_id not in chapters_map:
                chapters_map[ch_id] = {
                    "id": ch_id,
                    "name": q["chapter"],
                    "subject": q["subjectId"],
                    "totalQuestions": 0,
                }
            chapters_map[ch_id]["totalQuestions"] += 1

        return CTGStep2Response(
            chapters=[CTGChapterInfo(**c) for c in chapters_map.values()],
            suggestedTimeDurations=[30, 45, 60, 90, 180],
        )

    def generate_custom_test(
        self, student_id: str, request: CTGGenerateRequest
    ) -> CTGGeneratedTestResponse:
        wanted_subjects = {s.lower() for s in request.subjectIds}
        alloc_map = {a.chapterId.lower(): a.questionCount for a in request.chapterAllocations}

        selected: List[Dict[str, Any]] = []
        if alloc_map:
            for ch_id, count in alloc_map.items():
                pool = [
                    q for q in self.questions
                    if q["chapterId"].lower() == ch_id
                    and (
                        not request.difficulty
                        or request.difficulty == "mixed"
                        or q.get("difficulty", "").lower() == request.difficulty.lower()
                    )
                ]
                selected.extend(pool[:count])

        if not selected:
            # Fallback to subject filter across all available questions
            pool = [
                q for q in self.questions
                if q["subjectId"].lower() in wanted_subjects
            ]
            selected = pool if pool else list(self.questions)

        test_id = f"ct_{uuid.uuid4().hex[:8]}"
        title = request.title or f"Custom {request.examId.upper()} Practice Test"
        student_attempts = self._get_student_attempts(student_id)
        items = [
            self._to_pyq_item(q, idx + 1, student_attempts)
            for idx, q in enumerate(selected)
        ]
        total_marks = sum(int(q.get("correctMarks", 4)) for q in selected)

        test_record = {
            "testId": test_id,
            "studentId": student_id,
            "title": title,
            "examId": request.examId,
            "durationMinutes": request.durationMinutes,
            "totalQuestions": len(items),
            "totalMarks": total_marks,
            "questionIds": [q["id"] for q in selected],
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        _STATE["custom_tests"][test_id] = test_record

        return CTGGeneratedTestResponse(
            testId=test_id,
            title=title,
            examId=request.examId,
            durationMinutes=request.durationMinutes,
            totalQuestions=len(items),
            totalMarks=total_marks,
            questions=items,
        )

    def submit_custom_test(
        self, student_id: str, request: CTGSubmitRequest
    ) -> CTGSubmitResponse:
        test_record = _STATE["custom_tests"].get(request.testId)
        if test_record:
            q_ids = test_record["questionIds"]
            title = test_record["title"]
        else:
            q_ids = [r.questionId for r in request.responses]
            title = f"Custom Test {request.testId}"

        resp_by_qid = {r.questionId: r for r in request.responses}
        total_questions = max(len(q_ids), len(request.responses))
        total_marks = total_questions * 4

        score = 0
        attempted = 0
        correct = 0
        incorrect = 0
        subject_breakdown: Dict[str, Dict[str, Any]] = {}
        topic_stats: Dict[str, Dict[str, Any]] = {}
        question_details: List[Dict[str, Any]] = []

        for qid in q_ids:
            q = self.questions_by_id.get(qid)
            if not q:
                continue
            r = resp_by_qid.get(qid)
            subj = q["subject"]
            topic_key = f"{subj}|{q['topic']}"
            subject_breakdown.setdefault(subj, {"marks": 0, "correct": 0, "incorrect": 0, "unattempted": 0})
            topic_stats.setdefault(topic_key, {"subject": subj, "topic": q["topic"], "correct": 0, "incorrect": 0, "total": 0})
            topic_stats[topic_key]["total"] += 1

            is_answered = r is not None and r.status in ("answered", "answered_and_marked") and (
                r.selectedOption is not None or r.numericalValue is not None
            )
            if not is_answered:
                subject_breakdown[subj]["unattempted"] += 1
                question_details.append(
                    {
                        "questionId": qid,
                        "status": "unattempted",
                        "marks": 0,
                        "timeTaken": r.timeTaken if r else 0,
                        "correctOption": q.get("correctOption"),
                        "solutionHtml": q["solutionHtml"],
                    }
                )
                continue

            attempted += 1
            is_corr, marks = evaluate_question_attempt(q, r.selectedOption, r.numericalValue)
            score += marks
            subject_breakdown[subj]["marks"] += marks

            if is_corr:
                correct += 1
                subject_breakdown[subj]["correct"] += 1
                topic_stats[topic_key]["correct"] += 1
            else:
                incorrect += 1
                subject_breakdown[subj]["incorrect"] += 1
                topic_stats[topic_key]["incorrect"] += 1
                if self.error_recorder:
                    self.error_recorder(
                        student_id=student_id,
                        question=q,
                        student_selected=r.selectedOption
                        or (str(r.numericalValue) if r.numericalValue is not None else "unanswered"),
                        mistake_type=q.get("commonMistakeType", "conceptual"),
                        test_name=title,
                    )

            question_details.append(
                {
                    "questionId": qid,
                    "status": "correct" if is_corr else "incorrect",
                    "marks": marks,
                    "timeTaken": r.timeTaken,
                    "correctOption": q.get("correctOption"),
                    "solutionHtml": q["solutionHtml"],
                }
            )

        if self.heatmap_recorder and attempted > 0:
            self.heatmap_recorder(student_id, attempted)

        unattempted = max(0, total_questions - attempted)
        accuracy = round((correct / attempted) * 100.0, 2) if attempted > 0 else 0.0
        score_ratio = max(0.0, score / max(1, total_marks))
        percentile = round(min(99.95, 45.0 + score_ratio * 54.5), 2)

        weak_topics = [
            {"subject": v["subject"], "topic": v["topic"], "incorrectCount": v["incorrect"]}
            for v in topic_stats.values()
            if v["incorrect"] > 0
        ]
        strong_topics = [
            {
                "subject": v["subject"],
                "topic": v["topic"],
                "accuracy": round(v["correct"] / max(1, v["total"]), 2),
            }
            for v in topic_stats.values()
            if v["correct"] > 0 and v["incorrect"] == 0
        ]

        attempt_id = f"att_{uuid.uuid4().hex[:8]}"
        attempt_summary = {
            "attemptId": attempt_id,
            "testId": request.testId,
            "studentId": student_id,
            "testTitle": title,
            "totalMarks": total_marks,
            "score": score,
            "totalQuestions": total_questions,
            "attempted": attempted,
            "correct": correct,
            "incorrect": incorrect,
            "unattempted": unattempted,
            "accuracy": accuracy,
            "percentile": percentile,
            "timeTakenSeconds": request.timeTakenSeconds,
            "subjectBreakdown": subject_breakdown,
            "weakTopics": weak_topics,
            "strongTopics": strong_topics,
            "questionDetails": question_details,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        _STATE["custom_attempts"][attempt_id] = attempt_summary
        _STATE["custom_attempts"][f"by_test_{request.testId}"] = attempt_summary

        return CTGSubmitResponse(
            attemptId=attempt_id,
            testId=request.testId,
            totalMarks=total_marks,
            score=score,
            totalQuestions=total_questions,
            attempted=attempted,
            correct=correct,
            incorrect=incorrect,
            unattempted=unattempted,
            accuracy=accuracy,
            percentile=percentile,
            subjectBreakdown=subject_breakdown,
            weakTopics=weak_topics,
            strongTopics=strong_topics,
        )

    def get_custom_test_analysis(self, test_or_attempt_id: str) -> Dict[str, Any]:
        att = (
            _STATE["custom_attempts"].get(test_or_attempt_id)
            or _STATE["custom_attempts"].get(f"by_test_{test_or_attempt_id}")
        )
        if not att:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis not found for test/attempt: {test_or_attempt_id}",
            )

        total_marks = att["totalMarks"]
        avg_time = round(
            att["timeTakenSeconds"] / max(1, att["attempted"]), 1
        )
        return {
            "status": True,
            "code": 200,
            "data": {
                "attemptId": att["attemptId"],
                "testId": att["testId"],
                "testTitle": att["testTitle"],
                "studentScore": att["score"],
                "totalMarks": total_marks,
                "topperScore": int(total_marks * 0.95),
                "averageScore": int(total_marks * 0.42),
                "accuracy": att["accuracy"],
                "percentile": att["percentile"],
                "speedMetrics": {
                    "averageTimePerQuestionSeconds": avg_time,
                    "topperAverageTimeSeconds": 65.0,
                },
                "subjectBreakdown": att["subjectBreakdown"],
                "weakTopics": att["weakTopics"],
                "strongTopics": att["strongTopics"],
                "questionDetails": att["questionDetails"],
            },
        }

    # ─── 4. NEET NCERT Line-by-Line Modules ──────────────────────────────

    def get_ncert_modules(
        self, student_id: str, subject_id: str
    ) -> NcertModuleListResponse:
        student_attempts = self._get_student_attempts(student_id)
        subj_lower = subject_id.lower()
        modules: List[NcertModuleItem] = []

        for mod in self.ncert_modules:
            if subj_lower != "all" and mod["subjectId"].lower() != subj_lower:
                continue
            ch_id = mod["chapterId"]
            completed_in_chapter = sum(
                1
                for q in self.questions
                if q["chapterId"] == ch_id
                and student_attempts.get(q["id"], {}).get("status") in ("correct", "incorrect")
            )
            modules.append(
                NcertModuleItem(
                    moduleId=mod["moduleId"],
                    subjectId=mod["subjectId"],
                    book=mod["book"],
                    chapterId=ch_id,
                    chapterName=mod["chapterName"],
                    ncertPages=mod["ncertPages"],
                    totalQuestions=mod["totalQuestions"],
                    completedQuestions=completed_in_chapter,
                    highYieldCount=mod.get("highYieldCount", 40),
                    mustReviseCount=mod.get("mustReviseCount", 40),
                    trapZoneCount=mod.get("trapZoneCount", 20),
                )
            )

        return NcertModuleListResponse(subjectId=subject_id, modules=modules)
