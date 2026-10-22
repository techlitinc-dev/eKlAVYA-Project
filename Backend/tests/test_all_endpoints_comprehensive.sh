#!/bin/bash

# Comprehensive API Endpoint Testing Script - ALL ENDPOINTS
# Tests all endpoints including AI-powered features

BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)
TEST_EMAIL="testparent_${TIMESTAMP}@example.com"
TEST_PASSWORD="SecurePass123"
TEST_CHILD_USERNAME="testchild${TIMESTAMP}"
TEST_CHILD_PASSWORD="ChildPass123"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print test result
print_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        [ -n "$details" ] && echo -e "  ${BLUE}$details${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        [ -n "$details" ] && echo -e "  ${RED}$details${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo "=========================================="
echo "  Mentor AI Platform - Comprehensive API Testing"
echo "  Testing ALL Endpoints Including AI Features"
echo "=========================================="
echo ""

# ==================== HEALTH CHECK ====================
echo "=== 1. Health & System ==="
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
if echo "$HEALTH_RESPONSE" | grep -q '"status".*"healthy"'; then
    print_result "Health Check" "PASS"
else
    print_result "Health Check" "FAIL" "$HEALTH_RESPONSE"
fi

ROOT_RESPONSE=$(curl -s "$BASE_URL/")
if echo "$ROOT_RESPONSE" | grep -q '"name"'; then
    print_result "Root Endpoint" "PASS"
else
    print_result "Root Endpoint" "FAIL"
fi
echo ""

# ==================== AUTHENTICATION ====================
echo "=== 2. Authentication (8 endpoints) ==="

# 2.1 Simple Registration
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
else
    print_result "Simple Registration" "FAIL" "$REGISTER_RESPONSE"
fi

# 2.2 Parent Login
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login/email" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

if echo "$LOGIN_RESPONSE" | grep -q '"token"'; then
    print_result "Parent Email Login" "PASS"
    PARENT_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)
    REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('refresh_token', ''))" 2>/dev/null)
else
    print_result "Parent Email Login" "FAIL"
fi

# 2.3 Get Current User
USER_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $PARENT_TOKEN")

if echo "$USER_RESPONSE" | grep -q '"parent_id"'; then
    print_result "Get Current User" "PASS"
else
    print_result "Get Current User" "FAIL"
fi

# 2.4 Token Refresh
REFRESH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/token/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

if echo "$REFRESH_RESPONSE" | grep -q '"token"'; then
    print_result "Token Refresh" "PASS"
else
    print_result "Token Refresh" "FAIL" "$(echo $REFRESH_RESPONSE | head -c 100)"
fi

echo ""

# ==================== ONBOARDING ====================
echo "=== 3. Onboarding (8 endpoints) ==="

# 3.1 Set Preferences
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

# 3.2 Get Preferences
GET_PREF_RESPONSE=$(curl -s -X GET "$BASE_URL/api/onboarding/preferences?parent_id=$PARENT_ID")

if echo "$GET_PREF_RESPONSE" | grep -q '"language"'; then
    print_result "Get Preferences" "PASS"
else
    print_result "Get Preferences" "FAIL"
fi

# 3.3 Create Child Profile
CHILD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/onboarding/child?parent_id=$PARENT_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Child\",
    \"age\": 16,
    \"grade\": 11,
    \"current_level\": \"intermediate\",
    \"username\": \"$TEST_CHILD_USERNAME\",
    \"password\": \"$TEST_CHILD_PASSWORD\"
  }")

if echo "$CHILD_RESPONSE" | grep -q '"child_id"'; then
    print_result "Create Child Profile" "PASS"
    CHILD_ID=$(echo "$CHILD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('child_id', ''))" 2>/dev/null)
else
    print_result "Create Child Profile" "FAIL"
fi

# 3.4 Get Child Profile
GET_CHILD_RESPONSE=$(curl -s -X GET "$BASE_URL/api/onboarding/child?parent_id=$PARENT_ID")

if echo "$GET_CHILD_RESPONSE" | grep -q '"child_id"'; then
    print_result "Get Child Profile" "PASS"
else
    print_result "Get Child Profile" "FAIL"
fi

# 3.5 Get Available Exams
EXAMS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/onboarding/exams/available")

if echo "$EXAMS_RESPONSE" | grep -q '"exams"'; then
    print_result "Get Available Exams" "PASS"
else
    print_result "Get Available Exams" "FAIL"
fi

# 3.6 Select Exam
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
else
    print_result "Select Exam" "FAIL"
fi

# 3.7 Get Exam Preferences
GET_EXAM_RESPONSE=$(curl -s -X GET "$BASE_URL/api/onboarding/exam/preferences?child_id=$CHILD_ID")

if echo "$GET_EXAM_RESPONSE" | grep -q '"exam_type"'; then
    print_result "Get Exam Preferences" "PASS"
else
    print_result "Get Exam Preferences" "FAIL"
fi

# 3.8 Check Onboarding Status
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/onboarding/status?parent_id=$PARENT_ID")

if echo "$STATUS_RESPONSE" | grep -q '"onboarding_complete"'; then
    print_result "Onboarding Status" "PASS"
    IS_COMPLETE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('onboarding_complete', False))" 2>/dev/null)
    [ "$IS_COMPLETE" = "True" ] && echo -e "  ${BLUE}Onboarding Complete!${NC}"
else
    print_result "Onboarding Status" "FAIL"
fi

echo ""

# ==================== CHILD LOGIN ====================
echo "=== 4. Child Authentication ==="

CHILD_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login/child" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$TEST_CHILD_USERNAME\",
    \"password\": \"$TEST_CHILD_PASSWORD\"
  }")

if echo "$CHILD_LOGIN_RESPONSE" | grep -q '"token"'; then
    print_result "Child Login" "PASS"
    CHILD_TOKEN=$(echo "$CHILD_LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)
    STUDENT_ID=$(echo "$CHILD_LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('student_id', ''))" 2>/dev/null)
else
    print_result "Child Login" "FAIL"
fi

echo ""

# ==================== STUDY CENTER ====================
echo "=== 5. Study Center (11 endpoints) ==="

# 5.1 Get Topics
TOPICS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/topics?student_id=$STUDENT_ID&subject=Physics" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$TOPICS_RESPONSE" | grep -q '"topics"'; then
    print_result "Get Topics" "PASS"
    TOPIC_COUNT=$(echo "$TOPICS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', {}).get('topics', [])))" 2>/dev/null)
    echo -e "  ${BLUE}Found $TOPIC_COUNT topics${NC}"
else
    print_result "Get Topics" "FAIL"
fi

# 5.2 Get Topic Details
TOPIC_DETAIL_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/topics/T01" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$TOPIC_DETAIL_RESPONSE" | grep -q '"topic"'; then
    print_result "Get Topic Details" "PASS"
else
    print_result "Get Topic Details" "FAIL"
fi

# 5.3 Get Learning Materials (AI-powered)
echo -e "${YELLOW}Testing AI-powered endpoint...${NC}"
MATERIALS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/materials/T01" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$MATERIALS_RESPONSE" | grep -q '"topic_id"'; then
    print_result "Get Learning Materials (AI)" "PASS" "AI content generated successfully"
else
    print_result "Get Learning Materials (AI)" "FAIL" "$(echo $MATERIALS_RESPONSE | head -c 150)"
fi

# 5.4 Get Mind Map
MINDMAP_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/mindmap/T01" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$MINDMAP_RESPONSE" | grep -q '"mindmap_id"'; then
    print_result "Get Mind Map" "PASS"
else
    print_result "Get Mind Map" "FAIL"
fi

# 5.5 Get Teaching Content
TEACH_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/teach/T01" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$TEACH_RESPONSE" | grep -q '"teaching_id"'; then
    print_result "Get Teaching Content" "PASS"
else
    print_result "Get Teaching Content" "FAIL"
fi

# 5.6 Start Learning Session
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/study-center/progress/start" \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"student_id\": \"$STUDENT_ID\",
    \"topic_id\": \"T01\",
    \"topic_name\": \"Kinematics\",
    \"subject\": \"Physics\"
  }")

if echo "$SESSION_RESPONSE" | grep -q '"session_id"'; then
    print_result "Start Learning Session" "PASS"
    SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('session_id', ''))" 2>/dev/null)
else
    print_result "Start Learning Session" "FAIL"
fi

# 5.7 Complete Learning Session
COMPLETE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/study-center/progress/complete" \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"student_id\": \"$STUDENT_ID\",
    \"topic_id\": \"T01\",
    \"session_id\": \"$SESSION_ID\"
  }")

if echo "$COMPLETE_RESPONSE" | grep -q '"success"'; then
    print_result "Complete Learning Session" "PASS"
else
    print_result "Complete Learning Session" "FAIL"
fi

# 5.8 Get Progress
PROGRESS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/progress/$STUDENT_ID" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$PROGRESS_RESPONSE" | grep -q '"student_id"'; then
    print_result "Get Progress" "PASS"
else
    print_result "Get Progress" "FAIL"
fi

# 5.9 Get Learning Journey
JOURNEY_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/journey/$STUDENT_ID" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$JOURNEY_RESPONSE" | grep -q '"student_id"'; then
    print_result "Get Learning Journey" "PASS"
else
    print_result "Get Learning Journey" "FAIL"
fi

# 5.10 Get Parent Insights
INSIGHTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/study-center/parent-progress/$CHILD_ID?child_name=Test%20Child" \
  -H "Authorization: Bearer $PARENT_TOKEN")

if echo "$INSIGHTS_RESPONSE" | grep -q '"child_id"'; then
    print_result "Get Parent Insights" "PASS"
else
    print_result "Get Parent Insights" "FAIL"
fi

echo ""

# ==================== AI FEATURES ====================
echo "=== 6. AI Features (10 endpoints) ==="

# 6.1 Vector Search (AI-powered)
echo -e "${YELLOW}Testing Gemini-powered vector search...${NC}"
SEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/vector-search/query" \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are Newton'\''s laws of motion?",
    "top_k": 5,
    "filters": {
      "exam": "JEE_MAIN",
      "subject": "Physics"
    },
    "include_metadata": true
  }')

if echo "$SEARCH_RESPONSE" | grep -q '"results"'; then
    print_result "Vector Search (Gemini)" "PASS" "Semantic search working"
    RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_results', 0))" 2>/dev/null)
    echo -e "  ${BLUE}Found $RESULT_COUNT results${NC}"
else
    print_result "Vector Search (Gemini)" "FAIL" "$(echo $SEARCH_RESPONSE | head -c 150)"
fi

# 6.2 Batch Vector Search
BATCH_SEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/vector-search/query/batch" \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["Newton'\''s laws", "Thermodynamics"],
    "top_k": 3,
    "filters": {"exam": "JEE_MAIN"}
  }')

if echo "$BATCH_SEARCH_RESPONSE" | grep -q '"total_queries"'; then
    print_result "Batch Vector Search" "PASS"
else
    print_result "Batch Vector Search" "FAIL"
fi

# 6.3 Get Search Index Status
INDEX_STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/vector-search/index/status" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$INDEX_STATUS_RESPONSE" | grep -q '"service"'; then
    print_result "Get Index Status" "PASS"
else
    print_result "Get Index Status" "FAIL"
fi

# 6.4 Get Syllabus Content
SYLLABUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/vector-search/syllabus/JEE_MAIN/Physics" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$SYLLABUS_RESPONSE" | grep -q '"topics"'; then
    print_result "Get Syllabus Content" "PASS"
else
    print_result "Get Syllabus Content" "FAIL"
fi

# 6.5 Get Syllabus Stats
SYLLABUS_STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/vector-search/syllabus/stats" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$SYLLABUS_STATS_RESPONSE" | grep -q '"total_topics"'; then
    print_result "Get Syllabus Stats" "PASS"
else
    print_result "Get Syllabus Stats" "FAIL"
fi

# 6.6 RAG Question Generation (AI-powered)
echo -e "${YELLOW}Testing RAG question generation with Gemini...${NC}"
RAG_RESPONSE=$(curl -s -X POST "$BASE_URL/api/rag/generate-questions" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Kinematics",
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "num_questions": 3,
    "include_explanations": true,
    "use_cache": false
  }')

if echo "$RAG_RESPONSE" | grep -q '"questions"'; then
    print_result "RAG Question Generation (AI)" "PASS" "Questions generated successfully"
    QUESTION_COUNT=$(echo "$RAG_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('questions', [])))" 2>/dev/null)
    echo -e "  ${BLUE}Generated $QUESTION_COUNT questions${NC}"
else
    print_result "RAG Question Generation (AI)" "FAIL" "$(echo $RAG_RESPONSE | head -c 150)"
fi

# 6.7 RAG Batch Generation
RAG_BATCH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/rag/generate-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["Kinematics", "Newton'\''s Laws"],
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "questions_per_topic": 2
  }')

if echo "$RAG_BATCH_RESPONSE" | grep -q '"Kinematics"'; then
    print_result "RAG Batch Generation" "PASS"
else
    print_result "RAG Batch Generation" "FAIL"
fi

# 6.8 RAG Pipeline Status
RAG_STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/rag/pipeline/status")

if echo "$RAG_STATUS_RESPONSE" | grep -q '"all_systems_ok"'; then
    print_result "RAG Pipeline Status" "PASS"
else
    print_result "RAG Pipeline Status" "FAIL"
fi

# 6.9 RAG Metrics
RAG_METRICS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/rag/metrics")

if echo "$RAG_METRICS_RESPONSE" | grep -q '"total_generated"'; then
    print_result "RAG Metrics" "PASS"
else
    print_result "RAG Metrics" "FAIL"
fi

echo ""

# ==================== DIAGNOSTIC TESTS ====================
echo "=== 7. Diagnostic Tests (8 endpoints) ==="

# 7.1 Schedule Test
SCHEDULE_TEST_RESPONSE=$(curl -s -X POST "$BASE_URL/api/diagnostic-test/schedule" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"child_id\": \"$CHILD_ID\",
    \"exam_type\": \"JEE_MAIN\",
    \"scheduled_date\": \"$FUTURE_DATE\",
    \"test_id\": \"test_$TIMESTAMP\"
  }")

if echo "$SCHEDULE_TEST_RESPONSE" | grep -q '"test_id"'; then
    print_result "Schedule Diagnostic Test" "PASS"
    SCHEDULED_TEST_ID=$(echo "$SCHEDULE_TEST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('test_id', ''))" 2>/dev/null)
else
    print_result "Schedule Diagnostic Test" "FAIL"
fi

# 7.2 Get Test Metadata
TEST_META_RESPONSE=$(curl -s -X GET "$BASE_URL/api/diagnostic-test/$SCHEDULED_TEST_ID/metadata" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$TEST_META_RESPONSE" | grep -q '"test_id"'; then
    print_result "Get Test Metadata" "PASS"
else
    print_result "Get Test Metadata" "FAIL"
fi

# 7.3 Get Test Status
TEST_STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/diagnostic-test/$SCHEDULED_TEST_ID/status" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$TEST_STATUS_RESPONSE" | grep -q '"status"'; then
    print_result "Get Test Status" "PASS"
else
    print_result "Get Test Status" "FAIL"
fi

# 7.4 Start Test
START_TEST_RESPONSE=$(curl -s -X POST "$BASE_URL/api/diagnostic-test/$SCHEDULED_TEST_ID/start" \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"student_id\": \"$STUDENT_ID\"}")

if echo "$START_TEST_RESPONSE" | grep -q '"start_time"'; then
    print_result "Start Test" "PASS"
else
    print_result "Start Test" "FAIL"
fi

# 7.5 Submit Test
SUBMIT_TEST_RESPONSE=$(curl -s -X POST "$BASE_URL/api/diagnostic-test/$SCHEDULED_TEST_ID/submit" \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"test_id\": \"$SCHEDULED_TEST_ID\",
    \"student_id\": \"$STUDENT_ID\",
    \"answers\": {\"1\": \"A\", \"2\": \"B\", \"3\": \"C\"},
    \"time_taken\": 3600,
    \"submission_time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }")

if echo "$SUBMIT_TEST_RESPONSE" | grep -q '"total_score"'; then
    print_result "Submit Test" "PASS"
else
    print_result "Submit Test" "FAIL"
fi

# 7.6 Get Test Results
RESULTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/diagnostic-test/$SCHEDULED_TEST_ID/results" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$RESULTS_RESPONSE" | grep -q '"total_score"'; then
    print_result "Get Test Results" "PASS"
else
    print_result "Get Test Results" "FAIL"
fi

# 7.7 Get Student Tests
STUDENT_TESTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/diagnostic-test/student/$STUDENT_ID?limit=5" \
  -H "Authorization: Bearer $CHILD_TOKEN")

if echo "$STUDENT_TESTS_RESPONSE" | grep -q '\['; then
    print_result "Get Student Tests" "PASS"
else
    print_result "Get Student Tests" "FAIL"
fi

echo ""

# ==================== PAYMENT ====================
echo "=== 8. Payment & Subscriptions (6 endpoints) ==="

# 8.1 Get Plans
PLANS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/payment/plans")

if echo "$PLANS_RESPONSE" | grep -q '"plan_id"'; then
    print_result "Get Subscription Plans" "PASS"
else
    print_result "Get Subscription Plans" "FAIL"
fi

# 8.2 Get Subscription Status
SUB_STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/payment/subscription/$PARENT_ID" \
  -H "Authorization: Bearer $PARENT_TOKEN")

if echo "$SUB_STATUS_RESPONSE" | grep -q '"is_active"'; then
    print_result "Get Subscription Status" "PASS"
else
    print_result "Get Subscription Status" "FAIL"
fi

# 8.3 Get Transaction History
TRANSACTIONS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/payment/transactions/$PARENT_ID" \
  -H "Authorization: Bearer $PARENT_TOKEN")

if echo "$TRANSACTIONS_RESPONSE" | grep -q '\['; then
    print_result "Get Transaction History" "PASS"
else
    print_result "Get Transaction History" "FAIL"
fi

echo ""

# ==================== SUMMARY ====================
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo "Success Rate: ${PASS_RATE}%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the output above.${NC}"
    exit 1
fi
