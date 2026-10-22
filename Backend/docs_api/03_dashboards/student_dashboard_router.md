# Student Dashboard Router Testing Documentation

## Overview

The student dashboard router provides endpoints for students to access their daily study plans, practice modes, doubt resolution, bookmarks, and performance insights. It offers personalized learning experiences with AI-powered features.

## Endpoints

### GET /api/student/today/{student_id}

Get today's personalized study plan for a student.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/student/today/STUDENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/student/today/{{student_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `student_id`: `STUDENT_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "student_id": "student_123",
    "plan_date": "2024-01-15",
    "topics": [
        {
            "subject": "Physics",
            "topic": "Thermodynamics",
            "estimated_hours": 2.0,
            "priority": "high",
            "completed": false
        },
        {
            "subject": "Mathematics",
            "topic": "Integration",
            "estimated_hours": 1.5,
            "priority": "medium",
            "completed": false
        }
    ],
    "total_estimated_hours": 3.5,
    "pending_from_yesterday": [
        {
            "subject": "Chemistry",
            "topic": "Organic Chemistry",
            "reason": "incomplete"
        }
    ],
    "current_streak": 5,
    "completion_percentage": 0.0,
    "motivational_message": "Great job on your 5-day streak! Keep it up!"
}
```

#### Error Scenarios

**404 Not Found - Student Not Found:**
```json
{
    "detail": "Student profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get today's plan. Please try again later."
}
```

#### Troubleshooting

1. **Student ID Required:**
   - Must provide valid `student_id` in URL path
   - Student must exist in the system
   - Student must belong to authenticated user

2. **Plan Generation:**
   - Based on weak areas and upcoming tasks
   - Includes motivational messages for engagement
   - Estimated hours calculated based on topic difficulty

3. **Streak Tracking:**
   - Consecutive days of activity
   - Resets when day is missed
   - Used for motivation and gamification

4. **Priority System:**
   - High priority for urgent topics
   - Medium for regular study items
   - Low for review and reinforcement

---

### GET /api/student/topic/{topic_id}/resources

Get curated learning resources for a specific topic.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/student/topic/TOPIC_ID/resources" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/student/topic/{{topic_id}}/resources`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `topic_id`: `TOPIC_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "topic_id": "topic_123",
    "topic_name": "Thermodynamics",
    "videos": [
        {
            "title": "Laws of Thermodynamics",
            "url": "https://youtube.com/watch?v=...",
            "duration": "15:30"
        },
        {
            "title": "Heat Engines",
            "url": "https://youtube.com/watch?v=...",
            "duration": "12:45"
        }
    ],
    "formula_sheets": [
        {
            "title": "Thermodynamics Formulas",
            "url": "https://example.com/formulas.pdf"
        }
    ],
    "revision_notes": [
        {
            "title": "Quick Revision - Thermodynamics",
            "content": "Key concepts and formulas..."
        }
    ],
    "reference_links": [
        {
            "title": "NCERT Chapter",
            "url": "https://ncert.nic.in/..."
        }
    ]
}
```

#### Error Scenarios

**404 Not Found - Topic Not Found:**
```json
{
    "detail": "Topic resources not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get topic resources. Please try again later."
}
```

#### Troubleshooting

1. **Topic ID Required:**
   - Must provide valid `topic_id` in URL path
   - Topic must exist in the system
   - Resources are curated based on subject and difficulty

2. **Resource Organization:**
   - Videos: Educational content with duration information
   - Formula Sheets: Reference materials for quick access
   - Revision Notes: Key concepts and summaries
   - Reference Links: External resources for deeper study

---

### POST /api/student/practice/quick

Generate a quick practice session based on duration and focus area.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/student/practice/quick" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "duration_minutes": 15,
    "focus": "weak_topics",
    "difficulty": "medium"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/student/practice/quick`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "duration_minutes": 15,
    "focus": "weak_topics",
    "difficulty": "medium"
}
```

#### Request Examples

**Valid Request - Weak Topics:**
```json
{
    "duration_minutes": 20,
    "focus": "weak_topics",
    "difficulty": "easy"
}
```

**Valid Request - Specific Topic:**
```json
{
    "duration_minutes": 25,
    "focus": "specific_topic",
    "specific_topic": "Calculus",
    "difficulty": "hard"
}
```

**Valid Request - Revision:**
```json
{
    "duration_minutes": 30,
    "focus": "revision",
    "difficulty": "medium"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "practice_id": "practice_abc123",
    "questions": [
        {
            "question": "What is the first law of thermodynamics?",
            "options": ["Energy cannot be created or destroyed", "Matter is conserved", "Entropy always increases"],
            "correct_answer": 0
        },
        {
            "question": "Which process is most efficient for heat transfer?",
            "options": ["Conduction", "Convection", "Radiation"],
            "correct_answer": 1
        }
    ],
    "total_questions": 2,
    "estimated_duration": 15,
    "focus_area": "Thermodynamics",
    "difficulty": "medium"
}
```

#### Error Scenarios

**400 Bad Request - Invalid Duration:**
```json
{
    "detail": "Duration must be between 5 and 60 minutes"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to generate quick practice. Please try again later."
}
```

#### Troubleshooting

1. **Duration Limits:**
   - Minimum: 5 minutes
   - Maximum: 60 minutes
   - Used for focused practice sessions

2. **Focus Areas:**
   - `weak_topics`: Practice areas where student struggles
   - `revision`: Review of previously studied topics
   - `random`: Mixed questions from various topics
   - `specific_topic`: Practice on particular subject/topic

3. **Difficulty Levels:**
   - `easy`: Foundational concepts
   - `medium`: Application and problem-solving
   - `hard`: Complex multi-step problems

4. **Question Generation:**
   - Questions adapt to focus area and difficulty
   - Multiple choice and numerical problems
   - AI-generated based on curriculum and performance

---

### POST /api/student/doubts

Create a doubt/question for later explanation.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/student/doubts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "subject": "Physics",
    "topic": "Thermodynamics",
    "doubt_text": "I don't understand why entropy increases in irreversible processes"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/student/doubts`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "subject": "Physics",
    "topic": "Thermodynamics",
    "doubt_text": "I don't understand why entropy increases in irreversible processes"
}
```

#### Request Examples

**Valid Request - With Question ID:**
```json
{
    "subject": "Physics",
    "topic": "Thermodynamics",
    "question_id": "q_456",
    "doubt_text": "Can you explain the second law of thermodynamics?"
}
```

**Invalid Request Examples:**
```json
// Too short doubt text
{
    "doubt_text": "Help"
}

// Missing required fields
{
    "subject": "Physics"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "doubt_id": "doubt_abc123",
    "student_id": "student_123",
    "subject": "Physics",
    "topic": "Thermodynamics",
    "doubt_text": "I don't understand why entropy increases in irreversible processes",
    "status": "open",
    "created_at": "2024-01-15T14:30:00Z"
}
```

#### Error Scenarios

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Doubt text must be at least 10 characters"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to create doubt. Please try again later."
}
```

#### Troubleshooting

1. **Doubt Text Requirements:**
   - Minimum 10 characters
   - Maximum 500 characters
   - Should clearly describe the confusion

2. **Question Association:**
   - Can reference specific question from previous tests
   - Helps provide context for AI explanation

3. **AI Explanation:**
   - Generated using AI service
   - Provides detailed explanation with examples
   - Includes related concepts and similar questions

---

### GET /api/student/doubts/{doubt_id}/explanation

Get AI-generated detailed explanation for a doubt.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/student/doubts/DOUBT_ID/explanation" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/student/doubts/{{doubt_id}}/explanation`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `doubt_id`: `DOUBT_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "doubt_id": "doubt_abc123",
    "explanation": "Entropy increases in irreversible processes because...",
    "key_concepts": ["Second Law of Thermodynamics", "Entropy", "Irreversibility"],
    "examples": [
        "Example 1: Heat transfer from hot to cold object",
        "Example 2: Gas expansion in a container"
    ],
    "similar_questions": []
}
```

#### Error Scenarios

**404 Not Found - Doubt Not Found:**
```json
{
    "detail": "Doubt explanation not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get doubt explanation. Please try again later."
}
```

#### Troubleshooting

1. **Doubt Resolution:**
   - Status changes from "open" → "explained" → "understood"
   - Students can mark doubts as resolved
   - Helps track learning progress

2. **AI Integration:**
   - Uses AI service for detailed explanations
   - Provides educational value beyond simple answers
   - Includes related concepts and examples

---

### GET /api/student/revision/due

Get topics due for revision based on spaced repetition.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/student/revision/due/STUDENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/student/revision/due/{{student_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `student_id`: `STUDENT_ID`

#### Expected Output

**Success Response (200):**
```json
[
    {
        "topic_id": "topic_123",
        "topic_name": "Thermodynamics",
        "subject": "Physics",
        "last_studied": "2024-01-08",
        "due_date": "2024-01-15",
        "priority": "high",
        "estimated_time": 1.5
    },
    {
        "topic_id": "topic_456",
        "topic_name": "Calculus",
        "subject": "Mathematics",
        "last_studied": "2024-01-10",
        "due_date": "2024-01-20",
        "priority": "medium",
        "estimated_time": 2.0
    }
]
```

#### Error Scenarios

**404 Not Found - Student Not Found:**
```json
{
    "detail": "Student profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get revision items. Please try again later."
}
```

#### Troubleshooting

1. **Spaced Repetition Algorithm:**
   - Topics scheduled based on forgetting curve
   - Priority based on performance and difficulty
   - Time estimates based on historical data

2. **Priority Levels:**
   - `high`: Critical topics needing immediate attention
   - `medium`: Important topics for regular review
   - `low`: Topics for occasional reinforcement

3. **Revision Tracking:**
   - Helps prevent forgetting of important concepts
   - Encourages distributed practice over time
   - Based on cognitive science principles

---

### POST /api/student/revision/mark-complete/{topic_id}

Mark a topic revision as complete.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/student/revision/mark-complete/TOPIC_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/student/revision/mark-complete/{{topic_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `topic_id`: `TOPIC_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "success": true,
    "message": "Revision marked complete for topic: TOPIC_ID"
}
```

#### Error Scenarios

**404 Not Found - Topic Not Found:**
```json
{
    "detail": "Topic not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to mark revision complete. Please try again later."
}
```

#### Troubleshooting

1. **Completion Tracking:**
   - Updates revision schedule for future planning
   - Helps optimize study time allocation
   - Provides data for performance analytics

---

### POST /api/student/bookmarks

Create a bookmark for later reference.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/student/bookmarks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "item_type": "question",
    "item_id": "q_456",
    "title": "Challenging thermodynamics problem",
    "subject": "Physics",
    "tags": ["difficult", "important"]
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/student/bookmarks`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "item_type": "question",
    "item_id": "q_456",
    "title": "Challenging thermodynamics problem",
    "subject": "Physics",
    "tags": ["difficult", "important"]
}
```

#### Request Examples

**Valid Request - Resource Bookmark:**
```json
{
    "item_type": "resource",
    "item_id": "formula_sheet_123",
    "title": "Thermodynamics formulas",
    "subject": "Physics",
    "url": "https://example.com/formulas.pdf"
}
```

**Valid Request - Note Bookmark:**
```json
{
    "item_type": "note",
    "item_id": "note_456",
    "title": "Key concepts for thermodynamics",
    "content": "Remember the three laws and key formulas..."
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "bookmark_id": "bookmark_abc123",
    "student_id": "student_123",
    "item_type": "question",
    "title": "Challenging thermodynamics problem",
    "subject": "Physics",
    "tags": ["difficult", "important"],
    "created_at": "2024-01-15T14:30:00Z"
}
```

#### Error Scenarios

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Title must be at least 3 characters"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to create bookmark. Please try again later."
}
```

#### Troubleshooting

1. **Bookmark Types:**
   - `question`: Specific problems for later review
   - `resource`: Reference materials and study aids
   - `note`: Personal summaries and insights

2. **Tag System:**
   - Custom tags for organization
   - Helps categorize and filter bookmarks
   - Supports multiple tags per bookmark

---

### GET /api/student/bookmarks

Get all bookmarks for a student.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/student/bookmarks?student_id=STUDENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/student/bookmarks`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `student_id`: `STUDENT_ID`

#### Expected Output

**Success Response (200):**
```json
[
    {
        "bookmark_id": "bookmark_abc123",
        "student_id": "student_123",
        "item_type": "question",
        "title": "Challenging thermodynamics problem",
        "subject": "Physics",
        "tags": ["difficult", "important"],
        "created_at": "2024-01-15T14:30:00Z"
    },
    {
        "bookmark_id": "bookmark_def456",
        "student_id": "student_123",
        "item_type": "resource",
        "title": "Thermodynamics formulas",
        "url": "https://example.com/formulas.pdf",
        "created_at": "2024-01-10T08:00:00Z"
    }
]
```

#### Error Scenarios

**404 Not Found - Student Not Found:**
```json
{
    "detail": "Student profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get bookmarks. Please try again later."
}
```

#### Troubleshooting

1. **Bookmark Organization:**
   - Bookmarks are returned in reverse chronological order
   - Each bookmark includes creation timestamp
   - Supports filtering by tags and item types

---

### DELETE /api/student/bookmarks/{bookmark_id}

Delete a bookmark.

#### Testing Steps

1. **Using curl:**
```bash
curl -X DELETE "http://localhost:8000/api/student/bookmarks/BOOKMARK_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: DELETE
- URL: `{{base_url}}/api/student/bookmarks/{{bookmark_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `bookmark_id`: `BOOKMARK_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "success": true,
    "message": "Bookmark deleted: BOOKMARK_ID"
}
```

#### Error Scenarios

**404 Not Found - Bookmark Not Found:**
```json
{
    "detail": "Bookmark not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to delete bookmark. Please try again later."
}
```

#### Troubleshooting

1. **Permanent Deletion:**
   - Bookmark cannot be recovered after deletion
   - Confirmation should be shown before deletion
   - Student should be informed of permanent action

---

### GET /api/student/insights/{student_id}

Get AI-powered performance insights and recommendations.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/student/insights/STUDENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/student/insights/{{student_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `student_id`: `STUDENT_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "student_id": "student_123",
    "best_time_of_day": "Morning (9 AM - 12 PM)",
    "average_time_per_question": {
        "Physics": 2.5,
        "Chemistry": 2.2,
        "Mathematics": 3.0
    },
    "accuracy_trend": "improving",
    "accuracy_change": 5.2,
    "predicted_score": 78.5,
    "confidence_interval": {"lower": 75.0, "upper": 82.0},
    "strengths": ["Calculus", "Organic Chemistry"],
    "weaknesses": ["Thermodynamics", "Electromagnetism"],
    "recommendations": [
        "Focus more on Thermodynamics",
        "Practice more numerical problems in Physics"
    ]
}
```

#### Error Scenarios

**404 Not Found - Student Not Found:**
```json
{
    "detail": "Student profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get performance insights. Please try again later."
}
```

#### Troubleshooting

1. **Performance Analytics:**
   - Data aggregated from multiple sources
   - AI-powered insights and recommendations
   - Percentile calculations and peer comparisons
   - Identifies strengths and weaknesses

2. **Insight Generation:**
   - Uses AI service for analysis
   - Provides actionable recommendations
   - Updates based on recent performance trends

---

### GET /api/student/compare/percentile

Get anonymous peer comparison and percentile ranking.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/student/compare/percentile?student_id=STUDENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/student/compare/percentile`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `student_id`: `STUDENT_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "student_id": "student_123",
    "overall_percentile": 78.5,
    "subject_percentiles": {
        "Physics": 75.0,
        "Chemistry": 82.0,
        "Mathematics": 79.0
    },
    "rank_range": "2000-2500",
    "total_students": 10000,
    "performance_category": "top_25"
}
```

#### Error Scenarios

**404 Not Found - Student Not Found:**
```json
{
    "detail": "Student profile not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to get peer comparison. Please try again later."
}
```

#### Troubleshooting

1. **Percentile Calculations:**
   - Based on performance across all students
   - Anonymous comparison for privacy
   - Updates periodically as new data comes in
   - Used for motivation and goal setting

## Common Issues Across All Endpoints

### Authentication Requirements
- All endpoints require student authentication
- Use `Authorization: Bearer <token>` header
- Student must be logged in with valid session

### AI Integration
- AI-powered explanations for doubts
- Performance insights and recommendations
- Personalized study plans and content
- Adaptive difficulty based on performance

### Data Aggregation
- Performance data from multiple sources
- Study time tracking and attendance
- Goal progress and completion tracking

### Gamification Elements
- Streak tracking for engagement
- Achievement badges and notifications
- Progress percentages and completion metrics

## AI Troubleshooting Prompt

```
I'm testing the Mentor AI student dashboard router endpoint [INSERT_ENDPOINT] and encountering the following error:

[Insert error message here]

My request payload is:
```json
[Insert request payload here]
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Endpoint: [GET /api/student/today/{student_id}, GET /api/student/topic/{topic_id}/resources, POST /api/student/practice/quick, POST /api/student/doubts, GET /api/student/doubts/{doubt_id}/explanation, GET /api/student/revision/due, POST /api/student/revision/mark-complete/{topic_id}, POST /api/student/bookmarks, GET /api/student/bookmarks, DELETE /api/student/bookmarks/{bookmark_id}, GET /api/student/insights/{student_id}, or GET /api/student/compare/percentile]
- Authentication token: [Valid/Invalid/Missing]
- Student ID: [If applicable]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the student dashboard flow in services/student_dashboard_service.py
2. Checking if the request format matches the appropriate model in models/student_models.py
3. Verifying the AI integration for doubt explanations and performance insights
4. Checking the practice session generation logic
5. Verifying the bookmark management system
6. Verifying the revision tracking algorithm
7. Providing specific steps to fix the issue

Context: This endpoint provides comprehensive student dashboard functionality for the Mentor AI EdTech Platform, including personalized study plans, AI-powered doubt resolution, performance analytics, and gamification elements.