# Comprehensive Endpoint Test Report
Generated: 2025-12-02T19:33:18.983000
Base URL: http://localhost:8000

## Summary
- Total Tests: 100
- Successful: 34 (34.0%)
- Failed: 66 (66.0%)

## Results by Category
- ai: 6/6 (100.0%)
- analytics: 0/3 (0.0%)
- auth: 1/5 (20.0%)
- diagnostic-test: 1/7 (14.3%)
- email: 1/2 (50.0%)
- gamification: 4/7 (57.1%)
- onboarding: 4/8 (50.0%)
- parent: 2/7 (28.6%)
- payment: 2/5 (40.0%)
- phone: 1/2 (50.0%)
- rag: 4/6 (66.7%)
- root: 2/3 (66.7%)
- schedule: 0/1 (0.0%)
- student: 4/12 (33.3%)
- study-center: 2/11 (18.2%)
- syllabus: 0/7 (0.0%)
- test_child_123: 0/1 (0.0%)
- vector-search: 0/7 (0.0%)

## Failed Tests
### POST /api/auth/register/parent/email
- Status Code: 400
- Error: An account with email testparent@example.com already exists. Please login instead.
- Response Time: 1132.52ms

### POST /api/auth/register/parent/phone
- Status Code: 400
- Error: An account with phone number +919876543210 already exists. Please login instead.
- Response Time: 385.27ms

### POST /api/auth/register/simple
- Status Code: 400
- Error: An account with email testparent@example.com already exists. Please login instead.
- Response Time: 502.41ms

### POST /api/auth/login/phone
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'otp'], 'msg': 'Field required', 'input': {'phone': '+919876543210', 'password': 'TestPassword123'}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 3.94ms

### POST /verify/email/confirm
- Status Code: 400
- Error: Invalid verification code
- Response Time: 234.49ms

### POST /verify/phone/confirm
- Status Code: 400
- Error: Invalid OTP
- Response Time: 201.48ms

### POST /api/onboarding/preferences
- Status Code: 400
- Error: Preferences already exist for this parent. Use update endpoint to modify.
- Response Time: 87.73ms

### POST /child
- Status Code: 404
- Error: Not Found
- Response Time: 8.36ms

### GET /child/test_child_123
- Status Code: 404
- Error: Not Found
- Response Time: 7.93ms

### POST /api/onboarding/exam/select
- Status Code: 404
- Error: Child profile not found: test_child_123
- Response Time: 57.51ms

### GET /api/onboarding/exam/preferences
- Status Code: 404
- Error: Exam selection not found for child: test_child_123
- Response Time: 53.84ms

### PUT /api/onboarding/exam/preferences
- Status Code: 404
- Error: Child profile not found: test_child_123
- Response Time: 62.12ms

### POST /api/vector-search/embeddings/generate
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 8.39ms

### POST /api/vector-search/embeddings/batch
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 7.83ms

### GET /api/vector-search/embeddings/status
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 6.69ms

### POST /api/vector-search/query
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 9.46ms

### POST /api/vector-search/query/batch
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 9.22ms

### GET /api/vector-search/index/status
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 7.65ms

### GET /api/vector-search/syllabus/JEE_MAIN/Physics
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 9.56ms

### POST /api/rag/generate-questions
- Status Code: 0
- Error: 
- Response Time: 30033.22ms

### POST /api/rag/generate-batch
- Status Code: 422
- Error: [{'type': 'string_type', 'loc': ['body', 'topics', 0], 'msg': 'Input should be a valid string', 'input': {'topic': 'Kinematics', 'question_count': 3}, 'url': 'https://errors.pydantic.dev/2.12/v/string_type'}, {'type': 'string_type', 'loc': ['body', 'topics', 1], 'msg': 'Input should be a valid string', 'input': {'topic': 'Thermodynamics', 'question_count': 2}, 'url': 'https://errors.pydantic.dev/2.12/v/string_type'}]
- Response Time: 22590.31ms

### POST /api/diagnostic-test/generate
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 7.18ms

### POST /api/diagnostic-test/test_123/start
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 7.03ms

### POST /api/diagnostic-test/test_123/submit
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 6.36ms

### GET /api/diagnostic-test/test_123/results
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 5.68ms

### GET /api/diagnostic-test/test_123/status
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 5.10ms

### PATCH /api/diagnostic-test/test_123/status
- Status Code: 403
- Error: Admin privileges required
- Response Time: 4.65ms

### POST /api/schedule/generate
- Status Code: 401
- Error: Invalid token. Please login again.
- Response Time: 4.99ms

### POST /api/payment/create-order
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'parent_id'], 'msg': 'Field required', 'input': {'plan_id': 'premium_monthly', 'amount': 99900, 'currency': 'INR'}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 4.82ms

### GET /api/payment/transactions/test_parent_123
- Status Code: 500
- Error: Unable to retrieve transaction history. Please try again later.
- Response Time: 71.02ms

### POST /api/payment/cancel/test_parent_123
- Status Code: 500
- Error: Unable to cancel subscription. Please contact support.
- Response Time: 69.97ms

### GET /api/study-center/topics
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['query', 'student_id'], 'msg': 'Field required', 'input': None, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 2.90ms

### GET /api/study-center/topics/topic_123
- Status Code: 500
- Error: Failed to retrieve topic details. Please try again later.
- Response Time: 4.94ms

### GET /api/study-center/materials/topic_123
- Status Code: 500
- Error: Failed to retrieve learning materials. Please try again later.
- Response Time: 2.96ms

### POST /api/study-center/materials/generate
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'student_id'], 'msg': 'Field required', 'input': {'topic': "Newton's Laws", 'exam_type': 'JEE_MAIN', 'subject': 'Physics', 'material_types': ['notes', 'questions', 'videos']}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}, {'type': 'missing', 'loc': ['body', 'topic_id'], 'msg': 'Field required', 'input': {'topic': "Newton's Laws", 'exam_type': 'JEE_MAIN', 'subject': 'Physics', 'material_types': ['notes', 'questions', 'videos']}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 4.49ms

### GET /api/study-center/mindmap/topic_123
- Status Code: 500
- Error: Failed to retrieve mind map. Please try again later.
- Response Time: 3.84ms

### GET /api/study-center/teach/topic_123
- Status Code: 500
- Error: Failed to retrieve teaching content. Please try again later.
- Response Time: 3.03ms

### POST /api/study-center/progress/start
- Status Code: 500
- Error: Failed to start learning session. Please try again later.
- Response Time: 4.15ms

### POST /api/study-center/progress/complete
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'session_id'], 'msg': 'Field required', 'input': {'student_id': 'test_student_123', 'topic_id': 'topic_123', 'time_spent': 1200}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 2.94ms

### GET /api/study-center/parent-progress/child_123
- Status Code: 500
- Error: Failed to retrieve parent insights. Please try again later.
- Response Time: 113.63ms

### POST /api/analytics/generate
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'DefaultCredentialsError', 'message': 'Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.', 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 12179.34ms

### GET /api/analytics/student/test_student_123
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'DefaultCredentialsError', 'message': 'Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.', 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 12126.63ms

### GET /api/analytics/test/test_123
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'DefaultCredentialsError', 'message': 'Your default credentials were not found. To set up Application Default Credentials, see https://cloud.google.com/docs/authentication/external/set-up-adc for more information.', 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 12033.47ms

### GET /api/syllabus/coverage/test_student_123
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'TypeError', 'message': "string indices must be integers, not 'str'", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 15.38ms

### GET /api/syllabus/coverage/test_student_123/untested
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'TypeError', 'message': "string indices must be integers, not 'str'", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 12.43ms

### GET /api/syllabus/coverage/test_student_123/weak
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'TypeError', 'message': "string indices must be integers, not 'str'", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 17.85ms

### GET /api/syllabus/coverage/test_student_123/recommendations
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'TypeError', 'message': "string indices must be integers, not 'str'", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 16.89ms

### GET /api/syllabus/coverage/test_student_123/progress
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'TypeError', 'message': "string indices must be integers, not 'str'", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 13.31ms

### GET /api/syllabus/coverage/test_student_123/topic/topic_123
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'TypeError', 'message': "string indices must be integers, not 'str'", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 11.60ms

### GET /api/syllabus/coverage/health
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['query', 'exam_type'], 'msg': 'Field required', 'input': None, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 5.01ms

### GET /api/parent/dashboard/child_123
- Status Code: 404
- Error: Child not found: child_123
- Response Time: 43.94ms

### GET /api/parent/reports/weekly/child_123
- Status Code: 500
- Error: Failed to get weekly report
- Response Time: 50.57ms

### POST /api/parent/reports/email-schedule
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'parent_id'], 'msg': 'Field required', 'input': {'email': 'testparent@example.com', 'frequency': 'weekly', 'child_id': 'child_123'}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 8.56ms

### POST /api/parent/goals/child_123
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'child_id'], 'msg': 'Field required', 'input': {'title': 'Complete Physics syllabus', 'description': 'Finish all Physics topics in 2 months', 'target_date': '2026-01-31T19:33:18.533885Z', 'target_score': 85}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}, {'type': 'missing', 'loc': ['body', 'goal_type'], 'msg': 'Field required', 'input': {'title': 'Complete Physics syllabus', 'description': 'Finish all Physics topics in 2 months', 'target_date': '2026-01-31T19:33:18.533885Z', 'target_score': 85}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}, {'type': 'missing', 'loc': ['body', 'target_value'], 'msg': 'Field required', 'input': {'title': 'Complete Physics syllabus', 'description': 'Finish all Physics topics in 2 months', 'target_date': '2026-01-31T19:33:18.533885Z', 'target_score': 85}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 9.33ms

### GET /api/parent/goals/child_123
- Status Code: 500
- Error: Failed to get goals
- Response Time: 51.03ms

### GET /api/student/today/test_student_123
- Status Code: 404
- Error: No active schedule found for student: test_student_123
- Response Time: 58.25ms

### GET /api/student/topic/topic_123/resources
- Status Code: 404
- Error: Topic not found: topic_123
- Response Time: 59.16ms

### POST /api/student/practice/quick
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'duration_minutes'], 'msg': 'Field required', 'input': {'student_id': 'test_student_123', 'duration': 30, 'focus_area': 'weak_topics', 'subject': 'Physics'}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}, {'type': 'missing', 'loc': ['body', 'focus'], 'msg': 'Field required', 'input': {'student_id': 'test_student_123', 'duration': 30, 'focus_area': 'weak_topics', 'subject': 'Physics'}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 11.65ms

### POST /api/student/doubts
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'doubt_text'], 'msg': 'Field required', 'input': {'student_id': 'test_student_123', 'question': 'What is the difference between kinetic and potential energy?', 'subject': 'Physics', 'topic': 'Work, Energy and Power'}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 11.17ms

### GET /api/student/doubts/doubt_123/explanation
- Status Code: 404
- Error: Doubt not found: doubt_123
- Response Time: 45.55ms

### GET /api/student/revision/due
- Status Code: 500
- Error: Failed to get revision items
- Response Time: 50.17ms

### POST /api/student/bookmarks
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'item_type'], 'msg': 'Field required', 'input': {'student_id': 'test_student_123', 'type': 'question', 'item_id': 'q_123', 'title': "Newton's Second Law Question", 'subject': 'Physics'}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 8.95ms

### GET /api/student/bookmarks
- Status Code: 500
- Error: Failed to get bookmarks
- Response Time: 55.43ms

### GET /api/gamification/challenge/daily
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'ValidationError', 'message': "1 validation error for DailyChallenge\nchallenge_date\n  Field required [type=missing, input_value={'challenge_id': 'challen...s', 'topic': 'Calculus'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.12/v/missing", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 12.45ms

### POST /api/gamification/challenge/daily/submit
- Status Code: 422
- Error: [{'type': 'missing', 'loc': ['body', 'student_id'], 'msg': 'Field required', 'input': {'challenge_id': 'challenge_2024-01-15', 'answer': 'B', 'time_taken': 95}, 'url': 'https://errors.pydantic.dev/2.12/v/missing'}]
- Response Time: 9.13ms

### GET /api/gamification/challenge/leaderboard
- Status Code: 500
- Error: {'success': False, 'error': {'type': 'ValidationError', 'message': "1 validation error for Leaderboard\nleaderboard_date\n  Field required [type=missing, input_value={'date': datetime.date(20...otal_participants': 150}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.12/v/missing", 'detail': 'An internal server error occurred. Please try again later.'}}
- Response Time: 12.80ms

## Slow Tests (>2000ms)
### POST /api/rag/generate-questions
- Response Time: 30033.22ms
- Status Code: 0

### POST /api/rag/generate-batch
- Response Time: 22590.31ms
- Status Code: 422

### POST /api/analytics/generate
- Response Time: 12179.34ms
- Status Code: 500

### GET /api/analytics/student/test_student_123
- Response Time: 12126.63ms
- Status Code: 500

### GET /api/analytics/test/test_123
- Response Time: 12033.47ms
- Status Code: 500

### GET /api/study-center/journey/test_student_123
- Response Time: 6290.84ms
- Status Code: 200

## Detailed Results
### ai
✅ POST /api/ai/tutor/ask - 200 (9.76ms)
✅ GET /api/ai/tutor/history/test_student_123 - 200 (8.55ms)
✅ GET /api/ai/recommend/topics/test_student_123 - 200 (9.23ms)
✅ GET /api/ai/recommend/resources/topic_123 - 200 (9.21ms)
✅ GET /api/ai/readiness/test_student_123 - 200 (7.15ms)
✅ GET /api/ai/analysis/mistakes/test_student_123 - 200 (6.74ms)
### analytics
❌ POST /api/analytics/generate - 500 (12179.34ms)
❌ GET /api/analytics/student/test_student_123 - 500 (12126.63ms)
❌ GET /api/analytics/test/test_123 - 500 (12033.47ms)
### auth
❌ POST /api/auth/register/parent/email - 400 (1132.52ms)
❌ POST /api/auth/register/parent/phone - 400 (385.27ms)
❌ POST /api/auth/register/simple - 400 (502.41ms)
✅ POST /api/auth/login/email - 200 (1586.31ms)
❌ POST /api/auth/login/phone - 422 (3.94ms)
### diagnostic-test
❌ POST /api/diagnostic-test/generate - 401 (7.18ms)
❌ POST /api/diagnostic-test/test_123/start - 401 (7.03ms)
❌ POST /api/diagnostic-test/test_123/submit - 401 (6.36ms)
❌ GET /api/diagnostic-test/test_123/results - 401 (5.68ms)
❌ GET /api/diagnostic-test/test_123/status - 401 (5.10ms)
❌ PATCH /api/diagnostic-test/test_123/status - 403 (4.65ms)
✅ GET /api/diagnostic-test/management/health - 200 (3.01ms)
### email
✅ POST /verify/email/send - 200 (84.60ms)
❌ POST /verify/email/confirm - 400 (234.49ms)
### gamification
✅ GET /api/gamification/achievements - 200 (7.00ms)
✅ POST /api/gamification/achievements/claim/ach_123 - 200 (6.10ms)
❌ GET /api/gamification/challenge/daily - 500 (12.45ms)
❌ POST /api/gamification/challenge/daily/submit - 422 (9.13ms)
❌ GET /api/gamification/challenge/leaderboard - 500 (12.80ms)
✅ GET /api/gamification/streak - 200 (9.39ms)
✅ GET /api/gamification/points/history - 200 (4.89ms)
### onboarding
❌ POST /api/onboarding/preferences - 400 (87.73ms)
✅ GET /api/onboarding/preferences - 200 (73.83ms)
✅ PUT /api/onboarding/preferences - 200 (213.90ms)
✅ GET /api/onboarding/exams/available - 200 (9.27ms)
❌ POST /api/onboarding/exam/select - 404 (57.51ms)
❌ GET /api/onboarding/exam/preferences - 404 (53.84ms)
❌ PUT /api/onboarding/exam/preferences - 404 (62.12ms)
✅ GET /api/onboarding/status - 200 (171.51ms)
### parent
❌ GET /api/parent/dashboard/child_123 - 404 (43.94ms)
❌ GET /api/parent/reports/weekly/child_123 - 500 (50.57ms)
❌ POST /api/parent/reports/email-schedule - 422 (8.56ms)
✅ GET /api/parent/notifications/settings - 200 (51.91ms)
✅ PUT /api/parent/notifications/settings - 200 (80.50ms)
❌ POST /api/parent/goals/child_123 - 422 (9.33ms)
❌ GET /api/parent/goals/child_123 - 500 (51.03ms)
### payment
✅ GET /api/payment/plans - 200 (4.25ms)
❌ POST /api/payment/create-order - 422 (4.82ms)
✅ GET /api/payment/subscription/test_parent_123 - 200 (64.02ms)
❌ GET /api/payment/transactions/test_parent_123 - 500 (71.02ms)
❌ POST /api/payment/cancel/test_parent_123 - 500 (69.97ms)
### phone
✅ POST /verify/phone/send - 200 (129.60ms)
❌ POST /verify/phone/confirm - 400 (201.48ms)
### rag
❌ POST /api/rag/generate-questions - 0 (30033.22ms)
❌ POST /api/rag/generate-batch - 422 (22590.31ms)
✅ POST /api/rag/context/build - 200 (8.64ms)
✅ POST /api/rag/context/preview - 200 (9.05ms)
✅ GET /api/rag/pipeline/status - 200 (69.34ms)
✅ GET /api/rag/metrics - 200 (6.26ms)
### root
✅ GET / - 200 (8.16ms)
✅ GET /health - 200 (2.03ms)
❌ POST /child - 404 (8.36ms)
### schedule
❌ POST /api/schedule/generate - 401 (4.99ms)
### student
❌ GET /api/student/today/test_student_123 - 404 (58.25ms)
❌ GET /api/student/topic/topic_123/resources - 404 (59.16ms)
❌ POST /api/student/practice/quick - 422 (11.65ms)
❌ POST /api/student/doubts - 422 (11.17ms)
❌ GET /api/student/doubts/doubt_123/explanation - 404 (45.55ms)
❌ GET /api/student/revision/due - 500 (50.17ms)
✅ POST /api/student/revision/mark-complete/topic_123 - 200 (5.33ms)
❌ POST /api/student/bookmarks - 422 (8.95ms)
❌ GET /api/student/bookmarks - 500 (55.43ms)
✅ DELETE /api/student/bookmarks/bookmark_123 - 200 (6.49ms)
✅ GET /api/student/insights/test_student_123 - 200 (6.11ms)
✅ GET /api/student/compare/percentile - 200 (6.46ms)
### study-center
❌ GET /api/study-center/topics - 422 (2.90ms)
❌ GET /api/study-center/topics/topic_123 - 500 (4.94ms)
❌ GET /api/study-center/materials/topic_123 - 500 (2.96ms)
❌ POST /api/study-center/materials/generate - 422 (4.49ms)
❌ GET /api/study-center/mindmap/topic_123 - 500 (3.84ms)
❌ GET /api/study-center/teach/topic_123 - 500 (3.03ms)
✅ GET /api/study-center/progress/test_student_123 - 200 (49.86ms)
❌ POST /api/study-center/progress/start - 500 (4.15ms)
❌ POST /api/study-center/progress/complete - 422 (2.94ms)
✅ GET /api/study-center/journey/test_student_123 - 200 (6290.84ms)
❌ GET /api/study-center/parent-progress/child_123 - 500 (113.63ms)
### syllabus
❌ GET /api/syllabus/coverage/test_student_123 - 500 (15.38ms)
❌ GET /api/syllabus/coverage/test_student_123/untested - 500 (12.43ms)
❌ GET /api/syllabus/coverage/test_student_123/weak - 500 (17.85ms)
❌ GET /api/syllabus/coverage/test_student_123/recommendations - 500 (16.89ms)
❌ GET /api/syllabus/coverage/test_student_123/progress - 500 (13.31ms)
❌ GET /api/syllabus/coverage/test_student_123/topic/topic_123 - 500 (11.60ms)
❌ GET /api/syllabus/coverage/health - 422 (5.01ms)
### test_child_123
❌ GET /child/test_child_123 - 404 (7.93ms)
### vector-search
❌ POST /api/vector-search/embeddings/generate - 401 (8.39ms)
❌ POST /api/vector-search/embeddings/batch - 401 (7.83ms)
❌ GET /api/vector-search/embeddings/status - 401 (6.69ms)
❌ POST /api/vector-search/query - 401 (9.46ms)
❌ POST /api/vector-search/query/batch - 401 (9.22ms)
❌ GET /api/vector-search/index/status - 401 (7.65ms)
❌ GET /api/vector-search/syllabus/JEE_MAIN/Physics - 401 (9.56ms)