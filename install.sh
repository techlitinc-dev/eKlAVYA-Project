#!/usr/bin/env bash
# ============================================================================
# eKlAVYA (Mentor AI) — Unified Installation Script
# ============================================================================
# Installs and configures:
#   1. Backend (FastAPI + Python Virtual Environment + Dependencies + .env)
#   2. Frontend Website & SuperAdmin Portal (React 19 + TypeScript + Vite + Tailwind)
#
# Usage:
#   ./install.sh
# ============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/Backend"
FRONTEND_DIR="$ROOT_DIR/Frontend_Website"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${BLUE}ℹ $1${NC}"; }

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# 1. Check System Prerequisites
# ============================================================================
print_header "Step 1: Checking System Prerequisites"

if command_exists python3; then
    PYTHON_VER=$(python3 --version 2>&1)
    print_success "Found $PYTHON_VER"
else
    print_error "python3 is not installed. Please install Python 3.9+ and try again."
    exit 1
fi

if command_exists node; then
    NODE_VER=$(node --version 2>&1)
    print_success "Found Node.js $NODE_VER"
else
    print_error "node is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

if command_exists npm; then
    NPM_VER=$(npm --version 2>&1)
    print_success "Found npm v$NPM_VER"
else
    print_error "npm is not installed. Please install npm and try again."
    exit 1
fi

# ============================================================================
# 2. Backend Setup (FastAPI + Python venv)
# ============================================================================
print_header "Step 2: Setting Up Backend (FastAPI)"

cd "$BACKEND_DIR"

# Create required runtime directories
mkdir -p config logs data/syllabus data/embeddings data/exam_patterns
print_success "Verified Backend directory structure (config, logs, data/*)"

# Create or repair Python virtual environment
if [ ! -d "venv" ] || [ ! -x "venv/bin/python3" ]; then
    print_info "Creating Python virtual environment in Backend/venv..."
    rm -rf venv
    python3 -m venv venv
    print_success "Created Python virtual environment"
else
    # Ensure venv paths match current directory in case the folder was moved
    VENV_REAL_PATH="$BACKEND_DIR/venv"
    if grep -q "/mentorai/MENTOR-AI-onlyapi/venv" venv/bin/activate 2>/dev/null; then
        print_info "Updating relocated virtual environment paths in Backend/venv..."
        for f in venv/bin/*; do
            if [ -f "$f" ] && [ ! -L "$f" ] && file "$f" | grep -q "text"; then
                sed -i "s|/home/[^/]*/Projects/eKlAVYA/mentorai/MENTOR-AI-onlyapi/venv|$VENV_REAL_PATH|g" "$f" || true
            fi
        done
        print_success "Repaired virtual environment script paths"
    fi
    print_success "Using existing Python virtual environment in Backend/venv"
fi

# Install Python packages
print_info "Installing Python dependencies from Backend/requirements.txt..."
"$BACKEND_DIR/venv/bin/python3" -m pip install --upgrade pip --quiet
"$BACKEND_DIR/venv/bin/python3" -m pip install -r requirements.txt --quiet
print_success "Backend Python dependencies installed"

# Ensure .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created Backend/.env from .env.example"
        print_warning "Update Backend/.env with your GOOGLE_API_KEY and Firebase credentials as needed."
    else
        print_warning "No .env or .env.example found in Backend/"
    fi
else
    print_success "Backend/.env file already present"
fi

# Fix Backend helper scripts to use local venv python reliably
cat > "$BACKEND_DIR/start-dev.sh" << 'EOF'
#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")"
exec ./venv/bin/python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
EOF
chmod +x "$BACKEND_DIR/start-dev.sh"

cat > "$BACKEND_DIR/start-prod.sh" << 'EOF'
#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")"
exec ./venv/bin/python3 -m uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000 --log-level info
EOF
chmod +x "$BACKEND_DIR/start-prod.sh"

# ============================================================================
# 3. Frontend Website & SuperAdmin Setup (React 19 + Vite)
# ============================================================================
print_header "Step 3: Setting Up Frontend Website & SuperAdmin Portal"

cd "$FRONTEND_DIR"

print_info "Installing Node.js dependencies in Frontend_Website..."
npm install --no-audit --no-fund
print_success "Frontend Website dependencies installed"

# Ensure run.sh is executable if present
if [ -f "$ROOT_DIR/run.sh" ]; then
    chmod +x "$ROOT_DIR/run.sh"
fi

# ============================================================================
# 4. Complete
# ============================================================================
print_header "Installation Complete!"
echo -e "${GREEN}All eKlAVYA (Mentor AI) components are installed and ready.${NC}\n"
echo -e "To start both Backend & Frontend servers, run:"
echo -e "  ${BOLD}${CYAN}./run.sh${NC}\n"
echo -e "Individual modes supported by ${BOLD}./run.sh${NC}:"
echo -e "  ${CYAN}./run.sh${NC}           — Start full stack (Backend on :8000 + Frontend on :3000)"
echo -e "  ${CYAN}./run.sh backend${NC}   — Start only FastAPI Backend (:8000)"
echo -e "  ${CYAN}./run.sh frontend${NC}  — Start only React Frontend & SuperAdmin (:3000)"
echo -e "  ${CYAN}./run.sh stop${NC}      — Stop any running eKlAVYA servers\n"
