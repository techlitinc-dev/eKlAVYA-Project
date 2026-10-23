"""
Revision Flash Cards (RFC), Smart Notebooks, Error Notebook, Homework Assignments,
Daily Goals Heatmap, Daily Dose & Weekly Leagues Service

Implements:
- Revision Flash Cards & Formula Cards seeded from syllabus JSONs + curated LaTeX deck
- Smart Notebooks (create, pin/archive, bookmark question with personal note)
- Automated Error Notebook (populated on wrong PYQ/Test attempts, mistake categorization,
  mastery resolution)
- Teacher / Parent Homework Assignments (create with 6-char joinCode, student attempt,
  classroom analytics with question-level error rates)
- Daily Goals & GitHub-style Monthly Activity Heatmap
- Daily Dose 5-Question Sprint & Weekly League Leaderboards (Bronze -> Master)

Author: Mentor AI Team
Version: 1.0.0
"""

import calendar
import glob
import hashlib
import json
import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from models.marks_sathee_models import (
    AssignmentClassroomAnalytics,
    AssignmentSubmitRequest,
    BookmarkToNotebookRequest,
    CreateAssignmentRequest,
    CreateAssignmentResponse,
    CreateNotebookRequest,
    DailyDoseSubmitRequest,
    ErrorNotebookEntry,
    ErrorNotebookListResponse,
    FlashCardDeckResponse,
    FlashCardItem,
    FlashCardMasteryRequest,
    HeatmapDayItem,
    LeaderboardLeaguesResponse,
    MonthlyHeatmapResponse,
    NotebookItem,
    UpdateNotebookRequest,
)
from services.cpyqb_ctg_service import _STATE as _CPYQB_STATE, evaluate_question_attempt, load_pyq_dataset

logger = logging.getLogger(__name__)

SYLLABUS_GLOB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "syllabus",
    "*.json",
)

_ECOSYSTEM_STATE: Dict[str, Any] = {
    "rfc_mastery": {},        # {student_id: {card_id: "mastered" | "needs_revision"}}
    "notebooks": {},          # {student_id: {notebook_id: dict}}
    "notebook_questions": {}, # {notebook_id: {question_id: {"studentNote": str, "addedAt": str}}}
    "error_notebook": {},     # {student_id: {question_id: dict}}
    "assignments": {},        # {assignment_id: dict}
    "assignment_codes": {},   # {join_code: assignment_id}
    "daily_goals": {},        # {student_id: int}
    "daily_solved": {},       # {student_id: {"YYYY-MM-DD": int}}
    "weekly_points": {},      # {student_id: int}
}

CURATED_FLASHCARDS: List[Dict[str, Any]] = [
    {
        "cardId": "gauss_law",
        "subjectId": "physics",
        "chapterId": "electrostatics",
        "chapterName": "Electrostatics",
        "topicName": "Electric Flux & Gauss's Law",
        "title": "Gauss's Law & Electric Flux",
        "frontText": "What is the net electric flux through any closed Gaussian surface?",
        "backFormulaHtml": "<p>$$\\oint \\vec{E} \\cdot d\\vec{A} = \\frac{q_{\\text{enclosed}}}{\\varepsilon_0}$$</p>",
        "keyTakeaways": [
            "Net flux is independent of the shape or size of the closed Gaussian surface.",
            "Charges outside the Gaussian surface contribute zero net flux, though they affect E at points on the surface.",
        ],
    },
    {
        "cardId": "rolling_incline",
        "subjectId": "physics",
        "chapterId": "rotational_motion",
        "chapterName": "Rotational Motion",
        "topicName": "Rolling Without Slipping",
        "title": "Acceleration in Pure Rolling on an Incline",
        "frontText": "What is the linear acceleration of a rigid body of radius R and radius of gyration K rolling without slipping down an incline of angle θ?",
        "backFormulaHtml": "<p>$$a = \\frac{g \\sin \\theta}{1 + \\frac{I_{\\text{cm}}}{M R^2}} = \\frac{g \\sin \\theta}{1 + \\frac{K^2}{R^2}}$$</p>",
        "keyTakeaways": [
            "For a solid sphere (K²/R² = 2/5), a = (5/7) g sin θ.",
            "For a uniform disc/solid cylinder (K²/R² = 1/2), a = (2/3) g sin θ.",
            "Solid sphere reaches the bottom of the incline before a disc or hollow ring.",
        ],
    },
    {
        "cardId": "first_order_kinetics",
        "subjectId": "chemistry",
        "chapterId": "chemical_kinetics",
        "chapterName": "Chemical Kinetics",
        "topicName": "Integrated Rate Laws",
        "title": "First-Order Rate Law & Half-Life",
        "frontText": "State the integrated rate equation and half-life formula for a first-order chemical reaction.",
        "backFormulaHtml": "<p>$$k = \\frac{2.303}{t} \\log_{10}\\left(\\frac{[A]_0}{[A]_t}\\right), \\quad t_{1/2} = \\frac{\\ln 2}{k} = \\frac{0.693}{k}$$</p>",
        "keyTakeaways": [
            "First-order half-life is completely independent of initial reactant concentration [A]₀.",
            "Time for 99.9% completion is approximately 10 times the half-life (t_{99.9%} ≈ 10 × t_{1/2}).",
        ],
    },
    {
        "cardId": "kings_property",
        "subjectId": "mathematics",
        "chapterId": "definite_integration",
        "chapterName": "Definite Integration",
        "topicName": "Properties of Definite Integrals",
        "title": "King's Property of Definite Integrals",
        "frontText": "How does King's Property simplify definite integrals over [a, b] and [0, a]?",
        "backFormulaHtml": "<p>$$\\int_{a}^{b} f(x)\\,dx = \\int_{a}^{b} f(a + b - x)\\,dx, \\quad \\int_{0}^{a} f(x)\\,dx = \\int_{0}^{a} f(a - x)\\,dx$$</p>",
        "keyTakeaways": [
            "Adding I + I often cancels symmetric numerators and denominators, reducing the integrand to 1.",
            "Wait for bounds like [0, π/2] with sin(x) and cos(x) symmetry.",
        ],
    },
]


def load_all_flashcards(syllabus_glob: str = SYLLABUS_GLOB) -> List[Dict[str, Any]]:
    """Build flashcard library combining curated cards and syllabus formulas."""
    cards_by_id: Dict[str, Dict[str, Any]] = {c["cardId"]: dict(c) for c in CURATED_FLASHCARDS}

    for path in sorted(glob.glob(syllabus_glob)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        subj = (data.get("subject") or "Physics").lower()
        for ch in data.get("chapters", []):
            ch_name = ch.get("chapter_name", "General")
            ch_slug = ch_name.lower().replace(" ", "_")
            for top in ch.get("topics", []):
                top_name = top.get("topic_name", ch_name)
                for sub in top.get("subtopics", []):
                    formulas = sub.get("formulas") or []
                    concepts = sub.get("key_concepts") or []
                    if not formulas and not concepts:
                        continue
                    sub_name = sub.get("subtopic_name", top_name)
                    cid = "rfc_" + hashlib.md5(f"{subj}|{ch_slug}|{sub_name}".encode()).hexdigest()[:8]
                    if cid in cards_by_id:
                        continue
                    formula_html = (
                        "<p>" + "<br/>".join(f"$${fm}$$" for fm in formulas) + "</p>"
                        if formulas
                        else f"<p>{sub.get('content', '')}</p>"
                    )
                    cards_by_id[cid] = {
                        "cardId": cid,
                        "subjectId": subj,
                        "chapterId": ch_slug,
                        "chapterName": ch_name,
                        "topicName": top_name,
                        "title": sub_name,
                        "frontText": f"Review key formulas and concepts for {sub_name} ({ch_name}).",
                        "backFormulaHtml": formula_html,
                        "keyTakeaways": concepts[:4] if concepts else [sub.get("content", "")[:120]],
                    }

    return list(cards_by_id.values())


def determine_league(weekly_points: int) -> Tuple[str, Optional[int]]:
    """Pure function mapping weekly points to League name and next tier threshold."""
    if weekly_points < 200:
        return "Bronze", 200
    if weekly_points < 500:
        return "Silver", 500
    if weekly_points < 900:
        return "Gold", 900
    if weekly_points < 1500:
        return "Diamond", 1500
    return "Master", None


from typing import Tuple  # ensure Tuple is available above


class MarksEcosystemService:
    """Service managing RFC, Smart Notebooks, Error Notebook, Assignments, Heatmaps & Leagues."""

    def __init__(self):
        self.reload_dataset()
        self._seed_defaults()

    def reload_dataset(self) -> None:
        self.cards = load_all_flashcards()
        self.cards_by_id = {c["cardId"]: c for c in self.cards}
        self.pyq_data = load_pyq_dataset()
        self.questions = self.pyq_data.get("pyq_questions", [])
        self.questions_by_id = {q["id"]: q for q in self.questions}

    def _seed_defaults(self) -> None:
        """Seed realistic initial activity, notebooks, errors, and assignment 6X9A21 if empty."""
        if "6X9A21" not in _ECOSYSTEM_STATE["assignment_codes"]:
            q_ids = [
                q["id"]
                for q in self.questions[:4]
                if q["id"] in self.questions_by_id
            ]
            if q_ids:
                as_id = "as_demo_6x9a21"
                now_iso = datetime.now(timezone.utc).isoformat()
                _ECOSYSTEM_STATE["assignments"][as_id] = {
                    "assignmentId": as_id,
                    "creatorId": "parent_demo_01",
                    "title": "Weekly Electrostatics, Rotation & Calculus Drill",
                    "subjectId": "physics",
                    "questionIds": q_ids,
                    "dueDate": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                    "timeLimitMinutes": 30,
                    "joinCode": "6X9A21",
                    "shareUrl": "https://link.getmarks.app/assignment/student?code=6X9A21",
                    "submissions": [
                        {
                            "submissionId": "sub_demo_01",
                            "studentId": "Aarav Sharma",
                            "score": 12,
                            "totalMarks": len(q_ids) * 4,
                            "correct": 3,
                            "incorrect": 0,
                            "timeTakenSeconds": 340,
                            "perQuestionCorrect": {qid: (idx < 3) for idx, qid in enumerate(q_ids)},
                            "submittedAt": now_iso,
                        },
                        {
                            "submissionId": "sub_demo_02",
                            "studentId": "Priya Nair",
                            "score": 7,
                            "totalMarks": len(q_ids) * 4,
                            "correct": 2,
                            "incorrect": 1,
                            "timeTakenSeconds": 410,
                            "perQuestionCorrect": {qid: (idx < 2) for idx, qid in enumerate(q_ids)},
                            "submittedAt": now_iso,
                        },
                    ],
                    "createdAt": now_iso,
                }
                _ECOSYSTEM_STATE["assignment_codes"]["6X9A21"] = as_id

    def _ensure_student_seeded(self, student_id: str) -> None:
        """Populate realistic baseline heatmap, notebooks, and error notebook for a student on first read."""
        if student_id not in _ECOSYSTEM_STATE["daily_solved"]:
            today = date.today()
            solved_map: Dict[str, int] = {}
            sample_counts = [28, 34, 31, 18, 35, 40, 22, 30, 33, 36, 29, 32, 42, 31]
            for idx, cnt in enumerate(sample_counts):
                d = today - timedelta(days=idx)
                solved_map[d.isoformat()] = cnt
            _ECOSYSTEM_STATE["daily_solved"][student_id] = solved_map
            _ECOSYSTEM_STATE["weekly_points"].setdefault(student_id, 640)

        if student_id not in _ECOSYSTEM_STATE["notebooks"]:
            now_iso = datetime.now(timezone.utc).isoformat()
            nb1 = "nb_rotational_traps"
            nb2 = "nb_high_yield_kinetics"
            _ECOSYSTEM_STATE["notebooks"][student_id] = {
                nb1: {
                    "notebookId": nb1,
                    "title": "Rotational Motion & Electrostatics Traps",
                    "colorHex": "#1589EE",
                    "subjectId": "physics",
                    "isPinned": True,
                    "isArchived": False,
                    "createdAt": now_iso,
                },
                nb2: {
                    "notebookId": nb2,
                    "title": "High-Yield Kinetics & Calculus",
                    "colorHex": "#10B981",
                    "subjectId": "chemistry",
                    "isPinned": False,
                    "isArchived": False,
                    "createdAt": now_iso,
                },
            }
            _ECOSYSTEM_STATE["notebook_questions"].setdefault(
                nb1,
                {
                    "q_jee_2024_ph_01": {
                        "questionId": "q_jee_2024_ph_01",
                        "studentNote": "Use I = (2/5)MR² for solid sphere rolling without slipping: a = g sinθ / (1 + K²/R²).",
                        "addedAt": now_iso,
                    },
                    "q_jee_2023_ph_03": {
                        "questionId": "q_jee_2023_ph_03",
                        "studentNote": "Check equilibrium of extreme charge Q, not just central charge q!",
                        "addedAt": now_iso,
                    },
                },
            )
            _ECOSYSTEM_STATE["notebook_questions"].setdefault(
                nb2,
                {
                    "q_jee_2024_ch_01": {
                        "questionId": "q_jee_2024_ch_01",
                        "studentNote": "t_99.9% = 10 × t_1/2 for any first-order reaction.",
                        "addedAt": now_iso,
                    }
                },
            )

        if student_id not in _ECOSYSTEM_STATE["error_notebook"]:
            err_bucket: Dict[str, Dict[str, Any]] = {}
            now_iso = datetime.now(timezone.utc).isoformat()
            for qid, mtype, sel in [
                ("q_jee_2023_ph_03", "conceptual", "A"),
                ("q_jee_2024_ph_02", "calculation", "18.0"),
            ]:
                q = self.questions_by_id.get(qid)
                if q:
                    err_bucket[qid] = {
                        "errorId": f"err_seed_{qid[-5:]}",
                        "questionId": qid,
                        "testName": "CPYQB Practice Mode",
                        "subject": q["subject"],
                        "chapter": q["chapter"],
                        "topic": q["topic"],
                        "questionText": q["statementHtml"],
                        "studentSelectedOption": sel,
                        "correctOption": q.get("correctOption") or str(q.get("numericalAnswer")),
                        "solutionText": q["solutionHtml"],
                        "mistakeType": mtype,
                        "attemptCount": 2,
                        "isMastered": False,
                        "createdAt": now_iso,
                    }
            _ECOSYSTEM_STATE["error_notebook"][student_id] = err_bucket

    # ─── 1. Revision Flash Cards (RFC) & Formula Cards ───────────────────

    def get_chapter_cards(
        self, student_id: str, subject_id: str, chapter_id: str
    ) -> FlashCardDeckResponse:
        mastery_map = _ECOSYSTEM_STATE["rfc_mastery"].setdefault(student_id, {})
        subj_l = subject_id.lower()
        ch_l = chapter_id.lower()

        matched = [
            c
            for c in self.cards
            if (subj_l == "all" or c["subjectId"].lower() == subj_l)
            and (ch_l == "all" or c["chapterId"].lower() == ch_l)
        ]
        if not matched:
            # Fallback to subject match so students always get a playable deck
            matched = [c for c in self.cards if c["subjectId"].lower() == subj_l] or self.cards[:5]

        items: List[FlashCardItem] = []
        mastered_count = 0
        needs_rev_count = 0
        for c in matched:
            level = mastery_map.get(c["cardId"], "unseen")
            if level == "mastered":
                mastered_count += 1
            elif level == "needs_revision":
                needs_rev_count += 1
            items.append(FlashCardItem(**c, userMasteryLevel=level))

        return FlashCardDeckResponse(
            subjectId=subject_id,
            chapterId=chapter_id,
            totalCards=len(items),
            masteredCount=mastered_count,
            needsRevisionCount=needs_rev_count,
            cards=items,
        )

    def get_single_card(
        self, student_id: str, subject_id: str, chapter_id: str, card_id: str
    ) -> Dict[str, Any]:
        card = self.cards_by_id.get(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flashcard not found: {card_id}",
            )
        mastery_map = _ECOSYSTEM_STATE["rfc_mastery"].setdefault(student_id, {})
        level = mastery_map.get(card_id, "unseen")
        return {
            "status": True,
            "code": 200,
            "data": FlashCardItem(**card, userMasteryLevel=level).model_dump(),
        }

    def update_card_mastery(
        self, student_id: str, request: FlashCardMasteryRequest
    ) -> Dict[str, Any]:
        if request.cardId not in self.cards_by_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flashcard not found: {request.cardId}",
            )
        mastery_map = _ECOSYSTEM_STATE["rfc_mastery"].setdefault(student_id, {})
        mastery_map[request.cardId] = request.masteryLevel
        if request.masteryLevel == "mastered":
            self.add_weekly_points(student_id, 5)
        return {
            "status": True,
            "code": 200,
            "message": "Card mastery updated",
            "data": {
                "cardId": request.cardId,
                "userMasteryLevel": request.masteryLevel,
            },
        }

    # ─── 2. Smart Notebooks & Bookmarking ────────────────────────────────

    def create_notebook(
        self, student_id: str, request: CreateNotebookRequest
    ) -> NotebookItem:
        nb_map = _ECOSYSTEM_STATE["notebooks"].setdefault(student_id, {})
        nb_id = f"nb_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        record = {
            "notebookId": nb_id,
            "title": request.title.strip(),
            "colorHex": request.colorHex,
            "subjectId": request.subjectId,
            "isPinned": False,
            "isArchived": False,
            "createdAt": now_iso,
        }
        nb_map[nb_id] = record
        _ECOSYSTEM_STATE["notebook_questions"].setdefault(nb_id, {})
        return NotebookItem(**record, questionCount=0)

    def list_notebooks(
        self, student_id: str, include_archived: bool = False
    ) -> List[NotebookItem]:
        self._ensure_student_seeded(student_id)
        nb_map = _ECOSYSTEM_STATE["notebooks"].setdefault(student_id, {})
        result: List[NotebookItem] = []
        for nb_id, nb in nb_map.items():
            if not include_archived and nb.get("isArchived", False):
                continue
            q_count = len(_ECOSYSTEM_STATE["notebook_questions"].get(nb_id, {}))
            result.append(NotebookItem(**nb, questionCount=q_count))
        result.sort(key=lambda x: (not x.isPinned, x.createdAt))
        return result

    def update_notebook(
        self, student_id: str, notebook_id: str, request: UpdateNotebookRequest
    ) -> NotebookItem:
        self._ensure_student_seeded(student_id)
        nb_map = _ECOSYSTEM_STATE["notebooks"].setdefault(student_id, {})
        nb = nb_map.get(notebook_id)
        if not nb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notebook not found: {notebook_id}",
            )
        if request.title is not None:
            nb["title"] = request.title.strip()
        if request.colorHex is not None:
            nb["colorHex"] = request.colorHex
        if request.isPinned is not None:
            nb["isPinned"] = request.isPinned
        if request.isArchived is not None:
            nb["isArchived"] = request.isArchived
        q_count = len(_ECOSYSTEM_STATE["notebook_questions"].get(notebook_id, {}))
        return NotebookItem(**nb, questionCount=q_count)

    def bookmark_question(
        self, student_id: str, request: BookmarkToNotebookRequest
    ) -> Dict[str, Any]:
        if request.questionId not in self.questions_by_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question not found: {request.questionId}",
            )
        nb_map = _ECOSYSTEM_STATE["notebooks"].setdefault(student_id, {})
        now_iso = datetime.now(timezone.utc).isoformat()

        for nb_id in request.notebookIds:
            if nb_id not in nb_map:
                # Auto-create notebook if client passes a semantic ID like "nb_difficult_rotation"
                nb_map[nb_id] = {
                    "notebookId": nb_id,
                    "title": nb_id.replace("nb_", "").replace("_", " ").title(),
                    "colorHex": "#1589EE",
                    "subjectId": self.questions_by_id[request.questionId]["subjectId"],
                    "isPinned": False,
                    "isArchived": False,
                    "createdAt": now_iso,
                }
            q_bucket = _ECOSYSTEM_STATE["notebook_questions"].setdefault(nb_id, {})
            q_bucket[request.questionId] = {
                "questionId": request.questionId,
                "studentNote": request.studentNote or "",
                "addedAt": now_iso,
            }

        # Mark question as starred in student's CPYQB attempt state
        att_map = _CPYQB_STATE["user_attempts"].setdefault(student_id, {})
        cur = att_map.setdefault(request.questionId, {"status": "unattempted"})
        cur["isStarred"] = True

        return {
            "status": True,
            "code": 200,
            "message": "Question bookmarked successfully",
            "data": {
                "questionId": request.questionId,
                "notebookIds": request.notebookIds,
                "studentNote": request.studentNote,
            },
        }

    def get_notebook_questions(
        self, student_id: str, notebook_id: str
    ) -> Dict[str, Any]:
        self._ensure_student_seeded(student_id)
        nb_map = _ECOSYSTEM_STATE["notebooks"].setdefault(student_id, {})
        if notebook_id not in nb_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notebook not found: {notebook_id}",
            )
        q_bucket = _ECOSYSTEM_STATE["notebook_questions"].get(notebook_id, {})
        items = []
        for qid, meta in q_bucket.items():
            q = self.questions_by_id.get(qid)
            if not q:
                continue
            items.append(
                {
                    "questionId": qid,
                    "exam": q["exam"],
                    "year": q["year"],
                    "shift": q["shift"],
                    "subject": q["subject"],
                    "chapter": q["chapter"],
                    "topic": q["topic"],
                    "statementHtml": q["statementHtml"],
                    "options": q["options"],
                    "studentNote": meta.get("studentNote", ""),
                    "addedAt": meta.get("addedAt"),
                }
            )
        return {
            "status": True,
            "code": 200,
            "notebook": nb_map[notebook_id],
            "totalQuestions": len(items),
            "questions": items,
        }

    # ─── 3. Automated Error Notebook ─────────────────────────────────────

    def record_error(
        self,
        student_id: str,
        question: Dict[str, Any],
        student_selected: Optional[str],
        mistake_type: str = "conceptual",
        test_name: str = "Practice Session",
    ) -> Dict[str, Any]:
        err_map = _ECOSYSTEM_STATE["error_notebook"].setdefault(student_id, {})
        qid = question["id"]
        now_iso = datetime.now(timezone.utc).isoformat()

        if qid in err_map:
            entry = err_map[qid]
            entry["attemptCount"] += 1
            entry["studentSelectedOption"] = student_selected
            entry["mistakeType"] = mistake_type
            entry["testName"] = test_name
            entry["isMastered"] = False
            entry["createdAt"] = now_iso
        else:
            entry = {
                "errorId": f"err_{uuid.uuid4().hex[:8]}",
                "questionId": qid,
                "testName": test_name,
                "subject": question["subject"],
                "chapter": question["chapter"],
                "topic": question["topic"],
                "questionText": question["statementHtml"],
                "studentSelectedOption": student_selected,
                "correctOption": question.get("correctOption")
                or str(question.get("numericalAnswer")),
                "solutionText": question["solutionHtml"],
                "mistakeType": mistake_type,
                "attemptCount": 1,
                "isMastered": False,
                "createdAt": now_iso,
            }
            err_map[qid] = entry

        return entry

    def get_error_notebook(
        self,
        student_id: str,
        subject: Optional[str] = None,
        status_filter: str = "unresolved",
        mistake_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> ErrorNotebookListResponse:
        self._ensure_student_seeded(student_id)
        err_map = _ECOSYSTEM_STATE["error_notebook"].setdefault(student_id, {})
        items: List[ErrorNotebookEntry] = []

        for entry in err_map.values():
            if subject and subject.lower() != "all" and entry["subject"].lower() != subject.lower():
                continue
            if status_filter == "unresolved" and entry["isMastered"]:
                continue
            if status_filter == "mastered" and not entry["isMastered"]:
                continue
            if mistake_type and entry["mistakeType"].lower() != mistake_type.lower():
                continue
            items.append(ErrorNotebookEntry(**entry))

        items.sort(key=lambda x: x.createdAt, reverse=True)
        total = len(items)
        start = (page - 1) * limit
        return ErrorNotebookListResponse(
            totalCount=total,
            page=page,
            items=items[start : start + limit],
        )

    def resolve_error(self, student_id: str, error_id: str) -> Dict[str, Any]:
        self._ensure_student_seeded(student_id)
        err_map = _ECOSYSTEM_STATE["error_notebook"].setdefault(student_id, {})
        for entry in err_map.values():
            if entry["errorId"] == error_id or entry["questionId"] == error_id:
                entry["isMastered"] = True
                self.add_weekly_points(student_id, 10)
                return {
                    "success": True,
                    "status": 200,
                    "message": "Error notebook item marked as mastered",
                    "data": entry,
                }
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error entry not found: {error_id}",
        )

    # ─── 4. Teacher / Parent Homework Assignments ────────────────────────

    def create_assignment(
        self, creator_id: str, request: CreateAssignmentRequest
    ) -> CreateAssignmentResponse:
        valid_qids = [qid for qid in request.questionIds if qid in self.questions_by_id]
        if not valid_qids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="None of the provided questionIds exist in the PYQ repository",
            )

        assignment_id = f"as_{uuid.uuid4().hex[:8]}"
        join_code = uuid.uuid4().hex[:6].upper()
        share_url = f"https://link.getmarks.app/assignment/student?code={join_code}"

        record = {
            "assignmentId": assignment_id,
            "creatorId": creator_id,
            "title": request.title.strip(),
            "subjectId": request.subjectId,
            "questionIds": valid_qids,
            "dueDate": request.dueDate,
            "timeLimitMinutes": request.timeLimitMinutes,
            "joinCode": join_code,
            "shareUrl": share_url,
            "submissions": [],
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        _ECOSYSTEM_STATE["assignments"][assignment_id] = record
        _ECOSYSTEM_STATE["assignment_codes"][join_code] = assignment_id

        return CreateAssignmentResponse(
            assignmentId=assignment_id,
            joinCode=join_code,
            shareUrl=share_url,
            title=record["title"],
            questionCount=len(valid_qids),
            timeLimitMinutes=request.timeLimitMinutes,
            dueDate=request.dueDate,
        )

    def get_assignment(self, identifier: str) -> Dict[str, Any]:
        as_id = _ECOSYSTEM_STATE["assignment_codes"].get(identifier.upper(), identifier)
        record = _ECOSYSTEM_STATE["assignments"].get(as_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found: {identifier}",
            )
        questions = [
            {
                "id": q["id"],
                "questionNumber": i + 1,
                "exam": q["exam"],
                "year": q["year"],
                "shift": q["shift"],
                "type": q["type"],
                "statementHtml": q["statementHtml"],
                "options": q["options"],
            }
            for i, qid in enumerate(record["questionIds"])
            if (q := self.questions_by_id.get(qid)) is not None
        ]
        return {
            "status": True,
            "code": 200,
            "data": {
                "assignmentId": record["assignmentId"],
                "title": record["title"],
                "subjectId": record["subjectId"],
                "joinCode": record["joinCode"],
                "shareUrl": record["shareUrl"],
                "dueDate": record["dueDate"],
                "timeLimitMinutes": record["timeLimitMinutes"],
                "totalQuestions": len(questions),
                "questions": questions,
            },
        }

    def submit_assignment(
        self,
        student_id: str,
        assignment_id: str,
        request: AssignmentSubmitRequest,
    ) -> Dict[str, Any]:
        as_id = _ECOSYSTEM_STATE["assignment_codes"].get(assignment_id.upper(), assignment_id)
        record = _ECOSYSTEM_STATE["assignments"].get(as_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found: {assignment_id}",
            )

        resp_by_qid = {r.questionId: r for r in request.responses}
        score = 0
        correct = 0
        incorrect = 0
        per_question_correct: Dict[str, bool] = {}

        for qid in record["questionIds"]:
            q = self.questions_by_id.get(qid)
            if not q:
                continue
            r = resp_by_qid.get(qid)
            if not r or (r.selectedOption is None and r.numericalValue is None):
                per_question_correct[qid] = False
                continue
            is_corr, marks = evaluate_question_attempt(q, r.selectedOption, r.numericalValue)
            score += marks
            per_question_correct[qid] = is_corr
            if is_corr:
                correct += 1
            else:
                incorrect += 1
                self.record_error(
                    student_id=student_id,
                    question=q,
                    student_selected=r.selectedOption or str(r.numericalValue),
                    mistake_type=q.get("commonMistakeType", "conceptual"),
                    test_name=record["title"],
                )

        total_marks = len(record["questionIds"]) * 4
        submission = {
            "submissionId": f"sub_{uuid.uuid4().hex[:8]}",
            "studentId": student_id,
            "score": score,
            "totalMarks": total_marks,
            "correct": correct,
            "incorrect": incorrect,
            "timeTakenSeconds": request.timeTakenSeconds,
            "perQuestionCorrect": per_question_correct,
            "submittedAt": datetime.now(timezone.utc).isoformat(),
        }
        record["submissions"].append(submission)
        self.record_daily_questions_solved(student_id, correct + incorrect)
        self.add_weekly_points(student_id, max(5, correct * 5))

        # Compute live student rank within classroom
        sorted_subs = sorted(
            record["submissions"],
            key=lambda s: (-s["score"], s["timeTakenSeconds"]),
        )
        rank = next(
            (i + 1 for i, s in enumerate(sorted_subs) if s["submissionId"] == submission["submissionId"]),
            1,
        )

        return {
            "status": True,
            "code": 200,
            "message": "Assignment submitted and graded",
            "data": {
                **submission,
                "rank": rank,
                "totalStudents": len(sorted_subs),
            },
        }

    def get_assignment_analytics(
        self, assignment_id: str
    ) -> AssignmentClassroomAnalytics:
        as_id = _ECOSYSTEM_STATE["assignment_codes"].get(assignment_id.upper(), assignment_id)
        record = _ECOSYSTEM_STATE["assignments"].get(as_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found: {assignment_id}",
            )

        subs = record["submissions"]
        total_subs = len(subs)
        avg_score = round(sum(s["score"] for s in subs) / max(1, total_subs), 2) if total_subs else 0.0
        highest = max((s["score"] for s in subs), default=0)
        avg_time = round(sum(s["timeTakenSeconds"] for s in subs) / max(1, total_subs), 1) if total_subs else 0.0

        q_error_rates = []
        for qid in record["questionIds"]:
            q = self.questions_by_id.get(qid, {})
            wrong_count = sum(
                1 for s in subs if not s["perQuestionCorrect"].get(qid, False)
            )
            error_rate = round((wrong_count / max(1, total_subs)) * 100.0, 1) if total_subs else 0.0
            q_error_rates.append(
                {
                    "questionId": qid,
                    "topic": q.get("topic", ""),
                    "errorRatePercentage": error_rate,
                    "incorrectOrSkippedCount": wrong_count,
                }
            )
        q_error_rates.sort(key=lambda x: x["errorRatePercentage"], reverse=True)

        sorted_subs = sorted(subs, key=lambda s: (-s["score"], s["timeTakenSeconds"]))
        leaderboard = [
            {
                "rank": i + 1,
                "studentId": s["studentId"],
                "score": s["score"],
                "totalMarks": s["totalMarks"],
                "timeTakenSeconds": s["timeTakenSeconds"],
            }
            for i, s in enumerate(sorted_subs)
        ]

        return AssignmentClassroomAnalytics(
            assignmentId=record["assignmentId"],
            title=record["title"],
            joinCode=record["joinCode"],
            totalSubmissions=total_subs,
            averageScore=avg_score,
            highestScore=highest,
            averageTimeSeconds=avg_time,
            questionErrorRates=q_error_rates,
            leaderboard=leaderboard,
        )

    # ─── 5. Daily Goals, Monthly Activity Heatmap, Daily Dose & Leagues ──

    def update_daily_goal(self, student_id: str, daily_target: int) -> Dict[str, Any]:
        _ECOSYSTEM_STATE["daily_goals"][student_id] = daily_target
        return {
            "status": True,
            "code": 200,
            "message": "Daily goal updated successfully",
            "data": {"studentId": student_id, "dailyTargetQuestions": daily_target},
        }

    def record_daily_questions_solved(
        self, student_id: str, count: int = 1, date_str: Optional[str] = None
    ) -> None:
        if count <= 0:
            return
        d_str = date_str or date.today().isoformat()
        student_days = _ECOSYSTEM_STATE["daily_solved"].setdefault(student_id, {})
        student_days[d_str] = student_days.get(d_str, 0) + count
        self.add_weekly_points(student_id, count * 5)

    def add_weekly_points(self, student_id: str, points: int) -> None:
        cur = _ECOSYSTEM_STATE["weekly_points"].get(student_id, 0)
        _ECOSYSTEM_STATE["weekly_points"][student_id] = cur + points

    def get_monthly_heatmap(
        self, student_id: str, month: Optional[str] = None
    ) -> MonthlyHeatmapResponse:
        self._ensure_student_seeded(student_id)
        target = _ECOSYSTEM_STATE["daily_goals"].get(student_id, 30)
        m_str = month or date.today().strftime("%Y-%m")
        try:
            year_num, month_num = [int(x) for x in m_str.split("-")]
            _, num_days = calendar.monthrange(year_num, month_num)
        except Exception:
            today = date.today()
            year_num, month_num = today.year, today.month
            m_str = today.strftime("%Y-%m")
            _, num_days = calendar.monthrange(year_num, month_num)

        student_days = _ECOSYSTEM_STATE["daily_solved"].setdefault(student_id, {})
        days_list: List[HeatmapDayItem] = []
        longest_streak = 0
        running_streak = 0
        total_solved = 0

        for day_idx in range(1, num_days + 1):
            d_iso = f"{year_num:04d}-{month_num:02d}-{day_idx:02d}"
            solved = student_days.get(d_iso, 0)
            total_solved += solved
            met = solved >= target
            days_list.append(
                HeatmapDayItem(date=d_iso, solvedCount=solved, targetMet=met)
            )
            if solved > 0:
                running_streak += 1
                longest_streak = max(longest_streak, running_streak)
            else:
                running_streak = 0

        # Current active streak ending today or latest active day in month
        current_streak = 0
        for item in reversed(days_list):
            if item.solvedCount > 0:
                current_streak += 1
            elif current_streak > 0:
                break

        return MonthlyHeatmapResponse(
            month=m_str,
            dailyTargetQuestions=target,
            days=days_list,
            longestStreak=longest_streak,
            currentStreak=current_streak,
            totalSolvedInMonth=total_solved,
        )

    def get_daily_dose(self, student_id: str, exam_id: str = "jee_main") -> Dict[str, Any]:
        today_str = date.today().isoformat()
        pool = [q for q in self.questions if q["examId"] == exam_id] or self.questions
        sprint = pool[:5]
        return {
            "status": True,
            "code": 200,
            "data": {
                "doseId": f"dd_{today_str}_{exam_id}",
                "date": today_str,
                "examId": exam_id,
                "totalQuestions": len(sprint),
                "streakBonusPoints": 25,
                "questions": [
                    {
                        "id": q["id"],
                        "questionNumber": i + 1,
                        "subject": q["subject"],
                        "chapter": q["chapter"],
                        "type": q["type"],
                        "statementHtml": q["statementHtml"],
                        "options": q["options"],
                    }
                    for i, q in enumerate(sprint)
                ],
            },
        }

    def submit_daily_dose(
        self, student_id: str, request: DailyDoseSubmitRequest
    ) -> Dict[str, Any]:
        correct = 0
        incorrect = 0
        for r in request.responses:
            q = self.questions_by_id.get(r.questionId)
            if not q:
                continue
            is_corr, _ = evaluate_question_attempt(q, r.selectedOption, r.numericalValue)
            if is_corr:
                correct += 1
            else:
                incorrect += 1

        total_attempted = correct + incorrect
        points_earned = (correct * 15) + (25 if total_attempted > 0 else 0)
        self.record_daily_questions_solved(
            student_id, total_attempted, date_str=request.date
        )
        self.add_weekly_points(student_id, points_earned)

        return {
            "status": True,
            "code": 200,
            "message": "Daily Dose completed!",
            "data": {
                "date": request.date or date.today().isoformat(),
                "attempted": total_attempted,
                "correct": correct,
                "incorrect": incorrect,
                "pointsEarned": points_earned,
                "weeklyPointsTotal": _ECOSYSTEM_STATE["weekly_points"].get(student_id, 0),
            },
        }

    def get_leaderboard_leagues(self, student_id: str) -> LeaderboardLeaguesResponse:
        user_pts = _ECOSYSTEM_STATE["weekly_points"].get(student_id, 340)
        league_name, next_threshold = determine_league(user_pts)

        competitors = [
            {"rank": 1, "name": "Aman Verma", "points": max(user_pts + 180, 920), "avatar": "av_04"},
            {"rank": 2, "name": "Priya Singh", "points": max(user_pts + 90, 880), "avatar": "av_08"},
            {"rank": 3, "name": "You", "studentId": student_id, "points": user_pts, "avatar": "av_01"},
            {"rank": 4, "name": "Karthik Nair", "points": max(0, user_pts - 45), "avatar": "av_02"},
            {"rank": 5, "name": "Sneha Gupta", "points": max(0, user_pts - 110), "avatar": "av_06"},
        ]
        competitors.sort(key=lambda c: c["points"], reverse=True)
        for idx, comp in enumerate(competitors):
            comp["rank"] = idx + 1

        user_rank = next(
            (c["rank"] for c in competitors if c.get("studentId") == student_id),
            3,
        )

        return LeaderboardLeaguesResponse(
            currentLeague=league_name,
            userRank=user_rank,
            totalCompetitors=50,
            weeklyPoints=user_pts,
            nextLeagueThreshold=next_threshold,
            topRankers=competitors,
        )
