#!/bin/bash

# ============================================================================
# Fix Gemini API - Install Correct Package
# ============================================================================

echo "🔧 Fixing Gemini API setup..."
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Install correct package
echo "📦 Installing google-generativeai package..."
pip install google-generativeai==0.3.2

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ google-generativeai installed successfully!"
    echo ""
    echo "Now you can start the server:"
    echo "  ./start-dev.sh"
    echo ""
else
    echo ""
    echo "❌ Installation failed. Please try manually:"
    echo "  source venv/bin/activate"
    echo "  pip install google-generativeai"
    echo ""
    exit 1
fi
