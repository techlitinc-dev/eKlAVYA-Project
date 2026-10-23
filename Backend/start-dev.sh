#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")"
exec ./venv/bin/python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
