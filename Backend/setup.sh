#!/bin/bash

# ============================================================================
# Mentor AI Backend - Setup Script
# ============================================================================
# This script helps you set up the Mentor AI backend quickly
#
# Usage: ./setup.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# Welcome
# ============================================================================

print_header "Mentor AI Backend Setup"
echo "This script will help you set up the Mentor AI backend."
echo "Press Ctrl+C at any time to cancel."
echo ""
read -p "Press Enter to continue..."

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================

print_header "Step 1: Checking Prerequisites"

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 3 found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check pip
if command_exists pip3; then
    print_success "pip3 found"
else
    print_error "pip3 not found. Please install pip3."
    exit 1
fi

# Check git
if command_exists git; then
    print_success "git found"
else
    print_warning "git not found. You may need it for version control."
fi

# ============================================================================
# Step 2: Create Virtual Environment
# ============================================================================

print_header "Step 2: Creating Virtual Environment"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists."
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_success "Virtual environment recreated"
    else
        print_info "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

# ============================================================================
# Step 3: Install Dependencies
# ============================================================================

print_header "Step 3: Installing Dependencies"

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# ============================================================================
# Step 4: Create Directory Structure
# ============================================================================

print_header "Step 4: Creating Directory Structure"

# Create necessary directories
mkdir -p config
mkdir -p logs
mkdir -p data/syllabus
mkdir -p data/embeddings
mkdir -p data/exam_patterns

print_success "Directory structure created"

# ============================================================================
# Step 5: Configure Environment Variables
# ============================================================================

print_header "Step 5: Configuring Environment Variables"

if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Do you want to reconfigure it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping environment configuration"
    else
        CONFIGURE_ENV=true
    fi
else
    CONFIGURE_ENV=true
fi

if [ "$CONFIGURE_ENV" = true ]; then
    cp .env.example .env
    print_success ".env file created from template"
    
    echo ""
    print_info "Please configure the following required variables:"
    echo ""
    
    # Gemini API Key
    echo -e "${YELLOW}1. Gemini API Key${NC}"
    echo "   Get it from: https://makersuite.google.com/app/apikey"
    read -p "   Enter your Gemini API key: " GEMINI_KEY
    if [ ! -z "$GEMINI_KEY" ]; then
        sed -i "s/GOOGLE_API_KEY=.*/GOOGLE_API_KEY=$GEMINI_KEY/" .env
        print_success "Gemini API key configured"
    fi
    
    echo ""
    
    # Firebase Project ID
    echo -e "${YELLOW}2. Firebase Project ID${NC}"
    read -p "   Enter your Firebase project ID: " FIREBASE_PROJECT
    if [ ! -z "$FIREBASE_PROJECT" ]; then
        sed -i "s/FIREBASE_PROJECT_ID=.*/FIREBASE_PROJECT_ID=$FIREBASE_PROJECT/" .env
        sed -i "s/FIREBASE_STORAGE_BUCKET=.*/FIREBASE_STORAGE_BUCKET=$FIREBASE_PROJECT.appspot.com/" .env
        print_success "Firebase project ID configured"
    fi
    
    echo ""
    
    # JWT Secret
    echo -e "${YELLOW}3. JWT Secret Key${NC}"
    echo "   Generating secure JWT secret key..."
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
    print_success "JWT secret key generated and configured"
    
    echo ""
    print_success "Environment variables configured"
    print_warning "Don't forget to add your Firebase credentials file to config/"
fi

# ============================================================================
# Step 6: Verify Syllabus Files
# ============================================================================

print_header "Step 6: Verifying Syllabus Files"

SYLLABUS_COUNT=$(ls -1 data/syllabus/*.json 2>/dev/null | wc -l)

if [ $SYLLABUS_COUNT -gt 0 ]; then
    print_success "Found $SYLLABUS_COUNT syllabus files"
    
    # Validate JSON format
    echo "Validating syllabus files..."
    python3 -c "
import json
import os
import sys

syllabus_dir = 'data/syllabus'
errors = []

for filename in os.listdir(syllabus_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(syllabus_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            chapters = len(data.get('chapters', []))
            print(f'✓ {filename}: {chapters} chapters')
        except Exception as e:
            errors.append(f'{filename}: {e}')
            print(f'✗ {filename}: ERROR')

if errors:
    print('\nErrors found:')
    for error in errors:
        print(f'  - {error}')
    sys.exit(1)
" && print_success "All syllabus files are valid" || print_error "Some syllabus files have errors"
else
    print_warning "No syllabus files found in data/syllabus/"
    print_info "Please add your syllabus JSON files to data/syllabus/"
fi

# ============================================================================
# Step 7: Test Configuration
# ============================================================================

print_header "Step 7: Testing Configuration"

echo "Testing environment configuration..."
python3 -c "
from dotenv import load_dotenv
import os
import sys

load_dotenv()

# Check required variables
required = ['GOOGLE_API_KEY', 'FIREBASE_PROJECT_ID', 'JWT_SECRET_KEY']
missing = []

for var in required:
    value = os.getenv(var)
    if not value or value.startswith('your_'):
        missing.append(var)
    else:
        print(f'✓ {var} is set')

if missing:
    print(f'\n✗ Missing or invalid variables: {', '.join(missing)}')
    sys.exit(1)
else:
    print('\n✓ All required variables are configured')
" && print_success "Configuration test passed" || print_warning "Some configuration issues found"

# ============================================================================
# Step 8: Create Startup Scripts
# ============================================================================

print_header "Step 8: Creating Startup Scripts"

# Development startup script
cat > start-dev.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
uvicorn main:app --reload --port 8000 --log-level info
EOF
chmod +x start-dev.sh
print_success "Created start-dev.sh"

# Production startup script
cat > start-prod.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
EOF
chmod +x start-prod.sh
print_success "Created start-prod.sh"

# ============================================================================
# Setup Complete
# ============================================================================

print_header "Setup Complete!"

echo ""
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Add your Firebase credentials:"
echo "   - Download from Firebase Console"
echo "   - Save as: config/firebase-credentials.json"
echo ""
echo "2. Review and update .env file if needed:"
echo "   nano .env"
echo ""
echo "3. Start the development server:"
echo "   ./start-dev.sh"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "5. View documentation:"
echo "   - API Docs: http://localhost:8000/api/docs"
echo "   - Configuration: cat CONFIGURATION_GUIDE.md"
echo "   - Optimization: cat OPTIMIZATION_GUIDE.md"
echo ""
echo -e "${BLUE}For more information, see CONFIGURATION_GUIDE.md${NC}"
echo ""
