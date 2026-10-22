# Parent Dashboard Router Testing Documentation

## Overview

The parent dashboard router provides endpoints for parents to monitor their child's progress, view reports, manage notifications, and set goals. It offers comprehensive insights into the child's learning journey and performance.

## Endpoints

### GET /api/parent/dashboard/{child_id}

Get comprehensive dashboard overview for a child's progress.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/parent/dashboard/CHILD_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/parent/dashboard/{{child_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `child_id`: `CHILD_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "child_id": "child_abc123",
    "child_name": "Rahul Sharma",
    "overall_progress": 67.5,
    "current_streak": 5,
    "hours_studied_today": 3.5,
    "hours_studied_week": 22.0,
    "schedule_status": "on_track",
    "days_until_exam": 45,
    "weak_areas": [
        {"subject": "Physics", "topic": "Thermodynamics", "accuracy": "45%"},
        {"subject": "Chemistry", "topic": "Organic Chemistry", "accuracy": "52%"}
    ],
    "upcoming_tasks": [
        {"date": "2024-01-16", "topic": "Calculus - Integration", "duration": "2 hours"},
        {"date": "2024-01-17", "topic": "Physics - Optics", "duration": "1.5 hours"}
    ],
    "recent_test_score": 78.5,
    "last_active": "2024-01-15T18:30:00Z"
}
```

#### Error Scenarios

**404 Not Found - Child Not Found:**
```json
{
    "detail": "Child profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get dashboard. Please try again later."
}
```

#### Troubleshooting

1. **Child ID Required:**
   - Must provide valid `child_id` in URL path
   - Child must exist in the system
   - Child must belong to authenticated parent

2. **Data Verification:**
   - Dashboard data is calculated from multiple sources
   - Progress metrics come from test scores and study time
   - Weak areas identified from performance analysis
   - Upcoming tasks from scheduled study plans

3. **Performance Metrics:**
   - Overall progress: Weighted average of subject performances
   - Current streak: Consecutive days of activity
   - Hours studied: Tracked from study sessions
   - Schedule status: Based on study plan adherence

---

### GET /api/parent/reports/weekly/{child_id}

Get detailed weekly progress report for a child.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/parent/reports/weekly/CHILD_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/parent/reports/weekly/{{child_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `child_id`: `CHILD_ID`
- Query Params (Optional):
  - `week_start`: `2024-01-08` (defaults to current week)

#### Expected Output

**Success Response (200):**
```json
{
    "child_id": "child_abc123",
    "week_start": "2024-01-08",
    "week_end": "2024-01-14",
    "total_hours_studied": 28.5,
    "previous_week_hours": 25.0,
    "topics_completed": 12,
    "tests_taken": 3,
    "average_test_score": 76.5,
    "attendance_rate": 85.7,
    "subject_breakdown": {
        "Physics": {"hours": 10.0, "score": 72.0},
        "Chemistry": {"hours": 9.5, "score": 78.0},
        "Mathematics": {"hours": 9.0, "score": 79.5}
    },
    "achievements": ["7-day streak", "Completed Calculus chapter"],
    "areas_of_concern": ["Low accuracy in Thermodynamics"]
}
```

#### Error Scenarios

**404 Not Found - Child Not Found:**
```json
{
    "detail": "Child profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get weekly report. Please try again later."
}
```

#### Troubleshooting

1. **Date Range Validation:**
   - Week start and end must be valid dates
   - Week cannot span more than 7 days
   - Default is current week if not specified

2. **Data Aggregation:**
   - Hours studied from study sessions and tests
   - Test scores from diagnostic and practice tests
   - Attendance based on completed activities vs scheduled

3. **Subject Breakdown:**
   - Hours and scores tracked per subject
   - Used for identifying strong/weak areas
   - Calculated from completed topics and tests

---

### POST /api/parent/reports/email-schedule

Schedule automated email reports for a parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/parent/reports/email-schedule" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "parent_id": "parent_123",
    "child_id": "child_abc123",
    "email": "parent@example.com",
    "frequency": "weekly",
    "day_of_week": 6,
    "enabled": true
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/parent/reports/email-schedule`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "parent_id": "parent_123",
    "child_id": "child_abc123",
    "email": "parent@example.com",
    "frequency": "weekly",
    "day_of_week": 6,
    "enabled": true
}
```

#### Request Examples

**Valid Request - Weekly Reports:**
```json
{
    "parent_id": "parent_123",
    "child_id": "child_abc123",
    "email": "parent@example.com",
    "frequency": "weekly",
    "day_of_week": 6,
    "enabled": true
}
```

**Valid Request - Daily Reports:**
```json
{
    "parent_id": "parent_123",
    "child_id": "child_abc123",
    "email": "parent@example.com",
    "frequency": "daily",
    "enabled": true
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "success": true,
    "message": "Email reports scheduled for parent@example.com",
    "frequency": "weekly"
}
```

#### Error Scenarios

**400 Bad Request - Invalid Frequency:**
```json
{
    "detail": "Invalid frequency. Must be one of: daily, weekly, monthly"
}
```

**400 Bad Request - Invalid Day:**
```json
{
    "detail": "Invalid day_of_week. Must be between 0 and 6"
}
```

#### Troubleshooting

1. **Email Service Integration:**
   - This endpoint would integrate with an email service
   - Currently returns success response
   - Email scheduling is stored for future sending

2. **Frequency Options:**
   - `daily`: Reports sent every day
   - `weekly`: Reports sent once per week
   - `monthly`: Reports sent once per month

3. **Day of Week:**
   - 0: Monday, 1: Tuesday, 2: Wednesday, 3: Thursday
   - 4: Friday, 5: Saturday, 6: Sunday

---

### GET /api/parent/notifications/settings

Get notification preferences for a parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/parent/notifications/settings?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/parent/notifications/settings`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `parent_id`: `PARENT_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "parent_id": "parent_123",
    "missed_days_alert": true,
    "daily_summary": false,
    "test_completion": true,
    "schedule_milestones": true,
    "weekly_report": true,
    "low_performance_alert": true,
    "achievement_notifications": true,
    "email_notifications": true,
    "push_notifications": false
}
```

#### Error Scenarios

**404 Not Found - Settings Not Found:**
```json
{
    "detail": "Notification settings not found for this parent"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get notification settings. Please try again later."
}
```

---

### PUT /api/parent/notifications/settings

Update notification preferences for a parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X PUT "http://localhost:8000/api/parent/notifications/settings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "missed_days_alert": false,
    "push_notifications": true,
    "low_performance_alert": false
  }'
```

2. **Using Postman:**
- Method: PUT
- URL: `{{base_url}}/api/parent/notifications/settings`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "missed_days_alert": false,
    "push_notifications": true,
    "low_performance_alert": false
}
```

#### Request Examples

**Valid Partial Update:**
```json
{
    "missed_days_alert": false,
    "push_notifications": true,
    "low_performance_alert": false
}
```

**Invalid Request Examples:**
```json
// Invalid boolean values
{
    "missed_days_alert": "yes",
    "push_notifications": "maybe",
    "low_performance_alert": "no"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "parent_id": "parent_123",
    "missed_days_alert": false,
    "daily_summary": false,
    "test_completion": true,
    "schedule_milestones": true,
    "weekly_report": true,
    "low_performance_alert": true,
    "achievement_notifications": true,
    "email_notifications": true,
    "push_notifications": true
}
```

#### Error Scenarios

**404 Not Found - Settings Not Found:**
```json
{
    "detail": "Notification settings not found for this parent"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to update notification settings. Please try again later."
}
```

#### Troubleshooting

1. **Partial Updates Supported:**
   - Only provided fields are updated
   - Omitted fields remain unchanged
   - All boolean fields must be true or false

2. **Notification Types:**
   - `missed_days_alert`: Alert when child misses 2+ consecutive days
   - `daily_summary`: Daily progress summary emails
   - `test_completion`: Notifications when tests are completed
   - `schedule_milestones`: Study plan milestone alerts
   - `weekly_report`: Weekly progress reports
   - `low_performance_alert`: Alerts for low test scores
   - `achievement_notifications`: Badge and milestone notifications

---

### POST /api/parent/goals/{child_id}

Create a new goal for a child.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/parent/goals/CHILD_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "goal_type": "target_score",
    "target_value": 85.0,
    "deadline": "2024-03-31"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/parent/goals/{{child_id}}`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `child_id`: `CHILD_ID`
- Body (raw JSON):
```json
{
    "goal_type": "target_score",
    "target_value": 85.0,
    "deadline": "2024-03-31"
}
```

#### Request Examples

**Valid Request - Target Score Goal:**
```json
{
    "goal_type": "target_score",
    "target_value": 85.0,
    "deadline": "2024-03-31"
}
```

**Valid Request - Daily Hours Goal:**
```json
{
    "goal_type": "daily_hours",
    "target_value": 2.5,
    "deadline": "2024-02-15"
}
```

**Invalid Request Examples:**
```json
// Invalid goal type
{
    "goal_type": "invalid_type",
    "target_value": 85.0
}

// Missing required fields
{
    "target_value": 85.0
}

// Invalid deadline (past date)
{
    "goal_type": "target_score",
    "target_value": 85.0,
    "deadline": "2023-03-31"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "goal_id": "goal_abc123",
    "child_id": "child_123",
    "goal_type": "target_score",
    "target_value": 85.0,
    "deadline": "2024-03-31",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### Error Scenarios

**404 Not Found - Child Not Found:**
```json
{
    "detail": "Child profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to create goal. Please try again later."
}
```

#### Troubleshooting

1. **Goal Types:**
   - `target_score`: Achieve a specific test score
   - `daily_hours`: Study for a set number of hours daily
   - `topic_completion`: Complete specific learning topics
   - `test_count`: Complete a certain number of tests

2. **Deadline Validation:**
   - Must be in the future
   - Format: ISO 8601 date string
   - Used for goal tracking and reminders

3. **Target Values:**
   - Target scores: 0-100 (exam percentage)
   - Daily hours: Positive number (reasonable study hours)
   - Test counts: Positive integer

---

### GET /api/parent/goals/{child_id}

Get all goals for a child.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/parent/goals/CHILD_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/parent/goals/{{child_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `child_id`: `CHILD_ID`

#### Expected Output

**Success Response (200):**
```json
[
    {
        "goal_id": "goal_abc123",
        "child_id": "child_123",
        "goal_type": "target_score",
        "target_value": 85.0,
        "current_value": 78.5,
        "deadline": "2024-03-31",
        "status": "active",
        "created_at": "2024-01-15T10:30:00Z",
        "completed_at": null
    },
    {
        "goal_id": "goal_def456",
        "child_id": "child_123",
        "goal_type": "daily_hours",
        "target_value": 2.0,
        "current_value": 1.8,
        "deadline": "2024-02-15",
        "status": "active",
        "created_at": "2024-01-10T08:00:00Z",
        "completed_at": null
    }
]
```

#### Error Scenarios

**404 Not Found - Child Not Found:**
```json
{
    "detail": "Child profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get goals. Please try again later."
}
```

---

### PUT /api/parent/goals/{child_id}/{goal_id}

Update an existing goal for a child.

#### Testing Steps

1. **Using curl:**
```bash
curl -X PUT "http://localhost:8000/api/parent/goals/CHILD_ID/GOAL_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "target_value": 90.0,
    "status": "active"
  }'
```

2. **Using Postman:**
- Method: PUT
- URL: `{{base_url}}/api/parent/goals/{{child_id}}/{{goal_id}}`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `child_id`: `CHILD_ID`
  - `goal_id`: `GOAL_ID`
- Body (raw JSON):
```json
{
    "target_value": 90.0,
    "status": "active"
}
```

#### Request Examples

**Valid Update - Increase Target:**
```json
{
    "target_value": 90.0,
    "status": "active"
}
```

**Valid Update - Mark Complete:**
```json
{
    "status": "completed",
    "completed_at": "2024-01-20T15:45:00Z"
}
```

**Invalid Request Examples:**
```json
// Invalid target value
{
    "target_value": -5.0
}

// Invalid status
{
    "status": "invalid_status"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "goal_id": "goal_abc123",
    "child_id": "child_123",
    "goal_type": "target_score",
    "target_value": 85.0,
    "current_value": 87.5,
    "deadline": "2024-03-31",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": null
}
```

#### Error Scenarios

**404 Not Found - Goal Not Found:**
```json
{
    "detail": "Goal not found"
}
```

**403 Forbidden - Ownership Error:**
```json
{
    "detail": "Goal does not belong to this parent"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to update goal. Please try again later."
}
```

#### Troubleshooting

1. **Goal Status Values:**
   - `active`: Currently being worked towards
   - `completed`: Successfully achieved
   - `failed`: No longer achievable or cancelled
   - `cancelled`: Explicitly cancelled by parent

2. **Progress Calculation:**
   - Current value vs target value shows progress percentage
   - Used for dashboard displays and motivation

3. **Deadline Management:**
   - Goals with deadlines trigger reminder notifications
   - Past deadlines are automatically marked as failed

## Common Issues Across All Endpoints

### Authentication Requirements
- All endpoints require parent authentication
- Use `Authorization: Bearer <token>` header
- Parent must be logged in with valid session

### Child Ownership Verification
- All operations verify child belongs to authenticated parent
- Prevents unauthorized access to other children's data
- Uses parent_id from authentication token for verification

### Data Aggregation
- Dashboard data calculated from multiple sources:
  - Study sessions and practice tests
  - Diagnostic and mock test results
  - Goal progress and completion status
  - Attendance and activity tracking

### Notification System
- Multiple notification channels supported:
  - Email: Weekly reports, daily summaries, alerts
  - Push: Real-time notifications (if enabled)
  - In-app: Achievement notifications, milestone alerts

### Goal Management
- Goals support different types for various learning objectives
- Progress tracking with current vs target values
- Deadline management with automatic status updates
- Completion tracking with timestamps

## AI Troubleshooting Prompt

```
I'm testing the Mentor AI parent dashboard router endpoint [INSERT_ENDPOINT] and encountering the following error:

[Insert error message here]

My request payload is:
```json
[Insert request payload here]
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Endpoint: [GET /api/parent/dashboard/{child_id}, GET /api/parent/reports/weekly/{child_id}, POST /api/parent/reports/email-schedule, GET /api/parent/notifications/settings, PUT /api/parent/notifications/settings, POST /api/parent/goals/{child_id}, GET /api/parent/goals/{child_id}, or PUT /api/parent/goals/{child_id}/{goal_id}]
- Authentication token: [Valid/Invalid/Missing]
- Parent ID: [If applicable]
- Child ID: [If applicable]
- Goal ID: [If applicable]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the parent dashboard flow in services/parent_dashboard_service.py
2. Checking if request format matches the appropriate model in models/parent_models.py
3. Verifying the child ownership verification process
4. Checking the goal creation and management logic
5. Verifying the notification settings management
6. Verifying the weekly report generation process
7. Providing specific steps to fix the issue

Context: This endpoint provides comprehensive parent dashboard functionality for the Mentor AI EdTech Platform, including child progress monitoring, report generation, notification management, and goal setting with proper ownership verification and data aggregation.