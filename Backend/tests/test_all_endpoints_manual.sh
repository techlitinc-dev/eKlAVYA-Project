#!/bin/bash

# Comprehensive API Endpoint Testing Script
# Tests all endpoints from the API Testing Guide

BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)
TEST_EMAIL="testparent_${TIMESTAMP}@example.com"
TEST_PASSWORD="SecurePass123"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print test result
print_result() {
    local test_name="$1"
    local status="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local headers="$5"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -X GET "$BASE_URL$endpoint" $headers)
    else
        response=$(curl -s -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            $headers \
            -d "$data")
    fi
    
    # Check if response contains error
    if echo "$response" | grep -q '"detail"'; then
        print_result "$name" "FAIL"
        echo "  Error: $(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Unknown error'))" 2>/dev/null)"
        return 1
    else
        print_result "$name" "PASS"
        return 0
    fi
}

echo "=========================================="
echo "  Mentor AI Platform - API Testing"
echo "=========================================="
echo ""

# ==================== HEALTH CHECK ====================
echo "=== Health Check ==="
test_endpoint "Health Check" "GET" "/health" "" ""
echo ""

# ==================== AUTHENTICATION ====================
echo "=== Authentication ===="

# 1. Simple Registration
echo "Testing Simple Registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register/simple" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Parent\",
    \"email_address\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"repeat_password\": \"$TEST_PASSWORD\",
    \"mobile_number\": \"+919876543210\"
  }")

if echo "$REGISTER_RESPONSE" | grep -q '"parent_id"'; then
    print_result "Simple Registration" "PASS"
    PARENT_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('parent_id', ''))" 2>/dev/null)
    echo "  Parent ID: $PARENT_ID"
else
    print_result "Simple Registration" "FAIL"
    echo "  Error: $REGISTER_RESPONSE"
fi

# 2. Parent Login
echo "Testing Parent Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login/email" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

if echo "$LOGIN_RESPONSE" | grep -q '"token"'; then
    print_result "Parent Login" "PASS"
    PARENT_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)
    echo "  Token obtained"
else
    print_result "Parent Login" "FAIL"
    echo "  Error: $LOGIN_RESPONSE"
fi

# 3. Get Current User
echo "Testing Get Current User..."
USER_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $PARENT_TOKEN")

if echo "$USER_RESPONSE" | grep -q '"parent_id"'; then
    print_result "Get Current User" "PASS"
else
    print_result "Get Current User" "FAIL"
fi

echo ""

# ==================== ONBOARDING ====================
echo "=== Onboarding Flow ==="

# 1. Set Preferences
echo "Testing Set Preferences..."
PREF_RESPONSE=$(curl -s -X POST "$BASE_URL/api/onboarding/preferences?parent_id=$PARENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium"
  }')

if echo "$PREF_RESPONSE" | grep -q '"parent_id"'; then
    print_result "Set Preferences" "PASS"
else
    print_result "Set Preferences" "FAIL"
fi

# 2. Create Child Profile
echo "Testing Create Child Profile..."
CHILD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/onboarding/child?parent_id=$PARENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Child",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "testchild'$TIMESTAMP'",
    "password": "ChildPass123"
  }')

if echo "$CHILD_RESPONSE" | grep -q '"child_id"'; then
    print_result "Create Child Profile" "PASS"
    CHILD_ID=$(echo "$CHILD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('child_id', ''))" 2>/dev/null)
    echo "  Child ID: $CHILD_ID"
else
    print_result "Create Child Profile" "FAIL"
fi

# 3. Get Available Exams
echo "Testing Get Available Exams..."
EXAMS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/onboarding/exams/available")

if echo "$EXAMS_RESPONSE" | grep -q '"exams"'; then
    print_result "Get Available Exams" "PASS"
else
    print_result "Get Available Exams" "FAIL"
fi

# 4. Select Exam
echo "Testing Select Exam..."
FUTURE_DATE=$(date -d "+90 days" +%Y-%m-%dT00:00:00Z 2>/dev/null || date -v+90d +%Y-%m-%dT00:00:00Z)
EXAM_RESPONSE=$(curl -s -X POST "$BASE_URL/api/onboarding/exam/select?parent_id=$PARENT_ID&child_id=$CHILD_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"exam_type\": \"JEE_MAIN\",
    \"exam_date\": \"$FUTURE_DATE\",
    \"subject_preferences\": {
      \"Physics\": 40,
      \"Chemistry\": 30,
      \"Mathematics\": 30
    }
  }")

if echo "$EXAM_RESPONSE" | grep -q '"diagnostic_test_id"'; then
    print_result "Select Exam" "PASS"
    TEST_ID=$(echo "$EXAM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('diagnostic_test_id', ''))" 2>/dev/null)
    echo "  Test ID: $TEST_ID"
else
    print_result "Select Exam" "FAIL"
fi

# 5. Check Onboarding Status
echo "Testing Onboarding Status..."
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/onboarding/status?parent_id=$PARENT_ID")

if echo "$STATUS_RESPONSE" | grep -q '"onboarding_complete"'; then
    print_result "Onboarding Status" "PASS"
else
    print_result "Onboarding Status" "FAIL"
fi

echo ""

# ==================== PAYMENT ====================
echo "=== Payment & Subscriptions ==="

# 1. Get Plans
echo "Testing Get Subscription Plans..."
PLANS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/payment/plans")

if echo "$PLANS_RESPONSE" | grep -q '"plan_id"'; then
    print_result "Get Subscription Plans" "PASS"
else
    print_result "Get Subscription Plans" "FAIL"
fi

# 2. Get Subscription Status
echo "Testing Get Subscription Status..."
SUB_RESPONSE=$(curl -s -X GET "$BASE_URL/api/payment/subscription/$PARENT_ID" \
  -H "Authorization: Bearer $PARENT_TOKEN")

if echo "$SUB_RESPONSE" | grep -q '"is_active"'; then
    print_result "Get Subscription Status" "PASS"
else
    print_result "Get Subscription Status" "FAIL"
fi

echo ""

# ==================== SUMMARY ====================
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check the output above.${NC}"
    exit 1
fi
