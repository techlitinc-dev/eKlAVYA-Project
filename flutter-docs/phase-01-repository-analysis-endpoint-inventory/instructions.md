# Phase 01 — Instructions

These steps reproduce and verify the repository analysis. Execute them in order. No application
code is written in this phase.

## 1. Obtain the repository at the inspected commit

```bash
git clone https://github.com/techlitinc-dev/eKlAVYA-Project.git
cd eKlAVYA-Project
git checkout d8ab4917480c90a7c5c663f7fe6e8a726ce490f4
git log -1 --format='%H %ci %s'
```

Expected: the hash line matches `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`.
If `main` has moved on, still check out this exact commit — all citations in this documentation
set refer to it.

## 2. Confirm the directory structure

```bash
ls Android_App Super_Admin Frontend_Website Backend
```

Expected:
- `Android_App/` contains only `.gitkeep` before Phase 02. The Flutter scaffold is created there;
  no Kotlin/Android-native implementation is introduced.
- `Super_Admin/` contains only `README.md` and `.gitkeep`.
- `Frontend_Website/` is a Vite + React + TypeScript app.
- `Backend/` is the FastAPI backend (`main.py`, `routers/`, `services/`, `models/`, …).

## 3. Install and start the backend

```bash
./install.sh        # creates Backend/venv, installs requirements, copies .env.example -> .env
./run.sh backend    # starts uvicorn on http://localhost:8000
```

Then verify:

```bash
curl -s http://localhost:8000/health
```

Expected: a JSON health body (the app factory registers `GET /health` in `Backend/main.py:212`).

## 4. Dump the live OpenAPI spec and cross-check the inventory

```bash
curl -s http://localhost:8000/api/openapi.json > /tmp/openapi.json
python3 - <<'EOF'
import json
spec = json.load(open('/tmp/openapi.json'))
paths = spec['paths']
print(f"total paths: {len(paths)}")
for p in sorted(paths):
    if p.startswith('/api/v1'):
        continue
    print(p, sorted(paths[p].keys()))
EOF
```

Compare the printed paths against the inventory in `text.md` §9. They must match:

- `Backend/routers/question_router.py` defines 6 endpoints under `/api/questions` that are
  **absent** from the live spec — the router is defined but never mounted in `main.py`.
  This is expected and documented (inventory row: consumer = `unused`, reason given).
- `Backend/routers/diagnostic_test_router.py` and `Backend/routers/test_management_router.py`
  both mount at `/api/diagnostic-test` and both register `/{test_id}/start|submit|results|status`.
  The diagnostic router is included first (`main.py:296`), so its (mock) handlers win. The live
  spec shows a single handler per path — the diagnostic one. This shadowing is documented.

## 5. Verify the seed identities used throughout the docs

```bash
grep -n "parent_demo_eklavya\|child_demo_aarav\|superadmin_root" Backend/routers/superadmin_router.py
grep -n "student_aarav\|teacher_rao\|parent_rajesh" Backend/seed.py
```

Expected: hits in both files. These identities are used for manual testing in later phases.

## 6. Sign-off

Check off every item in `expected-output.md`. Any mismatch between this documentation and the
running backend is a documentation bug: fix the doc (never the backend) and record the fix in the
phase gap log, unless the mismatch is a genuine backend defect — in that case add it to the
`BACKEND CHANGE REQUIRED` list in `text.md` §11 of this phase.
