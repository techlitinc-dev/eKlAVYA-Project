"""
Development Seed Data

Deterministic seed records for local development and tests, loaded only
through the explicit bootstrap function (never as a production side effect).

Seeded identities:
    student_aarav   student
    student_meera   student
    teacher_rao     teacher, assigned to class_12a and student_aarav
    parent_rajesh   parent, linked to student_aarav
    admin_local     admin

Seed uses fixed ids; records created through the API generate UUIDs.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from datetime import date, timedelta

from core.time import today, utcnow
from models.common import ClassRoom, Identity, ParentLink
from models.communication import (
    CommunicationPreferences,
    Message,
    MessageKind,
)
from models.mindmaps import MapEdge, MapNode, MindMap
from models.notes import Note
from models.planner import PlannerTask, RevisionItem, TaskSource, TaskStatus, TaskType
from models.scans import Scan, ScanIntent, ScanStatus
from models.syllabus import (
    Chapter,
    Subject,
    Syllabus,
    SyllabusProfile,
    Topic,
)

logger = logging.getLogger(__name__)

SYLLABUS_ID = "syl_mock_v1"
SUBJECT_PHYSICS = "sub_physics"
SUBJECT_CHEMISTRY = "sub_chemistry"
SUBJECT_MATH = "sub_math"

STUDENT_AARAV = "student_aarav"
STUDENT_MEERA = "student_meera"
TEACHER_RAO = "teacher_rao"
PARENT_RAJESH = "parent_rajesh"
ADMIN_LOCAL = "admin_local"

CLASS_12A = "class_12a"

# Well-known topic used by scan/planner tests.
TOPIC_KINETIC_ENERGY = "top_kinetic_energy"
TOPIC_CHEMICAL_BONDING = "top_covalent_bonding"
TOPIC_MOMENT_INERTIA = "top_moment_of_inertia"


def bootstrap_development_data(repo) -> None:
    """
    Populate the repository with deterministic development/test data.

    Idempotent: existing seed records with the same ids are replaced with
    identical content, so reseeding between tests is safe.
    """
    _seed_identities(repo)
    _seed_syllabus(repo)
    _seed_profiles(repo)
    _seed_relationships(repo)
    _seed_planner(repo)
    _seed_notes(repo)
    _seed_mindmaps(repo)
    _seed_communication(repo)
    _seed_scans(repo)
    logger.info("Development seed data loaded (%d collections)", len(repo._store))


def _seed_identities(repo) -> None:
    identities = [
        Identity(id=STUDENT_AARAV, role="student", name="Aarav Sharma"),
        Identity(id=STUDENT_MEERA, role="student", name="Meera Iyer"),
        Identity(id=TEACHER_RAO, role="teacher", name="Mrs. Rao"),
        Identity(id=PARENT_RAJESH, role="parent", name="Rajesh Sharma"),
        Identity(id=ADMIN_LOCAL, role="admin", name="Local Admin"),
    ]
    for identity in identities:
        repo.put(identity)


def _seed_syllabus(repo) -> None:
    repo.put(
        Syllabus(
            id=SYLLABUS_ID,
            name="Mock Syllabus",
            version="1.0",
            exam="JEE Main 2027",
        )
    )

    subjects = [
        Subject(id=SUBJECT_PHYSICS, syllabus_id=SYLLABUS_ID, name="Physics", code="PHY"),
        Subject(id=SUBJECT_CHEMISTRY, syllabus_id=SYLLABUS_ID, name="Chemistry", code="CHE"),
        Subject(id=SUBJECT_MATH, syllabus_id=SYLLABUS_ID, name="Mathematics", code="MAT"),
    ]
    for subject in subjects:
        repo.put(subject)

    chapters = [
        Chapter(id="ch_rotational_motion", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_PHYSICS, name="Rotational Motion", order_index=1),
        Chapter(id="ch_work_energy_power", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_PHYSICS, name="Work, Energy and Power", order_index=2),
        Chapter(id="ch_chemical_bonding", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_CHEMISTRY, name="Chemical Bonding", order_index=1),
        Chapter(id="ch_chem_thermodynamics", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_CHEMISTRY, name="Thermodynamics", order_index=2),
        Chapter(id="ch_definite_integration", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_MATH, name="Definite Integration", order_index=1),
        Chapter(id="ch_matrices", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_MATH, name="Matrices and Determinants", order_index=2),
    ]
    for chapter in chapters:
        repo.put(chapter)

    topics = [
        Topic(id=TOPIC_MOMENT_INERTIA, syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_PHYSICS, chapter_id="ch_rotational_motion", name="Moment of Inertia", estimated_minutes=90),
        Topic(id="top_torque_angular_momentum", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_PHYSICS, chapter_id="ch_rotational_motion", name="Torque and Angular Momentum", estimated_minutes=75, prerequisites=[TOPIC_MOMENT_INERTIA]),
        Topic(id="top_rolling_motion", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_PHYSICS, chapter_id="ch_rotational_motion", name="Rolling Motion", estimated_minutes=60, prerequisites=["top_torque_angular_momentum"]),
        Topic(id="top_work_energy_theorem", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_PHYSICS, chapter_id="ch_work_energy_power", name="Work-Energy Theorem", estimated_minutes=60),
        Topic(id=TOPIC_KINETIC_ENERGY, syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_PHYSICS, chapter_id="ch_work_energy_power", name="Kinetic Energy", estimated_minutes=45),
        Topic(id=TOPIC_CHEMICAL_BONDING, syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_CHEMISTRY, chapter_id="ch_chemical_bonding", name="Covalent Bonding and Lewis Structures", estimated_minutes=60),
        Topic(id="top_ionic_bonding", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_CHEMISTRY, chapter_id="ch_chemical_bonding", name="Ionic Bonding", estimated_minutes=45),
        Topic(id="top_hybridization", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_CHEMISTRY, chapter_id="ch_chemical_bonding", name="Hybridization and VSEPR", estimated_minutes=90, prerequisites=[TOPIC_CHEMICAL_BONDING]),
        Topic(id="top_definite_integral_props", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_MATH, chapter_id="ch_definite_integration", name="Properties of Definite Integrals", estimated_minutes=75),
        Topic(id="top_area_under_curve", syllabus_id=SYLLABUS_ID, subject_id=SUBJECT_MATH, chapter_id="ch_definite_integration", name="Area Under Curves", estimated_minutes=90, prerequisites=["top_definite_integral_props"]),
    ]
    for topic in topics:
        repo.put(topic)


def _seed_profiles(repo) -> None:
    repo.put(
        SyllabusProfile(
            id="prof_aarav",
            student_id=STUDENT_AARAV,
            syllabus_id=SYLLABUS_ID,
            target_exam="JEE Main 2027",
            target_year=2027,
            target_date=date(2027, 1, 24),
            subjects=[SUBJECT_PHYSICS, SUBJECT_CHEMISTRY, SUBJECT_MATH],
            availability={"minutes_per_day": 180, "days_per_week": 6},
            preferences={"buffer_ratio": 0.1},
        )
    )
    repo.put(
        SyllabusProfile(
            id="prof_meera",
            student_id=STUDENT_MEERA,
            syllabus_id=SYLLABUS_ID,
            target_exam="JEE Main 2027",
            target_year=2027,
            target_date=date(2027, 1, 24),
            subjects=[SUBJECT_PHYSICS, SUBJECT_CHEMISTRY],
            availability={"minutes_per_day": 120, "days_per_week": 6},
        )
    )


def _seed_relationships(repo) -> None:
    repo.put(
        ClassRoom(
            id=CLASS_12A,
            name="Class 12-A",
            teacher_ids=[TEACHER_RAO],
            student_ids=[STUDENT_AARAV],
        )
    )
    repo.put(ParentLink(id="plink_rajesh_aarav", parent_id=PARENT_RAJESH, student_id=STUDENT_AARAV))


def _seed_planner(repo) -> None:
    today_ = today()
    repo.put(
        PlannerTask(
            id="task_seed_1",
            student_id=STUDENT_AARAV,
            title="Practice Kinetic Energy problems",
            task_type=TaskType.practice,
            status=TaskStatus.pending,
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_PHYSICS,
            chapter_id="ch_work_energy_power",
            topic_id=TOPIC_KINETIC_ENERGY,
            scheduled_date=today_,
            start_minute=9 * 60,
            duration_minutes=60,
            source=TaskSource.manual,
            created_by=STUDENT_AARAV,
        )
    )
    repo.put(
        PlannerTask(
            id="task_seed_2",
            student_id=STUDENT_AARAV,
            title="Revise Covalent Bonding notes",
            task_type=TaskType.revision,
            status=TaskStatus.pending,
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_CHEMISTRY,
            chapter_id="ch_chemical_bonding",
            topic_id=TOPIC_CHEMICAL_BONDING,
            scheduled_date=today_,
            start_minute=14 * 60,
            duration_minutes=45,
            source=TaskSource.manual,
            created_by=STUDENT_AARAV,
        )
    )
    repo.put(
        PlannerTask(
            id="task_seed_3",
            student_id=STUDENT_AARAV,
            title="Completed Rotational Motion drill",
            task_type=TaskType.practice,
            status=TaskStatus.completed,
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_PHYSICS,
            chapter_id="ch_rotational_motion",
            topic_id=TOPIC_MOMENT_INERTIA,
            scheduled_date=today_ - timedelta(days=1),
            start_minute=10 * 60,
            duration_minutes=60,
            completed_at=utcnow() - timedelta(hours=20),
            actual_minutes=55,
            source=TaskSource.manual,
            created_by=STUDENT_AARAV,
        )
    )
    repo.put(
        RevisionItem(
            id="rev_seed_1",
            student_id=STUDENT_AARAV,
            title="Revise Rotational Motion",
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_PHYSICS,
            chapter_id="ch_rotational_motion",
            due_date=today_,
            source=TaskSource.manual,
        )
    )
    repo.put(
        PlannerTask(
            id="task_seed_meera",
            student_id=STUDENT_MEERA,
            title="Meera private task",
            task_type=TaskType.practice,
            status=TaskStatus.pending,
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_MATH,
            chapter_id="ch_matrices",
            scheduled_date=today_,
            start_minute=10 * 60,
            duration_minutes=60,
            source=TaskSource.manual,
            created_by=STUDENT_MEERA,
        )
    )


def _seed_notes(repo) -> None:
    repo.put(
        Note(
            id="note_seed_1",
            owner_id=STUDENT_AARAV,
            title="Rotational Motion Formula Sheet",
            body="tau = dL/dt. K = 1/2 I omega^2. Parallel axis: I = I_cm + M d^2.",
            tags=["physics", "formulas"],
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_PHYSICS,
            chapter_id="ch_rotational_motion",
        )
    )
    repo.put(
        Note(
            id="note_seed_2",
            owner_id=STUDENT_AARAV,
            title="Chemical Bonding Summary",
            body="Sigma bonds form by head-on overlap; pi bonds by side-on overlap.",
            tags=["chemistry"],
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_CHEMISTRY,
            chapter_id="ch_chemical_bonding",
            topic_id=TOPIC_CHEMICAL_BONDING,
        )
    )
    repo.put(
        Note(
            id="note_seed_3",
            owner_id=STUDENT_AARAV,
            title="Kinetic Energy Mistakes",
            body="Remember KE uses speed squared; rotating bodies also carry rotational KE.",
            tags=["physics", "mistakes"],
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_PHYSICS,
            chapter_id="ch_work_energy_power",
            topic_id=TOPIC_KINETIC_ENERGY,
        )
    )
    repo.put(
        Note(
            id="note_seed_meera",
            owner_id=STUDENT_MEERA,
            title="Meera private note",
            body="Private content belonging to Meera.",
            tags=["private"],
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_CHEMISTRY,
            chapter_id="ch_chemical_bonding",
        )
    )


def _seed_mindmaps(repo) -> None:
    root_rot = MapNode(
        id="node_rot_root", map_id="map_seed_rotational", label="Rotational Motion",
        parent_id=None,
    )
    child_1 = MapNode(
        id="node_rot_torque", map_id="map_seed_rotational", label="Torque",
        parent_id="node_rot_root", note_id="note_seed_1",
    )
    child_2 = MapNode(
        id="node_rot_inertia", map_id="map_seed_rotational", label="Moment of Inertia",
        parent_id="node_rot_root",
    )
    repo.put(
        MindMap(
            id="map_seed_rotational",
            owner_id=STUDENT_AARAV,
            title="Rotational Motion",
            root_node_id="node_rot_root",
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_PHYSICS,
            chapter_id="ch_rotational_motion",
        )
    )
    for node in (root_rot, child_1, child_2):
        repo.put(node)
    repo.put(MapEdge(id="edge_rot_1", map_id="map_seed_rotational", source_node_id="node_rot_root", target_node_id="node_rot_torque"))
    repo.put(MapEdge(id="edge_rot_2", map_id="map_seed_rotational", source_node_id="node_rot_root", target_node_id="node_rot_inertia"))

    root_bond = MapNode(
        id="node_bond_root", map_id="map_seed_bonding", label="Chemical Bonding",
        parent_id=None,
    )
    child_b1 = MapNode(
        id="node_bond_covalent", map_id="map_seed_bonding", label="Covalent Bonding",
        parent_id="node_bond_root",
    )
    repo.put(
        MindMap(
            id="map_seed_bonding",
            owner_id=STUDENT_AARAV,
            title="Chemical Bonding",
            root_node_id="node_bond_root",
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_CHEMISTRY,
            chapter_id="ch_chemical_bonding",
        )
    )
    for node in (root_bond, child_b1):
        repo.put(node)
    repo.put(MapEdge(id="edge_bond_1", map_id="map_seed_bonding", source_node_id="node_bond_root", target_node_id="node_bond_covalent"))


def _seed_communication(repo) -> None:
    repo.put(
        Message(
            id="msg_seed_1",
            recipient_id=PARENT_RAJESH,
            sender_id=TEACHER_RAO,
            kind=MessageKind.announcement,
            title="Welcome to eKlAVYA",
            body="Weekly progress summaries are enabled for Aarav.",
        )
    )
    repo.put(
        Message(
            id="msg_seed_2",
            recipient_id=STUDENT_AARAV,
            sender_id=TEACHER_RAO,
            kind=MessageKind.system,
            title="Class update",
            body="Class 12-A syllabus template published.",
        )
    )
    repo.put(
        Message(
            id="msg_seed_3",
            recipient_id=STUDENT_AARAV,
            sender_id=None,
            kind=MessageKind.system,
            title="Revision reminder",
            body="Rotational Motion revision is due today.",
        )
    )
    repo.put(
        CommunicationPreferences(
            id="commpref_rajesh",
            user_id=PARENT_RAJESH,
            quiet_hours_enabled=True,
            quiet_hours_start=21,
            quiet_hours_end=7,
            max_calls_per_day=5,
        )
    )


def _seed_scans(repo) -> None:
    repo.put(
        Scan(
            id="scan_seed_meera",
            owner_id=STUDENT_MEERA,
            intent=ScanIntent.solve,
            status=ScanStatus.created,
            syllabus_id=SYLLABUS_ID,
            subject_id=SUBJECT_CHEMISTRY,
        )
    )
