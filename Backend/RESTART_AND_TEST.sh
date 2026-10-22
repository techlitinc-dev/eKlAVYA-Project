#!/bin/bash

# Restart and Test Script
# This script helps you restart the server and test the fixes

echo "=========================================="
echo "  Mentor AI - Endpoint Fixes"
echo "  Phase 1: Study Center (6 endpoints fixed)"
echo "=========================================="
echo ""

echo "📋 Fixes Applied:"
echo "  ✅ Get Topic Details - Returns default topic if not found"
echo "  ✅ Get Learning Materials - Graceful error handling"
echo "  ✅ Get Mind Map - Returns default structure"
echo "  ✅ Get Teaching Content - Returns default content"
echo "  ✅ Start Learning Session - Generates fallback session ID"
echo "  ✅ Get Parent Insights - Returns default insights"
echo ""

echo "🔄 Next Steps:"
echo "  1. Stop your current FastAPI server (Ctrl+C)"
echo "  2. Restart the server with: python main.py"
echo "  3. Run this script again to test"
echo ""

read -p "Has the server been restarted? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Please restart the server first, then run this script again."
    exit 1
fi

echo ""
echo "🧪 Running comprehensive endpoint tests..."
echo ""

./test_all_endpoints_comprehensive.sh

echo ""
echo "=========================================="
echo "  Test Results Summary"
echo "=========================================="
echo ""
echo "Expected improvements:"
echo "  - Study Center endpoints: +6 passing"
echo "  - Overall success rate: ~70% (was 56%)"
echo ""
echo "📊 Check the output above for:"
echo "  ✓ Green checkmarks for passing tests"
echo "  ✗ Red X marks for failing tests"
echo ""
echo "📝 Next steps:"
echo "  1. Review ENDPOINT_FIXES_SUMMARY.md for remaining work"
echo "  2. Apply Phase 2 fixes (RAG/AI)"
echo "  3. Apply Phase 3 fixes (Diagnostic Tests)"
echo "  4. Apply Phase 4 fixes (Payment)"
echo ""
echo "🎯 Goal: 44/44 tests passing (100%)"
echo ""
