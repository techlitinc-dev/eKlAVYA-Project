# eKlAVYA Backend — Working API Endpoints

Syllabus-bound study planner backend: syllabus catalogue + profiles, planner
(tasks, deterministic generation/replanning, study sessions, revision),
notes (versions, links, sharing, mock AI actions), mind maps (tree
operations, revisions, export), scan & solve (private uploads, mock OCR,
grounded mock answers, result actions), mock speech assets, simulated
one-way in-app calls with delivery state machine, messages, and teacher /
parent endpoints.

All eKlAVYA endpoints live under `/api/v1`. The documented error envelope is
`{"error": {"code", "message", "details", "request_id"}}`.

## Requirements

- Python 3.10+
- `pip install -r requirements.txt` (already includes FastAPI, pydantic 2,
  python-multipart, pytest)

No Firebase, Gemini, Jev, Sarvam, or internet access is required. The app
starts cleanly with zero credentials.

## Configuration

Copy the eKlAVYA section of `.env.example` (all values are safe defaults):

```bash
cd Backend
cp .env.example .env   # optional; defaults work without a .env file
```

Key settings: `TESTING_MODE=true` (development header authentication — never
enable in production; startup refuses `ENVIRONMENT=production` with
`TESTING_MODE=true`), `REPOSITORY_BACKEND=memory`, `MOCK_PROVIDERS=true`,
`LOCAL_UPLOAD_DIR`/`LOCAL_MEDIA_DIR` (gitignored `local_data/`).

## Run

```bash
cd Backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verify:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/docs (Swagger UI)
- http://127.0.0.1:8000/api/openapi.json

## Test

```bash
cd Backend
python -m pytest -q
```

The eKlAVYA suite (`tests/test_syllabus_api.py`, `test_planner_api.py`,
`test_notes_api.py`, `test_mindmap_api.py`, `test_scan_api.py`,
`test_speech_api.py`, `test_simulated_call_api.py`, `test_permissions.py`,
`test_smoke_sequence.py`) runs against the in-memory repository with
deterministic seed data. Legacy ad-hoc scripts in `tests/` are excluded via
`collect_ignore` in `tests/conftest.py`.

## Development authentication (TESTING_MODE=true)

```http
X-User-Id: student_aarav
X-User-Role: student
X-User-Name: Aarav Sharma
```

Roles: `student`, `teacher`, `parent`, `admin`. Seeded identities:
`student_aarav`, `student_meera`, `teacher_rao` (assigned to `class_12a`
and Aarav), `parent_rajesh` (linked to Aarav), `admin_local`. When
`TESTING_MODE=false`, the real Firebase Bearer-token path is used instead;
role headers are never production authentication.

## Mock providers (deterministic, local)

| Provider | File | Notes |
| --- | --- | --- |
| OCR | `providers/mock_ocr.py` | Recognizes the `EKLAVYA_SAMPLE` fixture; always flags uncertain regions |
| Answering | `providers/mock_answer.py` | Sample question → `9 J` with `1/2 mv^2` steps, approved mock citation; unsupported input → `needs_clarification` / `insufficient_sources` (never an invented answer) |
| Speech | `providers/mock_speech.py` | Short valid SILENT WAV, explicitly marked mock (not synthesized speech) |
| Decision | `providers/mock_decision.py` | Internal routing: syllabus relevance, OCR confirmation, answer review, communication approval |

Real providers can be added later behind the interfaces in `providers/base.py`
with feature flags; no provider credentials are exposed to clients.

## Architecture

- `core/` — config, error contract, ids, UTC time, auth principals, access rules
- `models/` — pydantic entities + API schemas per domain (`models/common.py` shared)
- `repositories/` — `Repository` interface + `InMemoryRepository`
  (process-lifetime, thread-safe, reset between tests; NOT production persistence)
- `services/` — business logic (one module per domain + `audit_service`, `grounding_service`)
- `providers/` — deterministic local provider adapters
- `routers/` — thin HTTP layer; `routers/eklavya_registry.py` enumerates the
  nine eKlAVYA routers registered in `main.py` under `/api/v1`
- `seed.py` — explicit development/test bootstrap (`bootstrap_development_data`)
- `tests/` — pytest suite with fresh seeded repository per test

Cross-cutting rules implemented centrally: cursor pagination (`limit` ≤ 100),
`Idempotency-Key` replay/conflict, optimistic concurrency (`version`),
relationship-based authorization (students own; teachers via assigned
classes; parents read-only for linked children; admin all), audit logging
without private bodies or secrets.

## Scope exclusions

No telephony, phone numbers, WebRTC, microphone endpoints, two-way calls,
payments, CBT examinations, rank predictors, gamification, or course
marketplace. Simulated calls are in-app audio announcements only.
