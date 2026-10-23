"""
Comprehensive Unit & Integration Tests for MARKS & SATHEE Backend Features

Tests all newly added domains from Ref_Docs:
1. Chapter-wise PYQ Bank (CPYQB) & Single-Question Practice Mode (MCQ + NAT)
2. Multi-Step Custom Test Generator (CTG: Step 1, Step 2, Generate, Submit, Analysis)
3. Revision Flash Cards (RFC) & Formula Cards Deck
4. Smart Notebooks, Bookmarking & Automated Error Notebook
5. Teacher / Parent Homework Assignments (Join Code, Student Submit, Classroom Analytics)
6. Daily Goals, Monthly Activity Heatmap, Daily Dose 5-Q Sprint & Weekly Leagues
7. Medical / NEET NCERT Line-by-Line Modules & Revision Zones
8. SATHEE AI Hub: Vision OCR, SSE Streaming Doubt Solver, Similar Question Generator,
   AI Rank & Percentile Predictor, College Cutoffs Explorer, Physical OMR Grader

Run from Backend/:
    venv/bin/python -m pytest tests/test_marks_and_sathee_endpoints.py -v
"""

import json
import os
import sys

# Ensure deterministic offline execution during tests
os.environ["HERMES_MOCK"] = "true"

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402
from models.marks_sathee_models import RankPredictRequest  # noqa: E402
from services.ai_hub_admissions_service import (  # noqa: E402
    compute_rank_prediction,
    detect_subject_from_text,
)
from services.cpyqb_ctg_service import evaluate_question_attempt  # noqa: E402
from services.rfc_notebook_assignment_service import (  # noqa: E402
    determine_league,
    load_all_flashcards,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ─── 1. Pure Unit Logic Tests ────────────────────────────────────────────

class TestPureGradingAndModels:
    def test_mcq_grading_correct_and_incorrect(self):
        q = {"type": "MCQ", "correctOption": "B", "correctMarks": 4, "negativeMarks": -1}
        assert evaluate_question_attempt(q, "B", None) == (True, 4)
        assert evaluate_question_attempt(q, "a", None) == (False, -1)
        assert evaluate_question_attempt(q, None, None) == (False, 0)

    def test_nat_grading_with_tolerance(self):
        q = {
            "type": "NAT",
            "numericalAnswer": 36.0,
            "numericalTolerance": 0.1,
            "correctMarks": 4,
            "negativeMarks": 0,
        }
        assert evaluate_question_attempt(q, None, 36.05) == (True, 4)
        assert evaluate_question_attempt(q, None, 35.5) == (False, 0)

    def test_league_tiers(self):
        assert determine_league(120) == ("Bronze", 200)
        assert determine_league(340) == ("Silver", 500)
        assert determine_league(650) == ("Gold", 900)
        assert determine_league(1100) == ("Diamond", 1500)
        assert determine_league(1800) == ("Master", None)

    def test_subject_detection(self):
        assert detect_subject_from_text("Mitochondria and ribosome in eukaryotic cell") == "Biology"
        assert detect_subject_from_text("Calculate molarity and enthalpy of reaction") == "Chemistry"
        assert detect_subject_from_text("Evaluate the definite integral of sin(x)") == "Mathematics"
        assert detect_subject_from_text("Centripetal force on a particle of mass m") == "Physics"

    def test_rank_prediction_calibration(self):
        res = compute_rank_prediction(
            RankPredictRequest(
                exam="jee_main",
                rawMarks=215,
                maxMarks=300,
                category="OBC-NCL",
                shiftDifficulty="moderate",
            )
        )
        assert 90.0 <= res.predictedPercentile <= 99.99
        assert res.predictedAIR >= 1
        assert res.categoryRank < res.predictedAIR
        assert res.airRange["min"] <= res.predictedAIR <= res.airRange["max"]
        assert len(res.historicalTrend) == 2

    def test_flashcards_seeded_from_syllabus(self):
        cards = load_all_flashcards()
        assert len(cards) >= 10
        card_ids = {c["cardId"] for c in cards}
        assert "gauss_law" in card_ids
        assert "rolling_incline" in card_ids


# ─── 2. Domain 2: Chapter-wise PYQ Bank & Practice Mode ──────────────────

class TestCPYQBAndPracticeEndpoints:
    def test_hierarchical_pyq_listing(self, client: TestClient):
        r = client.get(
            "/api/cpyqb/exam/jee_main/subject/physics/chapter/rotational_motion/topic/moment_of_inertia/questions",
            params={"student_id": "stu_pyq_01"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] is True
        assert body["totalCount"] >= 2
        q_ids = [q["id"] for q in body["questions"]]
        assert "q_jee_2024_ph_01" in q_ids

    def test_filter_pyq_by_nat_and_revision_zone(self, client: TestClient):
        r = client.get(
            "/api/cpyqb/questions",
            params={
                "examId": "jee_main",
                "qType": "NAT",
                "revisionZone": "trap_zone",
                "student_id": "stu_pyq_01",
            },
        )
        assert r.status_code == 200
        qs = r.json()["questions"]
        assert len(qs) == 1
        assert qs[0]["id"] == "q_jee_2024_ph_02"
        assert qs[0]["type"] == "NAT"

    def test_practice_mode_correct_mcq_and_nat(self, client: TestClient):
        # Correct MCQ
        r1 = client.post(
            "/api/solving-modes/practice/start",
            params={"student_id": "stu_pyq_01"},
            json={
                "questionId": "q_jee_2024_ph_01",
                "selectedOption": "A",
                "timeSpentSeconds": 65,
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["isCorrect"] is True
        assert d1["marksAwarded"] == 4
        assert d1["userPointsEarned"] == 5
        assert d1["loggedToErrorNotebook"] is False

        # Correct NAT
        r2 = client.post(
            "/api/solving-modes/practice/start",
            params={"student_id": "stu_pyq_01"},
            json={
                "questionId": "q_jee_2024_ph_02",
                "numericalAnswer": 36.0,
                "timeSpentSeconds": 90,
            },
        )
        assert r2.status_code == 200
        assert r2.json()["isCorrect"] is True
        assert r2.json()["marksAwarded"] == 4

    def test_practice_mode_incorrect_logs_to_error_notebook(self, client: TestClient):
        r = client.post(
            "/api/solving-modes/practice/start",
            params={"student_id": "stu_pyq_01"},
            json={
                "questionId": "q_jee_2023_ph_03",
                "selectedOption": "D",  # wrong (correct is B)
                "timeSpentSeconds": 40,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["isCorrect"] is False
        assert body["marksAwarded"] == -1
        assert body["loggedToErrorNotebook"] is True
        assert body["errorId"] is not None

        # Verify pyqFilter=incorrect returns this question
        r_filt = client.get(
            "/api/cpyqb/questions",
            params={"pyqFilter": "incorrect", "student_id": "stu_pyq_01"},
        )
        assert r_filt.status_code == 200
        inc_ids = [q["id"] for q in r_filt.json()["questions"]]
        assert "q_jee_2023_ph_03" in inc_ids


# ─── 3. Domain 3: Custom Test Generator (CTG) ────────────────────────────

class TestCustomTestGeneratorEndpoints:
    def test_full_ctg_lifecycle(self, client: TestClient):
        # Step 1: Exams & Subjects
        r1 = client.get("/api/custom-test/build/step1")
        assert r1.status_code == 200
        exams = {e["id"]: e for e in r1.json()["exams"]}
        assert "jee_main" in exams
        assert "neet" in exams

        # Step 2: Chapters for selected subjects
        r2 = client.post(
            "/api/custom-test/build/step2",
            json={"examId": "jee_main", "subjectIds": ["physics", "mathematics"]},
        )
        assert r2.status_code == 200
        step2 = r2.json()
        assert len(step2["chapters"]) >= 2
        assert 60 in step2["suggestedTimeDurations"]

        # Step 3: Synthesize Custom Test
        r3 = client.post(
            "/api/custom-test/generate",
            params={"student_id": "stu_ctg_01"},
            json={
                "examId": "jee_main",
                "title": "Physics & Maths Sprint CTG",
                "subjectIds": ["physics", "mathematics"],
                "chapterAllocations": [
                    {"chapterId": "rotational_motion", "questionCount": 2},
                    {"chapterId": "definite_integration", "questionCount": 1},
                ],
                "durationMinutes": 45,
            },
        )
        assert r3.status_code == 201
        gen = r3.json()
        test_id = gen["testId"]
        assert gen["totalQuestions"] == 3
        assert gen["totalMarks"] == 12

        # Step 4: Submit Custom Test Attempt
        r4 = client.post(
            "/api/custom-test/submit",
            params={"student_id": "stu_ctg_01"},
            json={
                "testId": test_id,
                "timeTakenSeconds": 240,
                "responses": [
                    {
                        "questionId": "q_jee_2024_ph_01",
                        "selectedOption": "A",  # Correct (+4)
                        "status": "answered",
                        "timeTaken": 70,
                    },
                    {
                        "questionId": "q_jee_2024_ph_02",
                        "numericalValue": 10.0,  # Wrong NAT (0)
                        "status": "answered",
                        "timeTaken": 90,
                    },
                    {
                        "questionId": "q_jee_2024_ma_01",
                        "selectedOption": "B",  # Correct (+4)
                        "status": "answered",
                        "timeTaken": 80,
                    },
                ],
            },
        )
        assert r4.status_code == 200
        sub = r4.json()
        assert sub["score"] == 8
        assert sub["correct"] == 2
        assert sub["incorrect"] == 1
        assert sub["attempted"] == 3
        assert "Physics" in sub["subjectBreakdown"]
        assert "Mathematics" in sub["subjectBreakdown"]

        # Step 5: Fetch Diagnostic Report Card Analysis
        r5 = client.get(f"/api/custom-test/analysis/{test_id}")
        assert r5.status_code == 200
        analysis = r5.json()["data"]
        assert analysis["studentScore"] == 8
        assert analysis["topperScore"] >= analysis["studentScore"]
        assert "speedMetrics" in analysis


# ─── 4. Domain 4: Revision Flash Cards (RFC) & Formula Cards ─────────────

class TestRevisionFlashCardsEndpoints:
    def test_deck_single_card_and_mastery(self, client: TestClient):
        r1 = client.get(
            "/api/rfc/subject/physics/chapter/electrostatics/cards",
            params={"student_id": "stu_rfc_01"},
        )
        assert r1.status_code == 200
        deck = r1.json()
        assert deck["totalCards"] >= 1
        assert deck["masteredCount"] == 0

        r2 = client.get(
            "/api/rfc/subject/physics/chapter/electrostatics/card/gauss_law",
            params={"student_id": "stu_rfc_01"},
        )
        assert r2.status_code == 200
        assert "varepsilon_0" in r2.json()["data"]["backFormulaHtml"]

        r3 = client.post(
            "/api/rfc/mastery",
            params={"student_id": "stu_rfc_01"},
            json={"cardId": "gauss_law", "masteryLevel": "mastered"},
        )
        assert r3.status_code == 200
        assert r3.json()["data"]["userMasteryLevel"] == "mastered"

        r4 = client.get(
            "/api/rfc/subject/physics/chapter/electrostatics/cards",
            params={"student_id": "stu_rfc_01"},
        )
        assert r4.json()["masteredCount"] == 1


# ─── 5. Domain 5: Smart Notebooks, Bookmarking & Error Notebook ──────────

class TestSmartAndErrorNotebooks:
    def test_smart_notebook_crud_and_bookmarking(self, client: TestClient):
        student = "stu_nb_01"
        r_create = client.post(
            "/api/notebook",
            params={"student_id": student},
            json={
                "title": "Rotational Motion Traps",
                "colorHex": "#FF5722",
                "subjectId": "physics",
            },
        )
        assert r_create.status_code == 201
        nb_id = r_create.json()["notebookId"]

        # Pin notebook
        r_pin = client.patch(
            f"/api/notebook/{nb_id}",
            params={"student_id": student},
            json={"isPinned": True},
        )
        assert r_pin.status_code == 200
        assert r_pin.json()["isPinned"] is True

        # Bookmark question with note
        r_bm = client.post(
            "/api/notebook/question",
            params={"student_id": student},
            json={
                "questionId": "q_jee_2024_ph_01",
                "notebookIds": [nb_id],
                "studentNote": "Use parallel axis theorem carefully!",
            },
        )
        assert r_bm.status_code == 200

        # List questions in notebook
        r_qs = client.get(
            f"/api/notebook/{nb_id}/questions",
            params={"student_id": student},
        )
        assert r_qs.status_code == 200
        assert r_qs.json()["totalQuestions"] == 1
        assert (
            r_qs.json()["questions"][0]["studentNote"]
            == "Use parallel axis theorem carefully!"
        )

        # Verify question is also starred in CPYQB filter
        r_star = client.get(
            "/api/cpyqb/questions",
            params={"pyqFilter": "starred", "student_id": student},
        )
        assert r_star.status_code == 200
        assert r_star.json()["totalCount"] == 1

    def test_error_notebook_listing_and_resolution(self, client: TestClient):
        # stu_pyq_01 logged an error earlier in TestCPYQBAndPracticeEndpoints
        r_err = client.get(
            "/api/notebook/errors",
            params={"student_id": "stu_pyq_01", "status": "unresolved"},
        )
        assert r_err.status_code == 200
        body = r_err.json()
        assert body["totalCount"] >= 1
        error_id = body["items"][0]["errorId"]

        # Resolve error
        r_res = client.post(
            f"/api/notebook/errors/{error_id}/resolve",
            params={"student_id": "stu_pyq_01"},
        )
        assert r_res.status_code == 200
        assert r_res.json()["data"]["isMastered"] is True

        # Verify it now appears under status=mastered
        r_mast = client.get(
            "/api/notebook/errors",
            params={"student_id": "stu_pyq_01", "status": "mastered"},
        )
        assert r_mast.status_code == 200
        assert r_mast.json()["totalCount"] >= 1


# ─── 6. Domain 8: Teacher / Parent Homework Assignments ──────────────────

class TestHomeworkAssignmentsFlow:
    def test_teacher_create_student_join_and_analytics(self, client: TestClient):
        r_create = client.post(
            "/api/assignment/teacher/create",
            params={"student_id": "teacher_01"},
            json={
                "title": "Weekly Electrostatics & Rotation Drill",
                "subjectId": "physics",
                "questionIds": ["q_jee_2024_ph_01", "q_jee_2023_ph_03"],
                "dueDate": "2026-10-30T23:59:59Z",
                "timeLimitMinutes": 30,
            },
        )
        assert r_create.status_code == 201
        created = r_create.json()
        join_code = created["joinCode"]
        assert len(join_code) == 6
        assert join_code in created["shareUrl"]

        # Student fetches assignment via 6-char joinCode
        r_fetch = client.get(f"/api/assignment/student/id/{join_code}")
        assert r_fetch.status_code == 200
        assert r_fetch.json()["data"]["totalQuestions"] == 2

        # Student 1 gets both right (+8)
        r_sub1 = client.post(
            f"/api/assignment/student/id/{join_code}/submit",
            params={"student_id": "stu_hw_01"},
            json={
                "timeTakenSeconds": 110,
                "responses": [
                    {"questionId": "q_jee_2024_ph_01", "selectedOption": "A"},
                    {"questionId": "q_jee_2023_ph_03", "selectedOption": "B"},
                ],
            },
        )
        assert r_sub1.status_code == 200
        assert r_sub1.json()["data"]["score"] == 8
        assert r_sub1.json()["data"]["rank"] == 1

        # Student 2 gets 1 right, 1 wrong (+3)
        r_sub2 = client.post(
            f"/api/assignment/student/id/{join_code}/submit",
            params={"student_id": "stu_hw_02"},
            json={
                "timeTakenSeconds": 150,
                "responses": [
                    {"questionId": "q_jee_2024_ph_01", "selectedOption": "A"},
                    {"questionId": "q_jee_2023_ph_03", "selectedOption": "C"},
                ],
            },
        )
        assert r_sub2.status_code == 200
        assert r_sub2.json()["data"]["score"] == 3
        assert r_sub2.json()["data"]["rank"] == 2

        # Teacher views classroom analytics
        r_an = client.get(f"/api/assignment/student/id/{join_code}/analysis")
        assert r_an.status_code == 200
        an = r_an.json()
        assert an["totalSubmissions"] == 2
        assert an["highestScore"] == 8
        assert an["averageScore"] == 5.5
        assert an["questionErrorRates"][0]["questionId"] == "q_jee_2023_ph_03"
        assert an["questionErrorRates"][0]["errorRatePercentage"] == 50.0


# ─── 7. Domain 9 & 10: Daily Goals, Heatmap, Daily Dose, Leagues & NEET ──

class TestGoalsHeatmapLeaguesAndNeet:
    def test_daily_goal_daily_dose_heatmap_and_leagues(self, client: TestClient):
        student = "stu_goal_01"
        r_goal = client.post(
            "/api/targets/update",
            params={"student_id": student},
            json={"dailyTargetQuestions": 5},
        )
        assert r_goal.status_code == 200

        r_dose = client.get(
            "/api/targets/daily-dose",
            params={"student_id": student, "examId": "jee_main"},
        )
        assert r_dose.status_code == 200
        qs = r_dose.json()["data"]["questions"]
        assert len(qs) >= 3

        r_sub = client.post(
            "/api/targets/daily-dose/submit",
            params={"student_id": student},
            json={
                "date": "2026-10-22",
                "responses": [
                    {"questionId": "q_jee_2024_ph_01", "selectedOption": "A"},
                    {"questionId": "q_jee_2023_ph_03", "selectedOption": "B"},
                    {"questionId": "q_jee_2024_ch_01", "selectedOption": "C"},
                    {"questionId": "q_jee_2024_ma_01", "selectedOption": "B"},
                    {"questionId": "q_jee_2024_ph_02", "numericalValue": 36.0},
                ],
            },
        )
        assert r_sub.status_code == 200
        assert r_sub.json()["data"]["correct"] == 5
        assert r_sub.json()["data"]["pointsEarned"] == 100

        r_hm = client.get(
            "/api/targets/heatmap",
            params={"student_id": student, "month": "2026-10"},
        )
        assert r_hm.status_code == 200
        hm = r_hm.json()
        assert hm["totalSolvedInMonth"] == 5
        assert hm["longestStreak"] >= 1
        oct_22 = next(d for d in hm["days"] if d["date"] == "2026-10-22")
        assert oct_22["solvedCount"] == 5
        assert oct_22["targetMet"] is True

        r_lb = client.get(
            "/api/leaderboard/achievements",
            params={"student_id": student},
        )
        assert r_lb.status_code == 200
        assert r_lb.json()["weeklyPoints"] >= 100
        assert len(r_lb.json()["topRankers"]) == 5

    def test_neet_ncert_modules(self, client: TestClient):
        r = client.get(
            "/api/neet/ncert/subject/biology/modules",
            params={"student_id": "stu_neet_01"},
        )
        assert r.status_code == 200
        mods = r.json()["modules"]
        assert len(mods) >= 2
        assert mods[0]["book"] == "Class 11 Biology"
        assert "125-144" in mods[0]["ncertPages"]


# ─── 8. SATHEE AI Hub & Admissions Microservices ─────────────────────────

class TestSatheeAIHubAndAdmissions:
    def test_vision_ocr(self, client: TestClient):
        r = client.post(
            "/api/ai-hub/vision/ocr",
            data={
                "detectMath": "true",
                "language": "en",
                "textHint": "Evaluate $\\int_0^{\\pi/2} \\sin(x) dx = 1$.",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["hasEquations"] is True
        assert body["detectedSubject"] == "Mathematics"

    def test_streaming_socratic_doubt_sse(self, client: TestClient):
        with client.stream(
            "POST",
            "/api/ai-hub/chat/stream",
            json={
                "query": "A particle moves in a circle under F = -k/r^2. Find total mechanical energy.",
                "subject": "Physics",
                "exam": "jee",
                "mode": "step_by_step",
            },
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            lines = [line for line in response.iter_lines() if line]
            assert any("analyzing" in ln for ln in lines)
            assert any("reasoning" in ln for ln in lines)
            assert any("solution" in ln for ln in lines)
            assert lines[-1] == "data: [DONE]"

    def test_generate_similar_questions(self, client: TestClient):
        r = client.post(
            "/api/ai-hub/qa/generate-similar-questions",
            json={
                "questionText": "Find the equivalent resistance of an infinite ladder network.",
                "subject": "Physics",
                "topic": "Current Electricity",
                "difficulty": "medium",
                "count": 3,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert len(body["questions"]) == 3
        assert len(body["questions"][0]["options"]) == 4

    def test_rank_predictor_and_college_cutoffs(self, client: TestClient):
        r_pred = client.post(
            "/api/ai-hub/rank/predict",
            json={
                "exam": "jee_main",
                "rawMarks": 230,
                "maxMarks": 300,
                "category": "OBC-NCL",
                "shiftDifficulty": "moderate",
            },
        )
        assert r_pred.status_code == 200
        pred = r_pred.json()
        assert pred["predictedPercentile"] > 95.0
        assert pred["categoryRank"] < pred["predictedAIR"]

        r_col = client.get(
            "/api/ai-hub/colleges/cutoffs",
            params={
                "collegeId": "iit_bombay",
                "category": "General",
                "studentAir": 120,
            },
        )
        assert r_col.status_code == 200
        col = r_col.json()["data"]
        assert col["id"] == "iit_bombay"
        branches = {b["branchCode"]: b for b in col["branches"]}
        # AIR 120 is > 68 (CSE cutoff) so CSE is False, but <= 480 (EE cutoff) so EE is True
        assert branches["CSE"]["isEligible"] is False
        assert branches["EE"]["isEligible"] is True

    def test_physical_omr_sheet_evaluation(self, client: TestClient):
        scanned = {"1": "A", "2": "C", "3": "B", "4": "A", "5": "B"}  # 4 correct, 1 wrong
        r = client.post(
            "/api/ai-hub/omr/evaluate",
            data={
                "templateId": "jee_advanced_paper1_2026",
                "rollNumber": "2026991",
                "scannedAnswersJson": json.dumps(scanned),
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["detectedRollNumber"] == "2026991"
        assert body["totalAttempted"] == 5
        assert body["correctCount"] == 4
        assert body["incorrectCount"] == 1
        assert body["marksCalculated"] == (4 * 4) - 1  # 15
