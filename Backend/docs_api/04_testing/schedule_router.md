# Schedule Router API Documentation

## Overview

The Schedule Router provides endpoints for AI-powered study schedule generation, management, and progress tracking. It uses Gemini AI to create personalized study plans based on student performance, exam dates, and learning preferences.

## Base URL
```
/api/schedule
```

## Endpoints

### 1. Generate Study Schedule

**Endpoint:** `POST /api/schedule/generate`

**Description:** Generate a personalized AI-powered study schedule for a student.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/schedule/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123",
    "analytics_id": "analytics_456",
    "exam_type": "JEE_MAIN",
    "exam_date": "2024-04-01",
    "daily_study_hours": 5.0,
    "preferred_study_times": ["morning", "evening"],
    "weak_topics": ["Calculus", "Thermodynamics"],
    "strong_topics": ["Algebra", "Organic Chemistry"],
    "constraints": {
      "no_study_days": ["Sunday"],
      "max_continuous_hours": 3
    }
  }'
```

#### Expected Response (201 Created)
```json
{
  "schedule_id": "schedule_student123_1234567890",
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "status": "active",
  "start_date": "2024-01-15",
  "exam_date": "2024-04-01",
  "daily_study_hours": 5.0,
  "completion_percentage": 0.0,
  "days": [
    {
      "day_number": 1,
      "date": "2024-01-15",
      "topics": [
        {
          "topic": "Calculus",
          "subject": "Mathematics",
          "estimated_hours": 2.5,
          "subtopics": ["Limits", "Continuity", "Differentiability"],
          "resources": [
            {
              "type": "video",
              "title": "Calculus Basics",
              "url": "https://example.com/calculus-basics"
            }
          ],
          "goals": ["Understand limit concepts", "Practice differentiation problems"],
          "priority": "high",
          "difficulty": "medium"
        }
      ],
      "total_estimated_hours": 5.0,
      "completed": false
    }
  ],
  "metadata": {
    "total_days": 75,
    "total_topics": 45,
    "weak_areas_focus": 60,
    "ai_generated": true,
    "generation_time": 3.2
  }
}
```

#### Requirements
- Valid analytics_id (student must have taken at least one test)
- Exam date must be in the future
- Daily study hours must be realistic (2-8 hours)

#### Process
1. Validates schedule request parameters
2. Fetches student analytics and performance data
3. Loads exam syllabus and weightages
4. Calculates topic priorities based on performance
5. Calculates time constraints and feasibility
6. Builds context for Gemini AI
7. Generates schedule using Gemini Flash 1.5
8. Validates and parses AI response
9. Saves schedule to Firestore
10. Returns complete schedule

#### Error Scenarios
- **400 Bad Request:** Invalid request data
- **404 Not Found:** Analytics or student not found
- **500 Internal Server Error:** Schedule generation failed

#### Troubleshooting
- Verify analytics_id exists and has test data
- Check exam_date is in valid ISO format and future date
- Ensure daily_study_hours is between 2-8 hours
- Confirm student_id exists in system

---

### 2. Get Schedule by ID

**Endpoint:** `GET /api/schedule/{schedule_id}`

**Description:** Retrieve a complete schedule by its unique identifier.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/schedule/schedule_student123_1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "schedule_id": "schedule_student123_1234567890",
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "status": "active",
  "start_date": "2024-01-15",
  "exam_date": "2024-04-01",
  "daily_study_hours": 5.0,
  "completion_percentage": 25.5,
  "days": [
    {
      "day_number": 1,
      "date": "2024-01-15",
      "topics": [...],
      "total_estimated_hours": 5.0,
      "completed": true
    },
    {
      "day_number": 2,
      "date": "2024-01-16",
      "topics": [...],
      "total_estimated_hours": 5.0,
      "completed": false
    }
  ],
  "metadata": {
    "total_days": 75,
    "total_topics": 45,
    "weak_areas_focus": 60,
    "ai_generated": true
  }
}
```

#### Error Scenarios
- **404 Not Found:** Schedule not found
- **500 Internal Server Error:** Failed to retrieve schedule

---

### 3. Get Active Student Schedule

**Endpoint:** `GET /api/schedule/student/{student_id}`

**Description:** Get currently active schedule for a student.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/schedule/student/student_123?status=active" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `status`: Filter by schedule status (active, completed, abandoned, paused)

#### Expected Response (200 OK)
```json
{
  "schedule_id": "schedule_student123_1234567890",
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "status": "active",
  "start_date": "2024-01-15",
  "exam_date": "2024-04-01",
  "daily_study_hours": 5.0,
  "completion_percentage": 25.5,
  "days": [...]
}
```

#### Returns null if:
- Student has no schedules
- All schedules are completed/abandoned

#### Error Scenarios
- **500 Internal Server Error:** Failed to retrieve schedule

---

### 4. Get Schedule History

**Endpoint:** `GET /api/schedule/student/{student_id}/history`

**Description:** Get all schedules for a student, sorted by creation date (newest first).

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/schedule/student/student_123/history?limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `limit`: Maximum number of schedules to return (default: 10, max: 100)

#### Expected Response (200 OK)
```json
[
  {
    "schedule_id": "schedule_student123_1234567890",
    "student_id": "student_123",
    "exam_type": "JEE_MAIN",
    "status": "active",
    "start_date": "2024-01-15",
    "exam_date": "2024-04-01",
    "completion_percentage": 25.5
  },
  {
    "schedule_id": "schedule_student123_9876543210",
    "student_id": "student_123",
    "exam_type": "JEE_MAIN",
    "status": "completed",
    "start_date": "2023-09-01",
    "exam_date": "2023-12-01",
    "completion_percentage": 100.0
  }
]
```

#### Use Cases
- View past schedules
- Track schedule changes over time
- Analyze completion rates

#### Error Scenarios
- **500 Internal Server Error:** Failed to retrieve schedule history

---

### 5. Regenerate Remaining Schedule

**Endpoint:** `POST /api/schedule/{schedule_id}/regenerate`

**Description:** Regenerate remaining portion of a schedule from a specific day.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/schedule/schedule_student123_1234567890/regenerate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_day": 15
  }'
```

#### Expected Response (200 OK)
```json
{
  "schedule_id": "schedule_student123_1234567890",
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "status": "active",
  "start_date": "2024-01-15",
  "exam_date": "2024-04-01",
  "daily_study_hours": 5.0,
  "completion_percentage": 20.0,
  "days": [
    // Days 1-14 (completed) remain unchanged
    // Days 15+ are regenerated based on current progress
  ],
  "metadata": {
    "regenerated_at": "2024-02-01T10:00:00Z",
    "regeneration_reason": "Student fell behind schedule"
  }
}
```

#### Process
1. Fetches existing schedule and progress
2. Identifies incomplete topics
3. Recalculates priorities based on current progress
4. Calculates remaining days until exam
5. Generates new schedule using Gemini AI
6. Merges with completed days
7. Saves updated schedule

#### Use Cases
- Student fell behind schedule
- Topics took longer than expected
- Schedule adjustments needed mid-way
- Performance improved/declined significantly

#### Error Scenarios
- **400 Bad Request:** Invalid current day
- **404 Not Found:** Schedule not found
- **500 Internal Server Error:** Failed to regenerate schedule

---

### 6. Update Schedule

**Endpoint:** `PUT /api/schedule/{schedule_id}`

**Description:** Update schedule fields.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X PUT "http://localhost:8000/api/schedule/schedule_student123_1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": {
      "status": "paused",
      "notes": "Paused due to exams",
      "daily_study_hours": 6.0
    }
  }'
```

#### Expected Response (200 OK)
```json
{
  "schedule_id": "schedule_student123_1234567890",
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "status": "paused",
  "start_date": "2024-01-15",
  "exam_date": "2024-04-01",
  "daily_study_hours": 6.0,
  "notes": "Paused due to exams",
  "completion_percentage": 25.5
}
```

#### Updatable Fields
- `status`: Change schedule status (active, paused, completed, abandoned)
- `notes`: Add/update schedule notes
- `daily_study_hours`: Adjust daily study hours

#### Restrictions
- Cannot modify completed days
- Cannot change exam_date (regenerate instead)
- Cannot change exam_type

#### Error Scenarios
- **400 Bad Request:** Invalid updates
- **404 Not Found:** Schedule not found
- **500 Internal Server Error:** Failed to update schedule

---

### 7. Delete Schedule

**Endpoint:** `DELETE /api/schedule/{schedule_id}`

**Description:** Delete a schedule (soft delete - marks as abandoned).

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X DELETE "http://localhost:8000/api/schedule/schedule_student123_1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Schedule deleted successfully"
}
```

#### Operation Details
- Marks schedule status as "abandoned"
- Preserves all data for historical records
- Does not physically delete from database

#### Use Cases
- Student wants to start fresh schedule
- Schedule is no longer relevant
- Exam was postponed/cancelled

#### Error Scenarios
- **404 Not Found:** Schedule not found
- **500 Internal Server Error:** Failed to delete schedule

---

### 8. Update Daily Progress

**Endpoint:** `POST /api/schedule/progress/update`

**Description:** Update progress for a specific day in schedule.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/schedule/progress/update" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "schedule_student123_1234567890",
    "day_number": 15,
    "date": "2024-01-29",
    "topics_completed": [
      {
        "topic": "Calculus",
        "subtopics_completed": ["Limits", "Continuity"],
        "time_spent_hours": 2.5,
        "confidence_level": 8,
        "notes": "Good progress on limits"
      }
    ],
    "total_time_spent": 5.0,
    "completion_percentage": 100,
    "challenges_faced": ["Differentiability concepts were tricky"],
    "additional_resources_used": ["YouTube tutorial on derivatives"]
  }'
```

#### Expected Response (200 OK)
```json
{
  "schedule_id": "schedule_student123_1234567890",
  "day_number": 15,
  "date": "2024-01-29",
  "topics_completed": [...],
  "total_time_spent": 5.0,
  "completion_percentage": 100,
  "updated_at": "2024-01-29T18:00:00Z"
}
```

#### Process
1. Validates day exists in schedule
2. Updates completion status for day
3. Stores progress in Firestore (subcollection)
4. Updates schedule completion percentage
5. Checks if rescheduling is needed
6. Returns updated progress

#### Triggers Reschedule Check
- Missed 2+ consecutive days
- Topic took 50%+ more time than estimated
- 3+ days behind schedule
- Practice test accuracy < 50%

#### Error Scenarios
- **400 Bad Request:** Invalid progress data
- **404 Not Found:** Schedule or day not found
- **500 Internal Server Error:** Failed to update progress

---

### 9. Get Progress Summary

**Endpoint:** `GET /api/schedule/progress/{schedule_id}`

**Description:** Get comprehensive progress summary for a schedule.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/schedule/progress/schedule_student123_1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "schedule_id": "schedule_student123_1234567890",
  "total_days": 75,
  "days_completed": 19,
  "days_remaining": 56,
  "total_topics_completed": 12,
  "total_topics": 45,
  "total_hours_studied": 95.5,
  "completion_percentage": 25.3,
  "days_ahead_behind": -2,
  "average_daily_study_time": 5.03,
  "current_streak": 5,
  "longest_streak": 12,
  "days_until_exam": 56,
  "on_track_percentage": 85.5,
  "subject_progress": {
    "Physics": {
      "completed": 4,
      "total": 15,
      "percentage": 26.7
    },
    "Chemistry": {
      "completed": 5,
      "total": 15,
      "percentage": 33.3
    },
    "Mathematics": {
      "completed": 3,
      "total": 15,
      "percentage": 20.0
    }
  },
  "last_updated": "2024-01-29T18:00:00Z"
}
```

#### Statistics Included
- Total days completed and remaining
- Total topics completed and hours studied
- Completion percentage
- Days ahead/behind schedule
- Average daily study time
- Current and longest study streak
- Days until exam
- Subject-wise progress

#### Use Cases
- Dashboard overview
- Progress tracking
- Performance analytics

#### Error Scenarios
- **404 Not Found:** Schedule not found
- **500 Internal Server Error:** Failed to get progress summary

---

### 10. Get Today's Tasks

**Endpoint:** `GET /api/schedule/progress/today`

**Description:** Get tasks scheduled for today.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/schedule/progress/today?schedule_id=schedule_student123_1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
[
  {
    "topic": "Calculus",
    "subject": "Mathematics",
    "estimated_hours": 2.5,
    "subtopics": ["Limits", "Continuity", "Differentiability"],
    "resources": [
      {
        "type": "video",
        "title": "Calculus Basics",
        "url": "https://example.com/calculus-basics",
        "duration_minutes": 45
      },
      {
        "type": "practice",
        "title": "Differentiation Problems",
        "url": "https://example.com/practice",
        "questions_count": 20
      }
    ],
    "goals": [
      "Understand limit concepts",
      "Practice differentiation problems",
      "Complete 15 practice questions"
    ],
    "priority": "high",
    "difficulty": "medium",
    "prerequisites": ["Algebra basics"],
    "learning_objectives": [
      "Define limits and continuity",
      "Apply differentiation rules",
      "Solve related rates problems"
    ]
  },
  {
    "topic": "Thermodynamics",
    "subject": "Physics",
    "estimated_hours": 2.5,
    "subtopics": [...],
    "resources": [...],
    "goals": [...],
    "priority": "medium",
    "difficulty": "hard"
  }
]
```

#### Returns for each topic
- Topic and subject information
- Estimated study hours
- Subtopics to cover
- Recommended resources (videos, practice, readings)
- Daily learning goals
- Priority and difficulty level
- Prerequisites and learning objectives

#### Use Cases
- Daily task view
- Study planner
- Mobile app home screen

#### Error Scenarios
- **404 Not Found:** Schedule not found
- **500 Internal Server Error:** Failed to get today's tasks

---

## Testing Workflows

### Complete Schedule Management Workflow

1. **Generate Schedule**
   ```bash
   curl -X POST "/api/schedule/generate" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"student_id": "student_123", "analytics_id": "analytics_456", ...}'
   ```

2. **Get Active Schedule**
   ```bash
   curl -X GET "/api/schedule/student/student_123?status=active" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **Update Daily Progress**
   ```bash
   curl -X POST "/api/schedule/progress/update" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"schedule_id": "...", "day_number": 1, ...}'
   ```

4. **Get Progress Summary**
   ```bash
   curl -X GET "/api/schedule/progress/{schedule_id}" \
     -H "Authorization: Bearer TOKEN"
   ```

5. **Get Today's Tasks**
   ```bash
   curl -X GET "/api/schedule/progress/today?schedule_id=..." \
     -H "Authorization: Bearer TOKEN"
   ```

6. **Regenerate Schedule (if needed)**
   ```bash
   curl -X POST "/api/schedule/{schedule_id}/regenerate" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"current_day": 15}'
   ```

---

## AI-Powered Features

### Schedule Generation Process
1. **Performance Analysis**: Analyzes student's test performance
2. **Weak Area Identification**: Identifies topics needing focus
3. **Time Optimization**: Balances study time across subjects
4. **Adaptive Planning**: Adjusts difficulty and pacing
5. **Resource Matching**: Recommends appropriate learning materials

### Intelligent Rescheduling
- Monitors progress patterns
- Detects learning pace issues
- Automatically suggests adjustments
- Maintains exam preparation goals

### Personalization Factors
- Learning speed and retention
- Subject strengths and weaknesses
- Preferred study times
- Historical performance data
- Exam weightage distribution

---

## Common Issues and Solutions

### 1. Schedule Generation Failed
**Problem:** Getting 500 error when generating schedule
**Solution:** 
- Verify analytics_id has test data
- Check exam_date is valid and in future
- Ensure daily_study_hours is realistic (2-8 hours)

### 2. Progress Update Failed
**Problem:** Getting 400 error when updating progress
**Solution:** 
- Verify day_number exists in schedule
- Check completion_percentage is valid (0-100)
- Ensure topics_completed format is correct

### 3. Schedule Not Found
**Problem:** Getting 404 errors
**Solution:** 
- Verify schedule_id is correct
- Check student has permission to access schedule
- Ensure schedule hasn't been deleted

### 4. Rescheduling Issues
**Problem:** Regeneration not working as expected
**Solution:** 
- Check current_day is valid and not completed
- Verify schedule is in 'active' status
- Ensure enough days remain before exam

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing the Schedule Router in Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Schedule Router uses Gemini AI for personalized schedule generation
- Schedules are based on student performance analytics and exam patterns
- AI considers weak areas, study pace, and exam weightage
- Progress tracking triggers adaptive rescheduling
- Schedules support JEE_MAIN, JEE_ADVANCED, and NEET exams

**Question:** Can you help me debug this issue by:
1. Analyzing the AI generation request and response
2. Checking if the schedule parameters are valid
3. Identifying common AI generation issues
4. Suggesting specific fixes or debugging steps

**Additional Information:**
- Student ID: [STUDENT_ID]
- Analytics ID: [ANALYTICS_ID]
- Exam Type: [EXAM_TYPE]
- Exam Date: [EXAM_DATE]
- [Add any relevant logs or observations]
```

---

## Related Models and Services

### Models
- `models.schedule_models.Schedule`
- `models.schedule_models.ScheduleRequest`
- `models.schedule_models.ProgressUpdate`
- `models.schedule_models.ScheduleStatus`
- `models.schedule_models.DailyTopic`

### Services
- `services.schedule_service.ScheduleService`
- `services.adaptive_scheduler.AdaptiveScheduler`
- `services.progress_tracker.ProgressTracker`

### Authentication
- `middleware.auth_middleware.get_current_user`

---

## Performance Considerations

1. **AI Generation:** Schedule generation takes 3-5 seconds
2. **Progress Updates:** Optimized for frequent updates
3. **Caching:** Schedule data cached for 1 hour
4. **Batch Operations:** Progress updates support batch processing
5. **Background Tasks:** AI generation runs in background

---

## Security Notes

1. **Access Control:** Students can only access their own schedules
2. **Data Validation:** All inputs validated before processing
3. **AI Safety:** Gemini AI responses are validated and filtered
4. **Progress Integrity:** Progress updates are atomic and audited
5. **Privacy:** Performance data anonymized for AI processing

---

## Testing Best Practices

1. **AI Testing:** Test with various student performance profiles
2. **Edge Cases:** Test with exam dates very close and far
3. **Progress Scenarios:** Test all progress update scenarios
4. **Rescheduling**: Test regeneration at different schedule stages
5. **Performance**: Test with large schedules (100+ days)