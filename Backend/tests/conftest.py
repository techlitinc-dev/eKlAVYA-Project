"""
pytest Configuration for eKlAVYA API Tests

- Excludes legacy ad-hoc test scripts (they require Firebase/Gemini and are
  not part of the eKlAVYA suite).
- Installs a freshly seeded in-memory repository per test.
- Neutralizes the legacy global rate limiter for the test suite (the
  eKlAVYA RATE_LIMITED behavior is tested at service level instead).
"""

import pytest
from fastapi.testclient import TestClient

# Legacy scripts under tests/ are not part of the eKlAVYA suite.
collect_ignore = [
    "comprehensive_endpoint_test.py",
    "create_test_student.py",
    "debug_gemini_response.py",
    "debug_question_generation_detailed.py",
    "debug_question_validation.py",
    "init_firestore.py",
    "run_endpoint_tests.py",
    "simple_child_login_test.py",
    "simple_test_study_center.py",
    "smoke_test_hermes.py",
    "test_all_endpoints.py",
    "test_batch_api.py",
    "test_batch_simple.py",
    "test_child_login.py",
    "test_endpoints_mock.py",
    "test_endpoints_mock_fixed.py",
    "test_gemini_endpoint.py",
    "test_hermes.py",
    "test_hermes_features.py",
    "test_marks_and_sathee_endpoints.py",
    "test_rag_endpoint_simple.py",
    "test_study_center_api.py",
    "test_validation_simple.py",
    "validate_child_login.py",
]

# Neutralize the legacy middleware rate limiter for tests. eKlAVYA
# RATE_LIMITED behavior (simulated-call frequency limits) is enforced in the
# communication service and tested directly.
from middleware import rate_limiter as _legacy_rate_limiter

_legacy_rate_limiter.RATE_LIMITS.clear()
_legacy_rate_limiter.RATE_LIMITS["default"] = 1_000_000
_legacy_rate_limiter.GLOBAL_RATE_LIMIT = 1_000_000_000

# Deterministic development identities (seed.py)
STUDENT_AARAV = "student_aarav"
STUDENT_MEERA = "student_meera"
TEACHER_RAO = "teacher_rao"
PARENT_RAJESH = "parent_rajesh"
ADMIN_LOCAL = "admin_local"
CLASS_12A = "class_12a"

SYLLABUS_ID = "syl_mock_v1"
SUBJECT_PHYSICS = "sub_physics"
SUBJECT_CHEMISTRY = "sub_chemistry"
CHAPTER_ROTATIONAL = "ch_rotational_motion"
CHAPTER_WORK_ENERGY = "ch_work_energy_power"
CHAPTER_CHEM_BONDING = "ch_chemical_bonding"
TOPIC_KINETIC_ENERGY = "top_kinetic_energy"
TOPIC_CHEMICAL_BONDING = "top_covalent_bonding"
TOPIC_MOMENT_INERTIA = "top_moment_of_inertia"


def auth_headers(user_id: str, role: str = "student", name: str = None) -> dict:
    """Development identity headers for TESTING_MODE authentication."""
    headers = {"X-User-Id": user_id, "X-User-Role": role}
    if name:
        headers["X-User-Name"] = name
    return headers


@pytest.fixture()
def app():
    from main import app as fastapi_app

    return fastapi_app


@pytest.fixture(autouse=True)
def fresh_repository(app):
    """Install a freshly seeded repository before every test."""
    from repositories.memory import InMemoryRepository
    from seed import bootstrap_development_data

    repository = InMemoryRepository()
    bootstrap_development_data(repository)
    app.state.repository = repository
    yield repository


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client
