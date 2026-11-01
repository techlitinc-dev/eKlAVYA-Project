# Instructions for the AI Coding Agent — eKlAVYA Working Backend Endpoints

## 1. Read before coding

Read these documents completely before changing the repository:

1. `features.md`
2. `spec.md`
3. This file, `endpoint_instructions.md`

Your task is to implement **working FastAPI endpoints** for eKlAVYA, a syllabus-bound study planner with notes, mind maps, scan-and-solve, and simulated one-way in-app calls.

You are working on the backend only. Do not build or modify the Flutter UI in this task.

The endpoints must perform real local state changes and pass automated tests. Do not return hard-coded success responses for operations that should create, update, retrieve, or delete data.

## 2. Most important rule

A “working endpoint” means all of the following:

- The request is validated with Pydantic.
- Authentication and role checks are applied.
- The requested operation changes or reads authoritative application state.
- Syllabus references are validated.
- Errors use the documented response format.
- Repeating an idempotent request does not create duplicates.
- The endpoint is registered in FastAPI and appears in OpenAPI.
- Automated tests verify both success and failure behavior.

A router function that only returns a prepared JSON example is not a working implementation.

## 3. Scope restrictions for this task

Do not add:

- Outbound telephone calls
- Telephony providers
- Two-way calls
- WebRTC
- Microphone handling
- Real Jev-Shim calls by default
- Real Sarvam.ai calls by default
- Real OCR or LLM calls by default
- Payments
- CBT examinations
- Rank predictors
- Gamification
- Course-marketplace features

Provide deterministic local development providers for OCR, answering, speech, and decisions. Real providers can only be added behind separate adapter interfaces and feature flags after the required local workflows pass.

Do not expose provider credentials to clients.

## 4. Existing repository rules

- Work inside the existing `Backend/` FastAPI application.
- Reuse suitable existing authentication, configuration, and database abstractions.
- Do not duplicate an existing endpoint under a slightly different path.
- Do not delete unrelated working routers.
- Do not rewrite the whole backend to complete this task.
- Do not add a second FastAPI application.
- Register new routers in the existing `main.py`.
- Keep new endpoints under `/api/v1`.
- Preserve existing health and documentation endpoints.
- Update the root and backend setup documentation only where necessary to run and test the new endpoints.

If existing code conflicts with these instructions, isolate new code behind clean services rather than modifying many unrelated files.

## 5. Required architecture

Use this logical structure:

```text
Backend/
├── main.py
├── core/
│   ├── config.py
│   ├── errors.py
│   ├── security.py
│   ├── ids.py
│   └── time.py
├── models/
│   ├── common.py
│   ├── syllabus.py
│   ├── planner.py
│   ├── notes.py
│   ├── mindmaps.py
│   ├── scans.py
│   ├── speech.py
│   └── communication.py
├── repositories/
│   ├── base.py
│   ├── memory.py
│   └── firestore_repository.py        # only if fully implemented
├── services/
│   ├── syllabus_service.py
│   ├── planner_service.py
│   ├── notes_service.py
│   ├── mindmap_service.py
│   ├── scan_service.py
│   ├── grounding_service.py
│   ├── speech_service.py
│   ├── simulated_call_service.py
│   └── audit_service.py
├── providers/
│   ├── base.py
│   ├── mock_ocr.py
│   ├── mock_answer.py
│   ├── mock_speech.py
│   └── mock_decision.py
├── routers/
│   ├── syllabus_router.py
│   ├── planner_router.py
│   ├── notes_router.py
│   ├── mindmap_router.py
│   ├── scan_router.py
│   ├── speech_router.py
│   ├── communication_router.py
│   ├── teacher_router.py
│   └── parent_router.py
└── tests/
    ├── conftest.py
    ├── test_syllabus_api.py
    ├── test_planner_api.py
    ├── test_notes_api.py
    ├── test_mindmap_api.py
    ├── test_scan_api.py
    ├── test_speech_api.py
    ├── test_simulated_call_api.py
    └── test_permissions.py
```

Exact filenames may vary, but routers, schemas, services, repositories, providers, and tests must remain separated.

Do not place business logic directly in router functions.

## 6. Configuration

Add explicit settings for:

```text
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
TESTING_MODE=true
REPOSITORY_BACKEND=memory
LOCAL_UPLOAD_DIR=./local_data/uploads
LOCAL_MEDIA_DIR=./local_data/media
MOCK_PROVIDERS=true
MAX_UPLOAD_MB=10
MAX_SCAN_PAGES=10
SIMULATED_CALL_RING_SECONDS=45
```

Rules:

- Do not commit real `.env` files or credentials.
- Update `.env.example` with safe sample values.
- Local upload and media directories must be gitignored.
- `TESTING_MODE` authentication must never be silently enabled in production.
- Default local tests must run without Firebase, Gemini, Jev, Sarvam, or internet access.

## 7. Development authentication and authorization

### 7.1 Development identity

When `TESTING_MODE=true`, accept these headers:

```text
X-User-Id: student_aarav
X-User-Role: student
X-User-Name: Aarav Sharma
```

Supported roles:

- `student`
- `teacher`
- `parent`
- `admin`

When testing mode is disabled, use the existing real authentication dependency. Do not treat role headers as production authentication.

### 7.2 Test relationships

Seed these identities for local development and tests:

```text
student_aarav       student
student_meera       student
teacher_rao         teacher, assigned to class_12a and student_aarav
parent_rajesh       parent, linked to student_aarav
admin_local         admin
```

Required authorization behavior:

- Students can access only their own records.
- Aarav cannot access Meera’s notes, scans, tasks, audio, calls, or progress.
- Mrs. Rao can access Aarav only through the assigned class relationship.
- Mrs. Rao cannot access Meera unless separately assigned.
- Rajesh can access only Aarav’s permitted read-only progress and his own messages.
- Parents cannot modify student tasks or notes.
- Admin endpoints require the admin role.
- Hiding a record is not enough; return the documented authorization error.

Use `403` for an authenticated user without permission and `404` where necessary to avoid exposing another user’s private record.

## 8. Common API contracts

### 8.1 Success responses

Return the resource directly or use one consistent envelope. Do not mix styles randomly.

For created resources, return `201 Created`.

For deletes, return `204 No Content` unless a response body is explicitly required.

### 8.2 Error response

Use:

```json
{
  "error": {
    "code": "SYLLABUS_CONTEXT_INVALID",
    "message": "The selected topic does not belong to the active syllabus.",
    "details": {},
    "request_id": "req_123"
  }
}
```

Do not return Python tracebacks or raw provider errors to clients.

Required common codes:

```text
VALIDATION_ERROR
AUTHENTICATION_REQUIRED
PERMISSION_DENIED
NOT_FOUND
SYLLABUS_CONTEXT_INVALID
RESOURCE_CONFLICT
IDEMPOTENCY_CONFLICT
INVALID_STATE_TRANSITION
UPLOAD_TOO_LARGE
UPLOAD_TYPE_NOT_ALLOWED
OCR_CONFIRMATION_REQUIRED
GROUNDING_FAILED
PROVIDER_UNAVAILABLE
RATE_LIMITED
```

### 8.3 Identifiers and timestamps

- Generate UUID-based IDs on the server.
- Store timestamps in UTC.
- Return ISO 8601 timestamps.
- Do not accept client-supplied IDs as authoritative without validation.

### 8.4 Pagination

List endpoints must support:

```text
limit: default 20, maximum 100
cursor: optional opaque cursor
```

Return:

```json
{
  "items": [],
  "next_cursor": null
}
```

### 8.5 Idempotency

Creation, generation, execution, speech, and simulated-call endpoints must accept:

```text
Idempotency-Key: unique-client-key
```

Rules:

- Same user + same key + same request body returns the original result.
- Same key with a different body returns `409 IDEMPOTENCY_CONFLICT`.
- Store the key and response for the local development retention period.
- Tests must prove duplicate creation is prevented.

### 8.6 Optimistic concurrency

Task, note, and mind-map updates must support a `version` integer.

- Clients send the version they read.
- Successful updates increment the version.
- Stale versions return `409 RESOURCE_CONFLICT`.
- Do not silently overwrite newer edits.

## 9. Repository requirements

Implement a repository interface with an in-memory implementation for local development and tests.

The in-memory repository must:

- Be shared through FastAPI dependency injection, not recreated per request.
- Store all resource types.
- Support reset between tests.
- Protect mutations sufficiently for the local test server.
- Persist state for the lifetime of the application process.
- Never be presented as production persistence.

If Firestore is implemented, it must satisfy the same service and API tests. Do not leave a half-written Firestore class that crashes application startup.

## 10. Seed data

Create deterministic seed data for:

- Mock Syllabus v1.0
- JEE Main 2027 student profile for Aarav
- Physics, Chemistry, and Mathematics
- Chapters and topics from the product documents
- Today’s planner tasks
- One revision item
- At least three notes
- Rotational Motion and Chemical Bonding mind maps
- Three sample messages
- Teacher and parent relationships

Use fixed test IDs for seed records, but generate UUIDs for newly created records.

Seed data must be loaded through an explicit development/test bootstrap function, not as an unwanted side effect in production.

## 11. Syllabus endpoints

Implement:

```http
GET    /api/v1/syllabi
GET    /api/v1/syllabi/{syllabusId}
GET    /api/v1/syllabi/{syllabusId}/subjects
GET    /api/v1/subjects/{subjectId}/chapters
GET    /api/v1/chapters/{chapterId}/topics
GET    /api/v1/me/syllabus-profile
PUT    /api/v1/me/syllabus-profile
GET    /api/v1/me/syllabus-progress
POST   /api/v1/teacher/syllabus-templates
POST   /api/v1/teacher/syllabus-templates/{templateId}/publish
```

### Required behavior

- Validate parent-child hierarchy.
- Reject a topic that does not belong to the supplied chapter or syllabus.
- `PUT /me/syllabus-profile` updates availability, target date, subjects, and preferences.
- Progress is calculated from topic/task state, not a hard-coded percentage.
- Only teachers/admins can create templates.
- Only teachers/admins can publish their authorized templates.
- Publishing sets status and timestamp and prevents accidental duplicate publishing.

## 12. Planner endpoints

Implement:

```http
GET    /api/v1/planner/today
GET    /api/v1/planner/tasks?from=&to=&status=&subjectId=&limit=&cursor=
POST   /api/v1/planner/tasks
GET    /api/v1/planner/tasks/{taskId}
PATCH  /api/v1/planner/tasks/{taskId}
POST   /api/v1/planner/tasks/{taskId}/complete
POST   /api/v1/planner/tasks/{taskId}/reschedule
POST   /api/v1/planner/generate
POST   /api/v1/planner/replan
GET    /api/v1/planner/generation-jobs/{jobId}
POST   /api/v1/study-sessions
PATCH  /api/v1/study-sessions/{sessionId}
GET    /api/v1/revision/due
POST   /api/v1/revision/{revisionId}/complete
```

### Required task behavior

- `POST` creates a task belonging to the authenticated student.
- Validate syllabus context, date, duration, type, and subject.
- `GET today` returns progress and tasks for the student’s current date.
- Filters compose correctly.
- Completion records actual completion time and updates progress.
- Repeating completion with the same idempotency key does not duplicate study time.
- Rescheduling records previous and new schedule values.
- Locked tasks cannot be moved by automatic replanning.
- Completed tasks cannot be moved by automatic replanning.
- Students cannot modify teacher-locked fields unless permitted.

### Generate and replan

Implement a deterministic local planner, not an AI call.

Generation must:

1. Validate the profile.
2. Calculate available study capacity.
3. Preserve fixed commitments.
4. Respect topic prerequisites where supplied.
5. Create non-overlapping tasks.
6. Include buffer/revision where configured.
7. Return warnings if all topics cannot fit.
8. Persist a plan and tasks atomically.

Replanning must:

- Move only eligible pending tasks.
- Preserve completed and locked tasks.
- Avoid duplicate tasks.
- Record rescheduling history.
- Return a human-readable explanation and warnings.

### Study sessions

- Start, pause/resume through patch actions, and finish sessions.
- Calculate elapsed time from recorded intervals.
- Reject invalid transitions such as finishing an already finished session.
- Link completion to a task only once.

## 13. Notes endpoints

Implement:

```http
GET    /api/v1/notes?query=&topicId=&tag=&limit=&cursor=
POST   /api/v1/notes
GET    /api/v1/notes/{noteId}
PATCH  /api/v1/notes/{noteId}
DELETE /api/v1/notes/{noteId}
GET    /api/v1/notes/{noteId}/versions
POST   /api/v1/notes/{noteId}/restore
POST   /api/v1/notes/{noteId}/attachments
POST   /api/v1/notes/{noteId}/links
DELETE /api/v1/notes/{noteId}/links/{linkedNoteId}
POST   /api/v1/notes/{noteId}/export
POST   /api/v1/notes/{noteId}/share
POST   /api/v1/notes/{noteId}/ai-actions
```

### Required behavior

- Create, read, update, and archive/delete real notes.
- Search title, body, OCR text, and tags.
- Filter by topic and tag.
- Validate syllabus context.
- Update creates a version and increments the current version.
- Restore creates a new version based on an older version; it does not erase history.
- Links cannot point to nonexistent or unauthorized notes.
- Prevent direct self-links.
- Export creates a local text or simple PDF artifact; a plain-text export is acceptable for local development if labelled correctly.
- Sharing modifies an explicit sharing scope and records an audit entry.

### Mock AI actions

Support:

- `summarize`
- `structure`
- `extract_formulas`
- `extract_mistakes`
- `generate_mindmap`
- `create_planner_tasks`

These actions use deterministic local providers. They must create a new note version or proposed resources without silently overwriting the original note.

## 14. Mind-map endpoints

Implement:

```http
GET    /api/v1/mindmaps?limit=&cursor=
POST   /api/v1/mindmaps
GET    /api/v1/mindmaps/{mapId}
PATCH  /api/v1/mindmaps/{mapId}
DELETE /api/v1/mindmaps/{mapId}
POST   /api/v1/mindmaps/{mapId}/nodes
PATCH  /api/v1/mindmaps/{mapId}/nodes/{nodeId}
DELETE /api/v1/mindmaps/{mapId}/nodes/{nodeId}
POST   /api/v1/mindmaps/{mapId}/edges
DELETE /api/v1/mindmaps/{mapId}/edges/{edgeId}
POST   /api/v1/mindmaps/{mapId}/generate
POST   /api/v1/mindmaps/{mapId}/regenerate-branch
GET    /api/v1/mindmaps/{mapId}/revisions
POST   /api/v1/mindmaps/{mapId}/export
```

### Required behavior

- Every map has exactly one root node.
- Root deletion is rejected.
- Child deletion handles descendants and related edges consistently.
- Parent and edge references must belong to the same map.
- Cycles that invalidate the tree/map structure are rejected where applicable.
- Updates use optimistic concurrency.
- Generate uses a deterministic mock provider and saves a revision.
- Branch regeneration preserves `manually_locked` nodes.
- Export returns valid structured JSON; additional formats are optional.

## 15. Scan & Solve endpoints

Implement:

```http
POST   /api/v1/scans
POST   /api/v1/scans/{scanId}/pages
POST   /api/v1/scans/{scanId}/process
GET    /api/v1/scans/{scanId}
GET    /api/v1/scans/{scanId}/ocr
PUT    /api/v1/scans/{scanId}/ocr-confirmation
POST   /api/v1/scans/{scanId}/execute
GET    /api/v1/scans/{scanId}/result
POST   /api/v1/scans/{scanId}/save-note
POST   /api/v1/scans/{scanId}/create-mindmap
POST   /api/v1/scans/{scanId}/schedule-revision
```

### 15.1 Upload behavior

- `POST /scans` creates a scan with intent and syllabus context.
- Page upload uses `multipart/form-data`.
- Allow only configured PNG/JPEG/PDF content for local development.
- Validate actual content signatures where practical.
- Enforce page count and file size.
- Store files under the configured private local directory using generated names.
- Do not use the original filename as a safe storage path.
- Return asset metadata, not a public filesystem path.

### 15.2 Mock OCR provider

The local provider must return deterministic OCR output and uncertain regions.

For the supplied sample fixture, recognize:

```text
A block of mass 2 kg moves at 3 m/s on a frictionless horizontal surface. Find its kinetic energy.
```

Processing sets the scan to `confirmation_required` when confirmation is needed.

`PUT ocr-confirmation` stores corrected text and marks the scan confirmed.

`execute` must reject unconfirmed scans when confirmation is required.

### 15.3 Mock answer provider

For the confirmed sample question, return:

- Final answer: `9 J`
- Correct `1/2 mv²` steps
- Physics / Work, Energy and Power / Kinetic Energy mapping
- Approved mock resource citation
- Grounding status: `grounded`
- Verification status: `verified_by_mock_rule`

For unsupported input:

- Do not invent a confident numeric answer.
- Return `needs_clarification`, `insufficient_sources`, or `teacher_review_required` as appropriate.
- Tests must verify this behavior.

### 15.4 Result actions

- Save Note creates one note linked to the scan.
- Create Mind Map creates one map linked to the scan.
- Schedule Revision creates a revision item/task linked to the scan.
- Idempotent retries return the originally created resource.
- Repeating an action without a key must still avoid accidental duplicates using a unique constraint on scan + action where practical.

### 15.5 Other intents

Support:

- `solve`
- `check_steps`
- `digitize`
- `summarize`
- `mindmap`
- `revision_tasks`

Return distinct appropriate result schemas and state transitions for each intent. Do not return the solve-question result for every intent.

## 16. Speech endpoints

Implement:

```http
POST   /api/v1/speech
GET    /api/v1/speech/{speechAssetId}
GET    /api/v1/speech/{speechAssetId}/playback-url
```

### Local mock behavior

- Accept source type, source ID, transcript, language, and voice settings.
- Authorize access to the source content.
- Generate a deterministic `SpeechAsset` using `MockSpeechProvider`.
- The mock provider may create a short valid silent WAV file using Python’s standard library, but it must be explicitly marked as a mock asset and must not be described as synthesized speech.
- Store the transcript and asset metadata.
- Return a local authorized playback route or signed-style development URL.
- Only authorized users can retrieve the asset.
- Cache repeated identical requests by content hash and settings.
- Provider failures leave the source transcript available.

Do not integrate Sarvam in this task. Leave a clear provider interface for a later implementation.

## 17. Simulated-call endpoints

Implement:

```http
POST   /api/v1/simulated-calls
GET    /api/v1/simulated-calls
GET    /api/v1/simulated-calls/{callId}
POST   /api/v1/simulated-calls/{callId}/cancel
GET    /api/v1/me/simulated-calls
POST   /api/v1/me/simulated-calls/{deliveryId}/accept
POST   /api/v1/me/simulated-calls/{deliveryId}/dismiss
POST   /api/v1/me/simulated-calls/{deliveryId}/playback-started
POST   /api/v1/me/simulated-calls/{deliveryId}/complete
GET    /api/v1/messages
POST   /api/v1/messages/{messageId}/read
```

### 17.1 Creation

Teachers may create calls for assigned students and linked parents.

AI-agent creation is represented by an internal service call or admin-authorized development endpoint; students must not be able to impersonate a teacher or AI sender.

Creation must:

- Validate recipients and relationships.
- Validate syllabus context for academic messages.
- Validate transcript and subject.
- Apply quiet hours, deduplication, and frequency limits.
- Create one parent call record and one delivery per recipient.
- Attach an existing authorized speech asset or use transcript-only mode.
- Return all delivery IDs and states.

### 17.2 Delivery states

Implement exactly:

```text
scheduled
ringing
accepted
playing
completed
dismissed
missed
failed
cancelled
```

Allowed main path:

```text
scheduled → ringing → accepted → playing → completed
```

Other paths:

```text
scheduled → cancelled
ringing → dismissed
ringing → missed
ringing → failed
accepted → failed
playing → failed
```

Rules:

- Accept is valid only for the recipient and only from an allowed state.
- Playback-started moves accepted to playing.
- Complete is idempotent.
- Dismiss creates/updates the corresponding message history.
- Cancel affects eligible scheduled deliveries.
- Invalid transitions return `409 INVALID_STATE_TRANSITION`.
- State changes record timestamps and increment an event version.
- `GET /me/simulated-calls` returns only the authenticated recipient’s deliveries.

### 17.3 No real calling

Do not add:

- Phone numbers
- Telephony API clients
- WebRTC tokens
- Microphone endpoints
- Realtime voice sessions
- Outbound-call status fields

This API represents an in-app audio announcement only.

## 18. Teacher and parent endpoints

Implement:

```http
GET    /api/v1/teacher/classes/{classId}/progress
POST   /api/v1/teacher/classes/{classId}/tasks
POST   /api/v1/teacher/classes/{classId}/resources
GET    /api/v1/teacher/reviews
POST   /api/v1/teacher/reviews/{reviewId}/resolve
GET    /api/v1/parent/children
GET    /api/v1/parent/children/{studentId}/progress
GET    /api/v1/parent/children/{studentId}/reports
GET    /api/v1/parent/communication-preferences
PUT    /api/v1/parent/communication-preferences
```

Required behavior:

- Teacher class access is verified.
- Teacher task creation creates tasks for selected authorized students.
- Resource sharing records class scope.
- Review resolution stores teacher correction and resolution timestamp.
- Parent progress is read-only and limited to linked children.
- Reports are generated from persisted task/progress state.
- Parent preferences affect subsequent communication scheduling.

## 19. Internal decision-provider interface

Do not expose a public Jev endpoint.

Create a small internal `DecisionProvider` interface and a deterministic `MockDecisionProvider` for routes such as:

- Syllabus relevance
- OCR confirmation
- Answer review routing
- Communication approval

Hard permission rules must execute before any provider decision.

Provider failures must use a documented safe fallback. Core CRUD must not depend on the provider.

Do not add Node.js or Jev-Shim until the local API workflow is complete and tested.

## 20. Audit logging

Record important actions:

- Plan generation and replanning
- Task completion and rescheduling
- Note AI actions and sharing
- Mind-map generation
- Scan processing and execution
- Answer grounding outcomes
- Speech generation
- Simulated-call creation and state transitions
- Teacher review resolution
- Permission failures for privileged operations

Audit entries must not contain full private note bodies, uploaded images, or secrets.

## 21. Required automated tests

Use `pytest`, FastAPI `TestClient` or an async equivalent, and deterministic fixtures.

### 21.1 General

- OpenAPI includes all new routes.
- Missing authentication is rejected when required.
- Validation errors use the common error schema.
- Pagination limits are enforced.
- Idempotency works.
- Optimistic concurrency rejects stale updates.

### 21.2 Permissions

Test at minimum:

- Aarav reads his own note.
- Aarav cannot read Meera’s note.
- Aarav cannot read Meera’s scan.
- Aarav cannot create a teacher simulated call.
- Mrs. Rao can access Aarav’s assigned-class progress.
- Mrs. Rao cannot access an unassigned student.
- Rajesh reads Aarav’s progress.
- Rajesh cannot modify Aarav’s tasks.
- Rajesh cannot read another child’s progress.
- Speech playback URLs enforce ownership/authorization.

### 21.3 Planner

- Create and retrieve a task.
- Complete a task and verify progress changes.
- Reschedule records history.
- Replan preserves locked and completed tasks.
- Generate produces non-overlapping tasks.
- Insufficient capacity returns a warning.
- Invalid study-session transitions fail.

### 21.4 Notes and mind maps

- Note CRUD and search work.
- Note versions and restore work.
- Unauthorized note links fail.
- Mock note AI action preserves original history.
- Root mind-map deletion fails.
- Child deletion cleans up edges/descendants according to the contract.
- Branch regeneration preserves locked nodes.

### 21.5 Scan

- Valid page upload works.
- Invalid type and oversized upload fail.
- OCR confirmation is required before execution.
- Sample scan returns `9 J` and the correct steps.
- Unsupported input does not return a confident invented answer.
- Save Note is idempotent.
- Schedule Revision creates a real task/revision item.
- Every supported intent returns its appropriate result.

### 21.6 Speech and simulated calls

- Mock speech asset and transcript are created.
- Repeated identical speech request uses cache/idempotency.
- Teacher creates deliveries for authorized recipients.
- Recipient accepts, starts playback, and completes.
- Dismiss creates missed/dismissed history as specified.
- Invalid state transitions fail.
- One recipient cannot mutate another recipient’s delivery.
- Cancel works only in allowed states.
- Quiet hours and deduplication are applied.

## 22. Implementation order

Complete one phase at a time. Do not start later phases while earlier tests fail.

### Phase 1 — Foundation

1. Add configuration, errors, auth context, IDs, timestamps, repositories, and seed data.
2. Add common schemas and dependency injection.
3. Add syllabus endpoints.
4. Add initial tests.
5. Run the backend and verify OpenAPI.

### Phase 2 — Planner and notes

1. Implement tasks, progress, sessions, revision, generate, and replan.
2. Implement notes, search, versions, links, sharing, and mock actions.
3. Add tests.
4. Fix every failure before continuing.

### Phase 3 — Mind maps and scans

1. Implement map CRUD, revisions, generation, and export.
2. Implement private uploads and scan state machine.
3. Implement mock OCR, grounded mock answers, and result actions.
4. Add all required tests.

### Phase 4 — Speech and communication

1. Implement mock speech assets.
2. Implement simulated calls and delivery state machine.
3. Implement messages, quiet hours, and deduplication.
4. Implement teacher and parent endpoints.
5. Add all permission and state tests.

### Phase 5 — Final hardening

1. Add audits and rate limits where required.
2. Check all routes against `spec.md`.
3. Remove debug output and accidental credentials.
4. Verify clean startup with local settings.
5. Run the complete test suite.
6. Verify API documentation and example requests.

## 23. Commands and verification

Use the project’s established environment where available. Otherwise install the existing backend requirements and only necessary new test dependencies.

Run from `Backend/`:

```bash
python -m pytest -q
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verify:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/docs
http://127.0.0.1:8000/api/openapi.json
```

If the existing application uses different documentation paths, use those paths and document them.

Do not claim verification if the server was not actually started or tests were not actually run.

## 24. Example smoke-test sequence

After implementation, verify this sequence with HTTP requests or an automated integration test:

1. Authenticate as `student_aarav` using development headers.
2. Get the active syllabus profile.
3. List Physics chapters and select a valid topic.
4. Create a planner task for that topic.
5. Complete the task.
6. Confirm Today progress changes.
7. Create a note.
8. Update the note and verify version increments.
9. Create a mind map and add a child node linked to the note.
10. Create a scan and upload the sample page.
11. Process the scan and retrieve OCR.
12. Confirm OCR.
13. Execute Solve and verify the answer is `9 J`.
14. Save the result to Notes.
15. Schedule revision.
16. Authenticate as `teacher_rao`.
17. Create a simulated call for Aarav with transcript-only or mock speech.
18. Authenticate as Aarav and list deliveries.
19. Accept the delivery.
20. Mark playback started.
21. Complete playback.
22. Verify Messages shows completed history.
23. Authenticate as `parent_rajesh` and verify Aarav’s read-only progress.
24. Attempt to access Meera’s records and verify denial.

## 25. Code-quality rules

- Use Pydantic models for every request and response.
- Use explicit response models on routers.
- Keep provider adapters behind interfaces.
- Keep all authorization in reusable dependencies/services.
- Do not catch all exceptions and return fake success.
- Do not expose stack traces.
- Do not use bare `except`.
- Do not commit uploaded files, generated audio, credentials, or local databases.
- Do not use global mutable dictionaries that reset unpredictably between dependencies.
- Do not use real external APIs in tests.
- Do not skip or delete failing tests to make the suite pass.
- Do not weaken authorization to simplify development.
- Do not mark incomplete endpoints as completed.

## 26. Final acceptance checklist

The task is complete only when every applicable item is true:

- [ ] All required routers are registered.
- [ ] All endpoints use `/api/v1`.
- [ ] Request and response models are defined.
- [ ] Development auth and real-auth boundaries are clear.
- [ ] Role and relationship permissions are tested.
- [ ] Syllabus context is validated across academic workflows.
- [ ] CRUD operations use shared authoritative state.
- [ ] Pagination, idempotency, and concurrency rules work.
- [ ] Planner generation and replanning are deterministic and tested.
- [ ] Note versions and mind-map revisions work.
- [ ] Upload validation and scan-state transitions work.
- [ ] The sample scan returns the correct `9 J` result.
- [ ] Unsupported questions do not receive invented confident answers.
- [ ] Result actions create actual notes, maps, and revision items.
- [ ] Mock speech assets are clearly labelled and authorized.
- [ ] Simulated-call state transitions and history work.
- [ ] No telephony, microphone, WebRTC, or real calling exists.
- [ ] Teacher and parent permissions work.
- [ ] Audit events avoid unnecessary private content.
- [ ] The application starts locally without external credentials.
- [ ] OpenAPI loads successfully.
- [ ] All required tests pass.
- [ ] Documentation contains correct run and test commands.

## 27. Final response required from the coding agent

When finished, provide:

1. A list of implemented endpoint groups.
2. The files added and materially changed.
3. Exact setup, migration/bootstrap, run, and test commands.
4. Actual test output summary, including number of tests passed.
5. OpenAPI and health-check verification results.
6. Which providers are mocks.
7. Any remaining limitation stated honestly.

Do not respond with only code snippets. Do not stop after creating schemas or routers. Complete the working services, state transitions, authorization, and automated tests.
