#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")"
exec ./venv/bin/python3 -m uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000 --log-level info
