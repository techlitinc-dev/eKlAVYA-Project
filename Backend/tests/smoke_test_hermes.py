#!/usr/bin/env python3
"""
Hermes End-to-End Smoke Test

Live test against a running server: creates (or reuses) a test parent +
student, then exercises the full Hermes flow with REAL Gemini calls:

  seed-topics -> chat -> quiz attempt -> progress -> summary generate ->
  summary read (student + parent) -> parent chat denied (403)

Usage:
  BASE_URL=http://localhost:8001 venv/bin/python tests/smoke_test_hermes.py

Requires: server running with valid Firebase creds + GOOGLE_API_KEY.
Costs: ~2 small gemini-2.5-flash-lite calls (< $0.001).
"""

import os
import sys
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API = f"{BASE_URL}/api"

PARENT = {
    "name": "Hermes Test Parent",
    "mobile_number": "9876543210",
    "email_address": "hermestest@example.com",
    "password": "HermesTest123!",
    "repeat_password": "HermesTest123!",
}
STUDENT = {
    "name": "Hermes Test Student",
    "age": 17,
    "grade": 12,
    "current_level": "intermediate",
    "username": "hermes_test_student",
    "password": "HermesTest123!",
}

results = []


def check(name: str, ok: bool, detail: str = ""):
    results.append((name, ok, detail))
    mark = "✅" if ok else "❌"
    print(f"{mark} {name}" + (f" — {detail[:180]}" if detail else ""))


def main() -> int:
    # ── Auth setup ────────────────────────────────────────────────
    r = requests.post(f"{API}/auth/register/simple", json=PARENT)
    if r.status_code not in (200, 201):
        detail = r.text[:200]
        if "already exists" not in detail.lower():
            check("register parent", False, detail)
            return 1
        print("ℹ️  parent already exists, logging in")

    r = requests.post(
        f"{API}/auth/login/email",
        json={"email": PARENT["email_address"], "password": PARENT["password"]},
    )
    if r.status_code != 200:
        check("parent login", False, r.text[:200])
        return 1
    parent_token = r.json().get("token") or r.json().get("access_token")
    parent_id = r.json().get("parent_id")
    parent_headers = {"Authorization": f"Bearer {parent_token}"}
    check("parent login", bool(parent_token), f"parent_id={parent_id}")

    r = requests.post(
        f"{API}/onboarding/child",
        json=STUDENT,
        params={"parent_id": parent_id},
        headers=parent_headers,
    )
    if r.status_code in (200, 201):
        child_id = r.json().get("child_id")
    else:
        # Child already exists (one-child policy) or other error — try reuse
        r2 = requests.get(
            f"{API}/onboarding/child",
            params={"parent_id": parent_id},
            headers=parent_headers,
        )
        if r2.status_code == 200 and r2.json().get("child_id"):
            child_id = r2.json().get("child_id")
            print("ℹ️  reusing existing child profile")
        else:
            check("create child", False, r.text[:200])
            return 1
    check("child profile", bool(child_id), f"child_id={child_id}")

    r = requests.post(
        f"{API}/auth/login/child",
        json={"username": STUDENT["username"], "password": STUDENT["password"]},
    )
    child_token = None
    if r.status_code == 200:
        body = r.json()
        child_token = body.get("token") or body.get("access_token")
        if not child_token and body.get("tokens"):
            child_token = body["tokens"].get("access_token")
    check("student login", bool(child_token))
    if not child_token:
        return 1
    child_headers = {"Authorization": f"Bearer {child_token}"}

    # ── Hermes flow ───────────────────────────────────────────────
    r = requests.post(f"{API}/hermes/admin/seed-topics", headers=parent_headers)
    check(
        "seed micro-topics",
        r.status_code == 200,
        f"{r.json() if r.status_code == 200 else r.text[:200]}",
    )
    if r.status_code == 200 and not r.json().get("already_seeded"):
        print(f"   seeded {r.json().get('micro_topics_count')} topics, exams={r.json().get('exams')}")

    r = requests.get(f"{API}/hermes/topics", headers=child_headers)
    topics = r.json() if r.status_code == 200 else []
    check("list in-scope topics", r.status_code == 200 and len(topics) > 0, f"{len(topics)} topics")
    topic_id = topics[0]["micro_topic_id"] if topics else None

    r = requests.post(
        f"{API}/hermes/chat",
        json={
            "message": "A projectile is launched at 20 m/s at 45 degrees. How do I find its range?",
            "micro_topic_id": topic_id,
        },
        headers=child_headers,
    )
    chat_ok = r.status_code == 200
    check("mentor chat (real Gemini)", chat_ok, f"{r.text[:200]}")
    if chat_ok:
        body = r.json()
        print(f"   language={body.get('language')} tokens≈{body.get('tokens_used')} mock={body.get('mock')}")
        print(f"   answer: {body.get('answer', '')[:220]}...")

    r = requests.post(
        f"{API}/hermes/quiz/attempt",
        json={"micro_topic_id": topic_id, "score_pct": 80, "total_questions": 10},
        headers=child_headers,
    )
    quiz_ok = r.status_code == 200 and r.json().get("passed") is True
    check("quiz attempt -> LEARNING", quiz_ok, f"{r.text[:200]}")

    r = requests.get(f"{API}/hermes/progress", headers=child_headers)
    prog_ok = r.status_code == 200 and r.json().get("total_in_scope", 0) > 0
    check("progress report", prog_ok, f"{r.text[:200]}")

    r = requests.post(
        f"{API}/hermes/summary/generate/{child_id}",
        headers=parent_headers,
    )
    check("generate daily summary", r.status_code == 200, f"quiet_day={r.json().get('quiet_day') if r.status_code == 200 else r.text[:200]}")

    for audience in ("student", "parent"):
        r = requests.get(
            f"{API}/hermes/summary/{child_id}",
            params={"audience": audience},
            headers=parent_headers,
        )
        ok = r.status_code == 200 and len(r.json().get("text", "")) > 0
        check(f"read summary ({audience})", ok, f"{r.json().get('text', '')[:150]}")
        if ok:
            print(f"   language={r.json().get('language')} mock={r.json().get('mock')}")

    r = requests.post(
        f"{API}/hermes/chat",
        json={"message": "hello"},
        params={"child_id": child_id},
        headers=parent_headers,
    )
    check("parent chat denied (403)", r.status_code == 403, f"status={r.status_code}")

    # ── Summary ───────────────────────────────────────────────────
    failed = [n for n, ok, _ in results if not ok]
    print("\n" + "=" * 60)
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    print("Hermes smoke test: ALL GREEN")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.ConnectionError:
        print(f"\n❌ Cannot reach server at {BASE_URL}. Start it with:\n"
              f"   venv/bin/python -m uvicorn main:app --port <port>")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
