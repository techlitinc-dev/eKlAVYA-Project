#!/usr/bin/env bash
# ============================================================================
# eKlAVYA (Mentor AI) — Unified Run Script
# ============================================================================
# Launches:
#   - FastAPI Backend API Server       (http://localhost:8000)
#   - React Frontend & SuperAdmin Web  (http://localhost:3000)
#
# Usage:
#   ./run.sh            Start full stack (Backend + Frontend)
#   ./run.sh backend    Start only FastAPI Backend (:8000)
#   ./run.sh frontend   Start only React Frontend (:3000)
#   ./run.sh stop       Stop any running eKlAVYA servers on ports 8000 / 3000
# ============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/Backend"
FRONTEND_DIR="$ROOT_DIR/Frontend_Website"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

BACKEND_PID=""
FRONTEND_PID=""

print_banner() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BOLD}${CYAN}  eKlAVYA (Mentor AI) — Platform Runner${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

kill_port() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        local pids
        pids=$(lsof -t -i:"$port" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            kill -9 $pids >/dev/null 2>&1 || true
        fi
    fi
    if command -v fuser >/dev/null 2>&1; then
        fuser -k "${port}/tcp" >/dev/null 2>&1 || true
    fi
}

cleanup() {
    echo -e "\n${YELLOW}Shutting down eKlAVYA servers...${NC}"
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Servers stopped.${NC}"
}

MODE="${1:-all}"

case "$MODE" in
    stop)
        print_banner
        echo -e "${YELLOW}Stopping processes on ports ${BACKEND_PORT} and ${FRONTEND_PORT}...${NC}"
        kill_port "$BACKEND_PORT"
        kill_port "$FRONTEND_PORT"
        echo -e "${GREEN}✓ Stopped running eKlAVYA services.${NC}"
        exit 0
        ;;
    -h|--help|help)
        print_banner
        echo "Usage: ./run.sh [all|backend|frontend|stop]"
        echo ""
        echo "  all (default)  Start both FastAPI Backend (:8000) and React Frontend (:3000)"
        echo "  backend        Start only FastAPI Backend (:8000)"
        echo "  frontend       Start only React Frontend & SuperAdmin (:3000)"
        echo "  stop           Stop any processes listening on ports 8000 and 3000"
        exit 0
        ;;
esac

print_banner

# Ensure installation has been run if dependencies are missing
if [ ! -x "$BACKEND_DIR/venv/bin/python3" ] || [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}⚠ Missing dependencies detected. Running ./install.sh first...${NC}"
    "$ROOT_DIR/install.sh"
fi

if [ "$MODE" = "backend" ]; then
    kill_port "$BACKEND_PORT"
    echo -e "${CYAN}Starting FastAPI Backend on http://localhost:${BACKEND_PORT} ...${NC}"
    cd "$BACKEND_DIR"
    exec ./venv/bin/python3 -m uvicorn main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" --log-level info
fi

if [ "$MODE" = "frontend" ]; then
    kill_port "$FRONTEND_PORT"
    echo -e "${CYAN}Starting React Frontend & SuperAdmin on http://localhost:${FRONTEND_PORT} ...${NC}"
    cd "$FRONTEND_DIR"
    exec npm run dev -- --port "$FRONTEND_PORT" --host 0.0.0.0
fi

# Default: Start both Backend and Frontend concurrently
trap cleanup SIGINT SIGTERM EXIT

kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

mkdir -p "$BACKEND_DIR/logs"

echo -e "${BLUE}1. Starting FastAPI Backend on port ${BACKEND_PORT}...${NC}"
(
    cd "$BACKEND_DIR"
    exec ./venv/bin/python3 -m uvicorn main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" --log-level info
) &
BACKEND_PID=$!

# Wait for backend health endpoint to respond
echo -ne "${BLUE}   Waiting for Backend API to become ready${NC}"
for _ in $(seq 1 25); do
    if curl -fsS "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
        echo -e " ${GREEN}✓ Ready!${NC}"
        break
    fi
    echo -n "."
    sleep 0.5
done
echo ""

echo -e "${BLUE}2. Starting React Frontend & SuperAdmin Portal on port ${FRONTEND_PORT}...${NC}"
(
    cd "$FRONTEND_DIR"
    exec npm run dev -- --port "$FRONTEND_PORT" --host 0.0.0.0
) &
FRONTEND_PID=$!

sleep 1.5

echo -e "\n${GREEN}============================================================================${NC}"
echo -e "${BOLD}${GREEN}  ✓ eKlAVYA (Mentor AI) Full Stack is Running!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo -e "  ${BOLD}🌐 Public Landing & Demo Switcher:${NC}  http://localhost:${FRONTEND_PORT}"
echo -e "  ${BOLD}🎓 Student Portal:${NC}                  http://localhost:${FRONTEND_PORT}/student/dashboard"
echo -e "  ${BOLD}👪 Parent / Teacher Portal:${NC}         http://localhost:${FRONTEND_PORT}/parent/dashboard"
echo -e "  ${BOLD}🛡️  SuperAdmin Governance Portal:${NC}   http://localhost:${FRONTEND_PORT}/superadmin/dashboard"
echo -e "  ${BOLD}⚡ FastAPI Backend & Swagger Docs:${NC}  http://localhost:${BACKEND_PORT}/api/docs"
echo -e "  ${BOLD}❤️  Backend Health Check:${NC}           http://localhost:${BACKEND_PORT}/health"
echo -e "${GREEN}============================================================================${NC}"
echo -e "${YELLOW}Press Ctrl+C at any time to stop both servers.${NC}\n"

wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || wait
