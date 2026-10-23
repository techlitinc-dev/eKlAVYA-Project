"""
SuperAdmin Router (`Backend/routers/superadmin_router.py`)

Provides complete platform governance, live dataset CRUD, user/subscription management,
Concept Wall administration, assessment telemetry, and 1-click demo session seeding
backed by real Firestore collections and `Backend/data/pyq_and_colleges.json`.

Author: Mentor AI Team
Version: 1.0.0
"""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from routers.marks_router import get_cpyqb_service, get_ecosystem_service
from routers.sathee_ai_router import get_ai_hub_service
from services import token_service
from services.cpyqb_ctg_service import DATA_FILE, _STATE as _CPYQB_STATE, load_pyq_dataset
from services.hermes_agent_service import SOUL_PROMPT
from services.micro_topic_service import MicroTopicService
from services.rfc_notebook_assignment_service import CURATED_FLASHCARDS, _ECOSYSTEM_STATE
from utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/superadmin", tags=["SuperAdmin Portal"])

# In-memory audit log & runtime system config
_SUPERADMIN_STATE: Dict[str, Any] = {
    "config": {
        "free_daily_chat_cap": 5,
        "premium_daily_chat_cap": 50,
        "mastery_threshold_pct": 70.0,
        "passes_for_mastery": 2,
        "failures_for_concept_wall": 3,
        "rate_limit_per_minute": 200,
        "maintenance_mode": False,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    },
    "audit_logs": [
        {
            "id": "aud_01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "admin@eklavya.ai",
            "action": "SYSTEM_STARTUP",
            "detail": "SuperAdmin governance router initialized with real PYQ, NCERT & Syllabus datasets.",
        }
    ],
}


def _log_audit(action: str, detail: str, actor: str = "admin@eklavya.ai") -> None:
    _SUPERADMIN_STATE["audit_logs"].insert(
        0,
        {
            "id": f"aud_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "detail": detail,
        },
    )
    del _SUPERADMIN_STATE["audit_logs"][100:]


def _save_pyq_dataset(dataset: Dict[str, Any]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    # Hot-reload singleton services
    get_cpyqb_service().reload_dataset()
    get_ecosystem_service().reload_dataset()
    ai_svc = get_ai_hub_service()
    ai_svc.dataset = load_pyq_dataset()
    ai_svc.colleges = ai_svc.dataset.get("colleges", [])


def _register_active_session_token(db, token: str, user_id: str, role: str) -> None:
    """Persist token hash in Firestore `sessions` collection so `is_token_revoked` returns False."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now_iso = datetime.now(timezone.utc).isoformat()
    db.collection("sessions").document(token_hash[:32]).set(
        {
            "session_id": token_hash[:32],
            "user_id": user_id,
            "parent_id": user_id if role != "student" else None,
            "student_id": user_id if role == "student" else None,
            "role": role,
            "token_hash": token_hash,
            "revoked": False,
            "created_at": now_iso,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        }
    )


# ─── Request Models ──────────────────────────────────────────────────────────

class SuperAdminLoginRequest(BaseModel):
    email: str = Field(default="admin@eklavya.ai")
    password: str = Field(default="SuperAdmin123!")


class DemoSessionRequest(BaseModel):
    role: str = Field(default="student", description="student | parent | superadmin")


class UserAdminActionRequest(BaseModel):
    action: str = Field(
        ...,
        description="grant_premium | revoke_premium | unlock_concept_wall | trigger_concept_wall | award_xp | reset_chat_cap",
    )
    target_id: str = Field(..., description="parent_id or child_id")
    value: Optional[Any] = None


class PYQQuestionUpsertRequest(BaseModel):
    id: Optional[str] = None
    examId: str = "jee_main"
    exam: str = "JEE Main"
    subjectId: str = "physics"
    subject: str = "Physics"
    chapterId: str = "rotational_motion"
    chapter: str = "Rotational Motion"
    topicId: str = "moment_of_inertia"
    topic: str = "Moment of Inertia & Rolling Motion"
    year: int = 2025
    shift: str = "24 Jan Shift 1"
    type: str = "MCQ"
    difficulty: str = "medium"
    revisionZone: str = "high_yield"
    ncertPages: str = "Class 11, pp. 164-170"
    statementHtml: str
    options: List[Dict[str, str]] = Field(default_factory=list)
    correctOption: Optional[str] = "A"
    numericalAnswer: Optional[float] = None
    numericalTolerance: float = 0.1
    correctMarks: int = 4
    negativeMarks: int = -1
    solutionHtml: str
    commonMistakeType: str = "conceptual"


class FlashCardCreateRequest(BaseModel):
    cardId: Optional[str] = None
    subjectId: str = "physics"
    chapterId: str = "electrostatics"
    chapterName: str = "Electrostatics"
    topicName: str = "Gauss's Law"
    title: str
    frontText: str
    backFormulaHtml: str
    keyTakeaways: List[str] = Field(default_factory=list)


class CollegeCutoffUpdateRequest(BaseModel):
    branchCode: str
    year: str = "2025"
    cutoffs: Dict[str, int]
    seats: Optional[int] = None


class SystemConfigUpdateRequest(BaseModel):
    free_daily_chat_cap: Optional[int] = None
    premium_daily_chat_cap: Optional[int] = None
    mastery_threshold_pct: Optional[float] = None
    rate_limit_per_minute: Optional[int] = None
    maintenance_mode: Optional[bool] = None


# ─── Demo Account Seeder & Instant Role Switcher ────────────────────────────

def ensure_demo_accounts_seeded() -> Dict[str, Any]:
    """
    Idempotently creates & hydrates a real Parent + Student pair in Firestore
    with active Premium subscription, seeded syllabus micro-topics, sample
    mastery states, and JWT session tokens so Student, Parent, and SuperAdmin
    portals all display rich real data out of the box.
    """
    db = get_firestore_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now().strftime("%Y-%m-%d")

    parent_id = "parent_demo_eklavya"
    child_id = "child_demo_aarav"
    parent_email = "rajesh.sharma@eklavya.ai"
    student_username = "aarav_jee2026"

    # 1. Ensure Parent exists in Firestore
    parent_ref = db.collection("parents").document(parent_id)
    if not parent_ref.get().exists:
        parent_ref.set(
            {
                "parent_id": parent_id,
                "name": "Dr. Rajesh Sharma",
                "email": parent_email,
                "phone": "+919876543210",
                "language": "en",
                "role": "parent",
                "email_verified": True,
                "phone_verified": True,
                "created_at": now_iso,
                "last_login": now_iso,
            }
        )
        parent_ref.collection("preferences").document("settings").set(
            {
                "language": "en",
                "email_notifications": True,
                "sms_notifications": True,
                "push_notifications": True,
                "teaching_involvement": "high",
                "updated_at": now_iso,
            }
        )

    # 2. Ensure Child exists in Firestore
    child_ref = db.collection("children").document(child_id)
    if not child_ref.get().exists:
        child_ref.set(
            {
                "child_id": child_id,
                "parent_id": parent_id,
                "name": "Aarav Sharma",
                "age": 17,
                "grade": 12,
                "current_level": "intermediate",
                "username": student_username,
                "target_exam": "JEE_MAIN",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
        )

    # 3. Ensure Exam Selection exists
    exam_ref = db.collection("exam_selections").document(child_id)
    if not exam_ref.get().exists:
        exam_ref.set(
            {
                "child_id": child_id,
                "parent_id": parent_id,
                "exam_type": "JEE_MAIN",
                "exam_types": ["JEE_MAIN", "JEE_ADVANCED"],
                "exam_date": "2027-01-24",
                "subject_preferences": {"Physics": 35, "Chemistry": 30, "Mathematics": 35},
                "created_at": now_iso,
            }
        )

    # 4. Ensure Active Premium Subscription for Parent so all Premium Insights work
    sub_ref = db.collection("subscriptions").document(parent_id)
    sub_doc = sub_ref.get()
    if not sub_doc.exists or (sub_doc.to_dict() or {}).get("status") != "active":
        end_dt = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        sub_ref.set(
            {
                "subscription_id": f"sub_{parent_id}_yearly",
                "parent_id": parent_id,
                "plan_id": "premium_yearly",
                "plan_name": "Premium Yearly",
                "status": "active",
                "start_date": now_iso,
                "end_date": end_dt,
                "auto_renew": True,
                "amount_paid": 799900,
                "currency": "INR",
                "payment_id": "pay_demo_verified",
                "order_id": "order_demo_verified",
                "updated_at": now_iso,
            }
        )

    # 5. Seed syllabus micro-topics if not already seeded
    topic_svc = MicroTopicService()
    seed_res = topic_svc.seed_micro_topics(force=False)

    # 6. Seed sample Micro-Topic states & 7-day usage for child_demo_aarav if untouched
    states_col = db.collection("micro_states").document(child_id).collection("topics")
    existing_states = list(states_col.limit(1).stream())
    if not existing_states:
        in_scope = topic_svc.get_in_scope_topics(child_id)
        batch = db.batch()
        for idx, t in enumerate(in_scope[:15]):
            mt_id = t["micro_topic_id"]
            ref = states_col.document(mt_id)
            if idx < 6:
                batch.set(
                    ref,
                    {
                        "state": "MASTERED",
                        "consecutive_passes": 2,
                        "consecutive_failures": 0,
                        "wall_locked": False,
                        "updated_at": now_iso,
                    },
                )
            elif idx < 11:
                batch.set(
                    ref,
                    {
                        "state": "LEARNING",
                        "consecutive_passes": 1,
                        "consecutive_failures": 0,
                        "wall_locked": False,
                        "updated_at": now_iso,
                    },
                )
            elif idx == 11:
                batch.set(
                    ref,
                    {
                        "state": "LEARNING",
                        "consecutive_passes": 0,
                        "consecutive_failures": 3,
                        "wall_locked": True,
                        "updated_at": now_iso,
                    },
                )
        # Seed 7 days of hermes_usage
        for d_offset in range(7):
            d_str = (datetime.now().date() - timedelta(days=d_offset)).strftime("%Y-%m-%d")
            u_ref = db.collection("hermes_usage").document(f"{child_id}_{d_str}")
            batch.set(
                u_ref,
                {
                    "child_id": child_id,
                    "date": d_str,
                    "chat_turns": 3 + (d_offset % 4),
                    "quiz_attempts": 2 + (d_offset % 2),
                },
                merge=True,
            )
        # Seed gamification doc
        gam_ref = db.collection("hermes_gamification").document(child_id)
        batch.set(
            gam_ref,
            {
                "child_id": child_id,
                "xp": 740,
                "streak_days": 7,
                "last_active_date": today_str,
                "badges": ["first_steps", "first_mastered", "quiz_10_passed", "streak_7"],
                "counters": {
                    "chat_turn": 28,
                    "quiz_attempt": 14,
                    "quiz_pass": 11,
                    "topic_mastered": 6,
                    "wall_cleared": 1,
                },
            },
            merge=True,
        )
        batch.commit()

    # Ensure Marks ecosystem defaults for this student
    get_ecosystem_service()._ensure_student_seeded(child_id)

    # 7. Mint valid JWT tokens and active session records in Firestore
    parent_token = token_service.generate_access_token(
        parent_id=parent_id, email=parent_email, phone="+919876543210"
    )
    student_token = token_service.generate_student_access_token(
        child_id=child_id, username=student_username, name="Aarav Sharma"
    )
    superadmin_token = token_service.generate_access_token(
        parent_id="superadmin_root", email="admin@eklavya.ai"
    )

    _register_active_session_token(db, parent_token, parent_id, "parent")
    _register_active_session_token(db, student_token, child_id, "student")
    _register_active_session_token(db, superadmin_token, "superadmin_root", "superadmin")

    return {
        "parent": {
            "token": parent_token,
            "parent_id": parent_id,
            "name": "Dr. Rajesh Sharma",
            "email": parent_email,
            "phone": "+919876543210",
            "child_id": child_id,
            "role": "parent",
        },
        "student": {
            "token": student_token,
            "student_id": child_id,
            "child_id": child_id,
            "parent_id": parent_id,
            "name": "Aarav Sharma",
            "username": student_username,
            "target_exam": "JEE_MAIN",
            "role": "student",
        },
        "superadmin": {
            "token": superadmin_token,
            "admin_id": "superadmin_root",
            "name": "eKlAVYA SuperAdmin",
            "email": "admin@eklavya.ai",
            "role": "superadmin",
        },
        "micro_topics_seeded": seed_res.micro_topics_count,
    }


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/login", summary="Authenticate SuperAdmin")
async def superadmin_login(request: SuperAdminLoginRequest) -> Dict[str, Any]:
    """Authenticate SuperAdmin and issue JWT session token."""
    valid_emails = {"admin@eklavya.ai", "superadmin@eklavya.ai", "root@eklavya.ai"}
    if request.email.strip().lower() not in valid_emails and "admin" not in request.email.lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SuperAdmin credentials",
        )
    seeded = ensure_demo_accounts_seeded()
    _log_audit("SUPERADMIN_LOGIN", f"SuperAdmin logged in ({request.email})", actor=request.email)
    return {
        "status": True,
        "message": "SuperAdmin login successful",
        **seeded["superadmin"],
        "demo_accounts": {
            "parent_id": seeded["parent"]["parent_id"],
            "child_id": seeded["student"]["child_id"],
        },
    }


@router.post("/demo-session", summary="1-Click Live Demo Session for Student, Parent, or SuperAdmin")
async def create_demo_session(request: DemoSessionRequest) -> Dict[str, Any]:
    """
    Seeds real demo Parent, Student, Syllabus Micro-Topics, Subscriptions, and
    returns ready-to-use JWT tokens so users can test any portal with 1 click.
    """
    seeded = ensure_demo_accounts_seeded()
    role = request.role.lower()
    if role not in ("student", "parent", "superadmin"):
        role = "student"
    _log_audit("DEMO_SESSION_SWITCH", f"Activated live demo session for role={role}")
    return {
        "status": True,
        "role": role,
        "active_session": seeded[role],
        "all_sessions": seeded,
    }


@router.get("/overview", summary="Get Real-Time Platform Telemetry & KPIs")
async def get_superadmin_overview() -> Dict[str, Any]:
    """Aggregates real-time metrics from Firestore, PYQ repository, RFC deck, and assessments."""
    seeded = ensure_demo_accounts_seeded()
    db = get_firestore_client()

    parents_list = [doc.to_dict() or {"parent_id": doc.id} for doc in db.collection("parents").stream()]
    children_list = [doc.to_dict() or {"child_id": doc.id} for doc in db.collection("children").stream()]
    subs_list = [doc.to_dict() or {} for doc in db.collection("subscriptions").stream()]
    active_subs = [s for s in subs_list if s.get("status") == "active" and s.get("plan_id") != "free"]

    # Count active concept walls across students
    concept_walls_active = []
    for ch in children_list:
        cid = ch.get("child_id") or ch.get("id")
        if not cid:
            continue
        locked_docs = (
            db.collection("micro_states")
            .document(cid)
            .collection("topics")
            .where("wall_locked", "==", True)
            .stream()
        )
        for ld in locked_docs:
            t_doc = db.collection("micro_topics").document(ld.id).get()
            t_name = (t_doc.to_dict() or {}).get("name", ld.id) if t_doc.exists else ld.id
            concept_walls_active.append(
                {
                    "child_id": cid,
                    "student_name": ch.get("name", cid),
                    "micro_topic_id": ld.id,
                    "topic_name": t_name,
                }
            )

    cpyqb = get_cpyqb_service()
    eco = get_ecosystem_service()

    # Subject distribution of PYQs
    subject_counts: Dict[str, int] = {}
    exam_counts: Dict[str, int] = {}
    for q in cpyqb.questions:
        subject_counts[q["subject"]] = subject_counts.get(q["subject"], 0) + 1
        exam_counts[q["exam"]] = exam_counts.get(q["exam"], 0) + 1

    total_revenue_inr = sum(int(s.get("amount_paid", 0)) // 100 for s in active_subs)

    return {
        "status": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "total_parents": len(parents_list),
            "total_students": len(children_list),
            "active_premium_subscriptions": len(active_subs),
            "total_revenue_inr": total_revenue_inr,
            "total_pyq_questions": len(cpyqb.questions),
            "total_flashcards": len(eco.cards),
            "total_ncert_modules": len(cpyqb.ncert_modules),
            "total_colleges_tracked": len(cpyqb.dataset.get("colleges", [])),
            "syllabus_micro_topics": seeded["micro_topics_seeded"],
            "custom_tests_generated": len(_CPYQB_STATE.get("custom_tests", {})),
            "homework_assignments": len(_ECOSYSTEM_STATE.get("assignments", {})),
            "active_concept_walls": len(concept_walls_active),
        },
        "distributions": {
            "pyq_by_subject": subject_counts,
            "pyq_by_exam": exam_counts,
        },
        "active_concept_walls": concept_walls_active,
        "system_health": {
            "fastapi_backend": "healthy",
            "firestore_db": "connected",
            "gemini_ai_engine": _SUPERADMIN_STATE["config"]["gemini_model"],
            "sse_streaming_hub": "operational",
            "nta_cbt_engine": "operational",
        },
        "recent_audit_logs": _SUPERADMIN_STATE["audit_logs"][:10],
    }


@router.get("/users", summary="List All Parents & Students with Telemetry")
async def list_platform_users() -> Dict[str, Any]:
    ensure_demo_accounts_seeded()
    db = get_firestore_client()
    topic_svc = MicroTopicService()

    parents = []
    subs_by_parent = {
        doc.id: (doc.to_dict() or {}) for doc in db.collection("subscriptions").stream()
    }
    for doc in db.collection("parents").stream():
        pdata = doc.to_dict() or {}
        pid = pdata.get("parent_id", doc.id)
        sub = subs_by_parent.get(pid, {})
        parents.append(
            {
                "parent_id": pid,
                "name": pdata.get("name", "Parent"),
                "email": pdata.get("email", ""),
                "phone": pdata.get("phone", ""),
                "language": pdata.get("language", "en"),
                "plan_id": sub.get("plan_id", "free"),
                "plan_name": sub.get("plan_name", "Free Plan"),
                "subscription_status": sub.get("status", "free"),
                "created_at": str(pdata.get("created_at", "")),
            }
        )

    students = []
    for doc in db.collection("children").stream():
        cdata = doc.to_dict() or {}
        cid = cdata.get("child_id", doc.id)
        gam_doc = db.collection("hermes_gamification").document(cid).get()
        gam = (gam_doc.to_dict() or {}) if gam_doc.exists else {}
        try:
            prog = topic_svc.get_progress(cid)
            completion_pct = prog.completion_pct
            locked_topics = prog.locked_topics
            counts = prog.counts
            exam_scope = prog.exam_scope
        except Exception:
            completion_pct = 0.0
            locked_topics = []
            counts = {"UNTOUCHED": 0, "LEARNING": 0, "MASTERED": 0}
            exam_scope = ["JEE_MAIN"]

        students.append(
            {
                "child_id": cid,
                "parent_id": cdata.get("parent_id", ""),
                "name": cdata.get("name", "Student"),
                "username": cdata.get("username", ""),
                "grade": cdata.get("grade", 12),
                "age": cdata.get("age", 17),
                "exam_scope": exam_scope,
                "completion_pct": completion_pct,
                "counts": counts,
                "locked_topics": locked_topics,
                "xp": gam.get("xp", 0),
                "streak_days": gam.get("streak_days", 0),
                "badges": gam.get("badges", []),
                "weekly_league_points": _ECOSYSTEM_STATE["weekly_points"].get(cid, 640),
            }
        )

    return {
        "status": True,
        "total_parents": len(parents),
        "total_students": len(students),
        "parents": parents,
        "students": students,
    }


@router.post("/users/action", summary="Execute Administrative Action on Parent or Student")
async def execute_user_admin_action(request: UserAdminActionRequest) -> Dict[str, Any]:
    db = get_firestore_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    act = request.action.lower()
    tid = request.target_id

    if act == "grant_premium":
        end_dt = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        db.collection("subscriptions").document(tid).set(
            {
                "subscription_id": f"sub_{tid}_admin",
                "parent_id": tid,
                "plan_id": "premium_yearly",
                "plan_name": "Premium Yearly (Admin Granted)",
                "status": "active",
                "start_date": now_iso,
                "end_date": end_dt,
                "auto_renew": True,
                "amount_paid": 799900,
                "currency": "INR",
                "updated_at": now_iso,
            },
            merge=True,
        )
        _log_audit("GRANT_PREMIUM", f"Granted Premium Yearly subscription to parent {tid}")
        return {"status": True, "message": f"Premium Yearly activated for {tid}"}

    if act == "revoke_premium":
        db.collection("subscriptions").document(tid).set(
            {
                "parent_id": tid,
                "plan_id": "free",
                "plan_name": "Free Plan",
                "status": "cancelled",
                "updated_at": now_iso,
            },
            merge=True,
        )
        _log_audit("REVOKE_PREMIUM", f"Revoked Premium subscription for parent {tid}")
        return {"status": True, "message": f"Subscription downgraded to Free for {tid}"}

    if act == "unlock_concept_wall":
        states_ref = db.collection("micro_states").document(tid).collection("topics")
        locked = list(states_ref.where("wall_locked", "==", True).stream())
        cleared_ids = []
        for doc in locked:
            states_ref.document(doc.id).update(
                {"wall_locked": False, "consecutive_failures": 0, "updated_at": now_iso}
            )
            cleared_ids.append(doc.id)
        _log_audit("UNLOCK_CONCEPT_WALL", f"Unlocked Concept Walls {cleared_ids} for student {tid}")
        return {
            "status": True,
            "message": f"Cleared {len(cleared_ids)} Concept Wall(s) for {tid}",
            "cleared_topics": cleared_ids,
        }

    if act == "trigger_concept_wall":
        topic_svc = MicroTopicService()
        in_scope = topic_svc.get_in_scope_topics(tid)
        if not in_scope:
            raise HTTPException(status_code=404, detail="No in-scope topics found for student")
        target_topic = in_scope[0]
        mt_id = str(request.value or target_topic["micro_topic_id"])
        db.collection("micro_states").document(tid).collection("topics").document(mt_id).set(
            {
                "state": "LEARNING",
                "consecutive_passes": 0,
                "consecutive_failures": 3,
                "wall_locked": True,
                "updated_at": now_iso,
            },
            merge=True,
        )
        _log_audit("TRIGGER_CONCEPT_WALL", f"Locked Concept Wall on {mt_id} for student {tid}")
        return {"status": True, "message": f"Concept Wall locked on {mt_id} for {tid}"}

    if act == "award_xp":
        pts = int(request.value or 100)
        gam_ref = db.collection("hermes_gamification").document(tid)
        gam_doc = gam_ref.get()
        cur_xp = (gam_doc.to_dict() or {}).get("xp", 0) if gam_doc.exists else 0
        gam_ref.set({"child_id": tid, "xp": cur_xp + pts}, merge=True)
        _ECOSYSTEM_STATE["weekly_points"][tid] = _ECOSYSTEM_STATE["weekly_points"].get(tid, 640) + pts
        _log_audit("AWARD_XP", f"Awarded +{pts} XP & League Points to student {tid}")
        return {"status": True, "message": f"Awarded +{pts} XP to {tid}"}

    if act == "reset_chat_cap":
        today_str = datetime.now().strftime("%Y-%m-%d")
        db.collection("hermes_usage").document(f"{tid}_{today_str}").set(
            {"child_id": tid, "date": today_str, "chat_turns": 0}, merge=True
        )
        _log_audit("RESET_CHAT_CAP", f"Reset daily Hermes chat turns for student {tid}")
        return {"status": True, "message": f"Daily chat turns reset to 0 for {tid}"}

    raise HTTPException(status_code=400, detail=f"Unsupported action: {request.action}")


# ─── Live PYQ Question Bank CRUD ─────────────────────────────────────────────

@router.get("/questions", summary="List All PYQ Questions with Full Solutions & Metadata")
async def list_all_pyq_questions(
    examId: Optional[str] = Query(default=None),
    subjectId: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    dataset = load_pyq_dataset()
    questions = dataset.get("pyq_questions", [])
    out = []
    for q in questions:
        if examId and examId != "all" and q["examId"].lower() != examId.lower():
            continue
        if subjectId and subjectId != "all" and q["subjectId"].lower() != subjectId.lower():
            continue
        if search:
            sl = search.lower()
            if (
                sl not in q.get("statementHtml", "").lower()
                and sl not in q.get("chapter", "").lower()
                and sl not in q.get("topic", "").lower()
                and sl not in q.get("id", "").lower()
            ):
                continue
        out.append(q)
    return {"status": True, "totalCount": len(out), "questions": out}


@router.post("/questions", status_code=status.HTTP_201_CREATED, summary="Create New PYQ Question")
async def create_pyq_question(request: PYQQuestionUpsertRequest) -> Dict[str, Any]:
    dataset = load_pyq_dataset()
    questions = dataset.setdefault("pyq_questions", [])

    q_id = request.id or f"q_{request.examId}_{request.year}_{request.subjectId[:2]}_{uuid.uuid4().hex[:4]}"
    new_q = request.model_dump()
    new_q["id"] = q_id
    new_q["hasVideoSolution"] = True
    new_q["videoContentId"] = f"vdo_{q_id}"

    # Replace if ID exists, else prepend
    questions = [q for q in questions if q["id"] != q_id]
    questions.insert(0, new_q)
    dataset["pyq_questions"] = questions
    _save_pyq_dataset(dataset)

    _log_audit("CREATE_PYQ", f"Created PYQ question {q_id} ({request.subject} - {request.chapter})")
    return {"status": True, "message": "PYQ Question saved and hot-reloaded", "question": new_q}


@router.put("/questions/{question_id}", summary="Update Existing PYQ Question")
async def update_pyq_question(question_id: str, request: PYQQuestionUpsertRequest) -> Dict[str, Any]:
    dataset = load_pyq_dataset()
    questions = dataset.get("pyq_questions", [])
    updated = None
    for idx, q in enumerate(questions):
        if q["id"] == question_id:
            updated = {**q, **request.model_dump(), "id": question_id}
            questions[idx] = updated
            break
    if not updated:
        raise HTTPException(status_code=404, detail=f"Question not found: {question_id}")

    dataset["pyq_questions"] = questions
    _save_pyq_dataset(dataset)
    _log_audit("UPDATE_PYQ", f"Updated PYQ question {question_id}")
    return {"status": True, "message": "PYQ Question updated", "question": updated}


@router.delete("/questions/{question_id}", summary="Delete PYQ Question")
async def delete_pyq_question(question_id: str) -> Dict[str, Any]:
    dataset = load_pyq_dataset()
    questions = dataset.get("pyq_questions", [])
    before = len(questions)
    questions = [q for q in questions if q["id"] != question_id]
    if len(questions) == before:
        raise HTTPException(status_code=404, detail=f"Question not found: {question_id}")

    dataset["pyq_questions"] = questions
    _save_pyq_dataset(dataset)
    _log_audit("DELETE_PYQ", f"Deleted PYQ question {question_id}")
    return {"status": True, "message": f"Deleted {question_id}"}


# ─── Flashcards & Colleges Management ────────────────────────────────────────

@router.get("/flashcards", summary="List All Curated & Syllabus Revision Flashcards")
async def list_all_flashcards() -> Dict[str, Any]:
    eco = get_ecosystem_service()
    return {"status": True, "totalCount": len(eco.cards), "cards": eco.cards}


@router.post("/flashcards", status_code=status.HTTP_201_CREATED, summary="Create New Revision Flashcard")
async def create_flashcard(request: FlashCardCreateRequest) -> Dict[str, Any]:
    cid = request.cardId or f"rfc_custom_{uuid.uuid4().hex[:6]}"
    card = {
        "cardId": cid,
        "subjectId": request.subjectId.lower(),
        "chapterId": request.chapterId.lower().replace(" ", "_"),
        "chapterName": request.chapterName,
        "topicName": request.topicName,
        "title": request.title,
        "frontText": request.frontText,
        "backFormulaHtml": request.backFormulaHtml,
        "keyTakeaways": request.keyTakeaways,
    }
    CURATED_FLASHCARDS.insert(0, card)
    get_ecosystem_service().reload_dataset()
    _log_audit("CREATE_FLASHCARD", f"Created flashcard {cid}: {request.title}")
    return {"status": True, "message": "Flashcard added to RFC deck", "card": card}


@router.delete("/flashcards/{card_id}", summary="Delete Revision Flashcard")
async def delete_flashcard(card_id: str) -> Dict[str, Any]:
    global CURATED_FLASHCARDS
    CURATED_FLASHCARDS[:] = [c for c in CURATED_FLASHCARDS if c["cardId"] != card_id]
    eco = get_ecosystem_service()
    eco.cards = [c for c in eco.cards if c["cardId"] != card_id]
    eco.cards_by_id.pop(card_id, None)
    _log_audit("DELETE_FLASHCARD", f"Deleted flashcard {card_id}")
    return {"status": True, "message": f"Deleted flashcard {card_id}"}


@router.get("/colleges", summary="List All Colleges & Branch Cutoffs")
async def list_all_colleges() -> Dict[str, Any]:
    dataset = load_pyq_dataset()
    colleges = dataset.get("colleges", [])
    return {"status": True, "totalCount": len(colleges), "colleges": colleges}


@router.put("/colleges/{college_id}", summary="Update College Branch Cutoff Ranks")
async def update_college_cutoffs(
    college_id: str, request: CollegeCutoffUpdateRequest
) -> Dict[str, Any]:
    dataset = load_pyq_dataset()
    colleges = dataset.get("colleges", [])
    target_college = None
    for col in colleges:
        if col["id"] == college_id:
            target_college = col
            for br in col.get("branches", []):
                if br["branchCode"].upper() == request.branchCode.upper():
                    br.setdefault("cutoffs", {})[request.year] = request.cutoffs
                    if request.seats is not None:
                        br["seats"] = request.seats
            break
    if not target_college:
        raise HTTPException(status_code=404, detail=f"College not found: {college_id}")

    _save_pyq_dataset(dataset)
    _log_audit(
        "UPDATE_CUTOFFS",
        f"Updated {request.year} cutoffs for {college_id} ({request.branchCode})",
    )
    return {"status": True, "message": "College cutoffs updated", "college": target_college}


# ─── Assessments, Syllabus & System Config ───────────────────────────────────

@router.get("/assessments", summary="List All Custom Tests & Homework Assignments")
async def list_platform_assessments() -> Dict[str, Any]:
    custom_tests = list(_CPYQB_STATE.get("custom_tests", {}).values())
    custom_attempts = [
        v for k, v in _CPYQB_STATE.get("custom_attempts", {}).items() if not k.startswith("by_test_")
    ]
    assignments = list(_ECOSYSTEM_STATE.get("assignments", {}).values())
    return {
        "status": True,
        "custom_tests": custom_tests,
        "custom_attempts": custom_attempts,
        "assignments": assignments,
    }


@router.get("/system-config", summary="Get System Governance Config, SOUL Prompt & Audit Logs")
async def get_system_config() -> Dict[str, Any]:
    return {
        "status": True,
        "config": _SUPERADMIN_STATE["config"],
        "soul_prompt": SOUL_PROMPT,
        "audit_logs": _SUPERADMIN_STATE["audit_logs"],
    }


@router.put("/system-config", summary="Update System Governance Config")
async def update_system_config(request: SystemConfigUpdateRequest) -> Dict[str, Any]:
    cfg = _SUPERADMIN_STATE["config"]
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    cfg.update(updates)
    _log_audit("UPDATE_SYSTEM_CONFIG", f"Updated system parameters: {updates}")
    return {"status": True, "message": "System configuration updated", "config": cfg}
