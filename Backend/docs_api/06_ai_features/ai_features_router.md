# AI Features Router API Testing Guide

## Overview

The AI Features router provides endpoints for AI-powered educational features including AI tutor chat, smart recommendations, exam readiness assessment, and mistake pattern analysis. These features use Gemini AI to provide personalized learning assistance.

**Base URL:** `http://localhost:8000/api/ai`

## Authentication

All endpoints require JWT authentication:
```bash
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Ask AI Tutor

**Endpoint:** `POST /api/ai/tutor/ask`

Ask a question to the AI tutor and get detailed explanation with examples and related topics.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/ai/tutor/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "student_id": "student_123",
    "question": "Can you explain the second law of thermodynamics?",
    "subject": "Physics",
    "topic": "Thermodynamics",
    "include_examples": true
  }'
```

#### Request Example (Postman):
```json
{
  "student_id": "student_123",
  "question": "Can you explain the second law of thermodynamics?",
  "subject": "Physics",
  "topic": "Thermodynamics",
  "include_examples": true
}
```

#### Expected Response (200 OK):
```json
{
  "message_id": "msg_1701085800123",
  "answer": "The second law of thermodynamics states that the total entropy of an isolated system can never decrease over time. In simple terms, heat naturally flows from hot to cold, and processes tend to move towards disorder. This law introduces the concept of entropy as a measure of disorder in a system.",
  "key_points": [
    "Entropy always increases in isolated systems",
    "Heat flows from hot to cold spontaneously",
    "Impossible to convert all heat to work (100% efficiency)"
  ],
  "examples": [
    "Ice melting in warm water - heat flows from water to ice",
    "Gas expanding into vacuum - molecules spread out (increase disorder)",
    "Coffee cooling down - heat dissipates to surroundings"
  ],
  "related_topics": ["Entropy", "Heat Engines", "Carnot Cycle", "Reversible Processes"],
  "practice_questions": [
    {
      "question": "What happens to entropy in an irreversible process?",
      "options": ["Decreases", "Remains constant", "Increases", "Cannot determine"],
      "answer": "Increases"
    }
  ],
  "resources": [
    {
      "title": "Thermodynamics Video Lecture",
      "url": "https://youtube.com/watch?v=example",
      "type": "video"
    }
  ]
}
```

#### Error Scenarios:

**400 Bad Request - Invalid question:**
```json
{
  "detail": "Question must be at least 5 characters long"
}
```

**401 Unauthorized - Invalid token:**
```json
{
  "detail": "Could not validate credentials"
}
```

**500 Internal Server Error - AI generation failed:**
```json
{
  "detail": "Failed to generate AI tutor response"
}
```

---

### 2. Get Chat History

**Endpoint:** `GET /api/ai/tutor/history/{student_id}`

Get chat history with AI tutor for a specific student.

#### Request Example (curl):
```bash
curl -X GET "http://localhost:8000/api/ai/tutor/history/student_123?limit=50" \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "student_id": "student_123",
  "messages": [
    {
      "message_id": "msg_1701085800123",
      "role": "user",
      "content": "Can you explain the second law of thermodynamics?",
      "timestamp": "2024-11-27T10:30:00Z",
      "context": {
        "subject": "Physics",
        "topic": "Thermodynamics"
      }
    },
    {
      "message_id": "msg_1701085800156",
      "role": "assistant",
      "content": "The second law of thermodynamics states that...",
      "timestamp": "2024-11-27T10:30:56Z"
    }
  ],
  "total_messages": 25
}
```

#### Error Scenarios:

**400 Bad Request - Invalid limit:**
```json
{
  "detail": "Limit must be between 1 and 100"
}
```

**404 Not Found - Student not found:**
```json
{
  "detail": "Student not found"
}
```

---

### 3. Get Topic Recommendations

**Endpoint:** `GET /api/ai/recommend/topics/{student_id}`

Get AI-recommended topics to study based on student's performance data.

#### Request Example (curl):
```bash
curl -X GET "http://localhost:8000/api/ai/recommend/topics/student_123?limit=5" \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
[
  {
    "topic_id": "topic_123",
    "topic_name": "Thermodynamics",
    "subject": "Physics",
    "priority": "high",
    "reason": "Low accuracy (45%) on high-weightage topic (8%)",
    "estimated_hours": 6.0,
    "current_accuracy": 45.0,
    "target_accuracy": 75.0,
    "weightage": 8.0
  },
  {
    "topic_id": "topic_124",
    "topic_name": "Organic Chemistry",
    "subject": "Chemistry",
    "priority": "high",
    "reason": "Critical topic with moderate performance (62%)",
    "estimated_hours": 8.0,
    "current_accuracy": 62.0,
    "target_accuracy": 80.0,
    "weightage": 12.0
  },
  {
    "topic_id": "topic_125",
    "topic_name": "Calculus",
    "subject": "Mathematics",
    "priority": "medium",
    "reason": "Foundation topic needing improvement (70%)",
    "estimated_hours": 5.0,
    "current_accuracy": 70.0,
    "target_accuracy": 85.0,
    "weightage": 10.0
  }
]
```

#### Error Scenarios:

**400 Bad Request - Invalid limit:**
```json
{
  "detail": "Limit must be between 1 and 20"
}
```

**404 Not Found - No performance data:**
```json
{
  "detail": "No performance data available for recommendations"
}
```

---

### 4. Get Resource Recommendations

**Endpoint:** `GET /api/ai/recommend/resources/{topic_id}`

Get AI-recommended learning resources for a specific topic.

#### Request Example (curl):
```bash
curl -X GET "http://localhost:8000/api/ai/recommend/resources/topic_123?limit=5" \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
[
  {
    "resource_id": "res_123",
    "title": "Thermodynamics Explained",
    "type": "video",
    "url": "https://youtube.com/watch?v=example",
    "description": "Comprehensive explanation of thermodynamics laws",
    "difficulty": "intermediate",
    "duration": "25:30",
    "rating": 4.5,
    "relevance_score": 0.92
  },
  {
    "resource_id": "res_124",
    "title": "Thermodynamics Practice Problems",
    "type": "practice",
    "url": "https://example.com/practice",
    "description": "50 practice problems with solutions",
    "difficulty": "intermediate",
    "duration": "2 hours",
    "rating": 4.7,
    "relevance_score": 0.88
  },
  {
    "resource_id": "res_125",
    "title": "Thermodynamics Notes",
    "type": "notes",
    "url": "https://example.com/notes",
    "description": "Concise notes covering all key concepts",
    "difficulty": "beginner",
    "duration": "30 min read",
    "rating": 4.3,
    "relevance_score": 0.85
  }
]
```

#### Error Scenarios:

**400 Bad Request - Invalid limit:**
```json
{
  "detail": "Limit must be between 1 and 20"
}
```

**404 Not Found - Topic not found:**
```json
{
  "detail": "Topic not found"
}
```

---

### 5. Get Exam Readiness

**Endpoint:** `GET /api/ai/readiness/{student_id}`

Get comprehensive exam readiness assessment with AI-powered predictions.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/ai/readiness/student_123 \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "student_id": "student_123",
  "overall_readiness": 72.5,
  "readiness_level": "good",
  "subject_readiness": {
    "Physics": 68.0,
    "Chemistry": 75.0,
    "Mathematics": 74.5
  },
  "topic_coverage": 78.0,
  "practice_score": 71.5,
  "consistency_score": 85.0,
  "predicted_rank_range": "2000-2500",
  "confidence": 78.0,
  "gaps": [
    {
      "subject": "Physics",
      "topic": "Thermodynamics",
      "severity": "high",
      "hours_needed": 6.0
    },
    {
      "subject": "Chemistry",
      "topic": "Electrochemistry",
      "severity": "medium",
      "hours_needed": 4.0
    }
  ],
  "recommendations": [
    "Focus 6 more hours on Thermodynamics",
    "Take 2 more full-length practice tests",
    "Revise Organic Chemistry formulas",
    "Practice more numerical problems in Physics"
  ],
  "days_to_exam": 45
}
```

#### Error Scenarios:

**404 Not Found - Student not found:**
```json
{
  "detail": "Student not found"
}
```

**500 Internal Server Error - Insufficient data:**
```json
{
  "detail": "Insufficient data for readiness assessment"
}
```

---

### 6. Get Mistake Analysis

**Endpoint:** `GET /api/ai/analysis/mistakes/{student_id}`

Get AI-powered analysis of mistake patterns in student's performance.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/ai/analysis/mistakes/student_123 \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "student_id": "student_123",
  "total_mistakes": 34,
  "analysis_period": "Last 30 days",
  "patterns": [
    {
      "pattern_type": "calculation",
      "frequency": 12,
      "percentage": 35.3,
      "subjects_affected": ["Physics", "Chemistry"],
      "topics_affected": ["Thermodynamics", "Chemical Kinetics"],
      "examples": [
        {
          "question": "Q15",
          "mistake": "Decimal point error"
        }
      ],
      "impact": "high",
      "recommendation": "Double-check calculations and use calculator"
    },
    {
      "pattern_type": "conceptual",
      "frequency": 10,
      "percentage": 29.4,
      "subjects_affected": ["Physics"],
      "topics_affected": ["Electromagnetism", "Optics"],
      "examples": [
        {
          "question": "Q8",
          "mistake": "Misunderstood concept"
        }
      ],
      "impact": "high",
      "recommendation": "Review fundamental concepts and theory"
    },
    {
      "pattern_type": "silly",
      "frequency": 8,
      "percentage": 23.5,
      "subjects_affected": ["Mathematics", "Physics"],
      "topics_affected": ["Calculus", "Mechanics"],
      "examples": [
        {
          "question": "Q22",
          "mistake": "Misread question"
        }
      ],
      "impact": "medium",
      "recommendation": "Read questions carefully and highlight key terms"
    }
  ],
  "most_common_pattern": "calculation",
  "improvement_potential": 12.5,
  "priority_actions": [
    "Practice more calculation-heavy problems",
    "Use calculator for complex computations",
    "Review conceptual understanding of Thermodynamics",
    "Read questions more carefully"
  ],
  "subject_wise_mistakes": {
    "Physics": 15,
    "Chemistry": 10,
    "Mathematics": 9
  }
}
```

#### Error Scenarios:

**404 Not Found - Student not found:**
```json
{
  "detail": "Student not found"
}
```

**500 Internal Server Error - No mistake data:**
```json
{
  "detail": "No mistake data available for analysis"
}
```

## Testing Workflow

### Complete AI Features Testing

1. **Ask AI Tutor:**
   ```bash
   curl -X POST http://localhost:8000/api/ai/tutor/ask \
     -d '{"student_id":"student_123","question":"What is entropy?","subject":"Physics"}'
   ```

2. **Get Chat History:**
   ```bash
   curl -X GET "http://localhost:8000/api/ai/tutor/history/student_123?limit=10"
   ```

3. **Get Topic Recommendations:**
   ```bash
   curl -X GET "http://localhost:8000/api/ai/recommend/topics/student_123?limit=5"
   ```

4. **Get Resource Recommendations:**
   ```bash
   curl -X GET "http://localhost:8000/api/ai/recommend/resources/topic_123?limit=3"
   ```

5. **Get Exam Readiness:**
   ```bash
   curl -X GET http://localhost:8000/api/ai/readiness/student_123
   ```

6. **Get Mistake Analysis:**
   ```bash
   curl -X GET http://localhost:8000/api/ai/analysis/mistakes/student_123
   ```

## Troubleshooting

### Common Issues

1. **AI Tutor Not Responding:**
   - Check Gemini API key configuration
   - Verify network connectivity to Google services
   - Monitor API quota usage
   - Check question length and format

2. **Poor Recommendations:**
   - Verify student has sufficient performance data
   - Check if topics are covered in syllabus
   - Update student's recent test scores
   - Validate subject/topic mapping

3. **Readiness Assessment Issues:**
   - Ensure student has completed practice tests
   - Check if enough historical data exists
   - Verify exam date is set
   - Validate subject performance data

4. **Mistake Analysis Problems:**
   - Check if student has submitted test answers
   - Verify mistake tracking is enabled
   - Ensure sufficient mistake data (minimum 10 mistakes)
   - Check if mistake categories are properly classified

5. **Chat History Not Loading:**
   - Verify student ID is correct
   - Check if chat persistence is enabled
   - Ensure messages are being saved
   - Validate database connectivity

### AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT/Claude when debugging AI features issues:

```
I'm testing Mentor AI features system and encountering an issue. Please help me debug:

**System Context:**
- Mentor AI uses Gemini API for AI-powered educational features
- Features: AI tutor, recommendations, readiness assessment, mistake analysis
- Requires student performance data for personalized recommendations
- Supports JEE_MAIN, JEE_ADVANCED, NEET exam types

**Issue Details:**
- Endpoint: [POST/GET endpoint URL]
- Request payload: [Copy exact JSON request]
- Error response: [Copy exact error message]
- Expected behavior: [Describe what should happen]

**Environment:**
- Gemini API key: [Valid/Invalid/Expired]
- Student data: [Available/Insufficient/Missing]
- Testing mode: [Yes/No]
- Feature enabled: [Yes/No]

**Questions:**
1. What's causing this AI feature error based on the response?
2. How can I improve the quality of AI responses?
3. What additional data is needed for this feature?
4. Are there any workarounds for this issue?

Please provide specific steps to resolve this AI features issue.
```

## Reference Models

### Request Models

- **AITutorRequest** ([`models/ai_models.py`](models/ai_models.py:38))
  - `student_id`: str - Student identifier
  - `question`: str (min 5 chars) - Student's question
  - `subject`: Optional[str] - Subject context
  - `topic`: Optional[str] - Topic context
  - `include_examples`: bool - Include examples in response

### Response Models

- **AITutorResponse** ([`models/ai_models.py`](models/ai_models.py:60))
  - `message_id`: str - Message identifier
  - `answer`: str - AI tutor's answer
  - `key_points`: List[str] - Key points
  - `examples`: List[str] - Examples
  - `related_topics`: List[str] - Related topics
  - `practice_questions`: List[Dict] - Suggested questions
  - `resources`: List[Dict[str, str]] - Additional resources

- **ChatHistory** ([`models/ai_models.py`](models/ai_models.py:97))
  - `student_id`: str - Student identifier
  - `messages`: List[AITutorMessage] - Chat messages
  - `total_messages`: int - Total message count

- **TopicRecommendation** ([`models/ai_models.py`](models/ai_models.py:115))
  - `topic_id`: str - Topic identifier
  - `topic_name`: str - Topic name
  - `subject`: str - Subject
  - `priority`: Literal["critical", "high", "medium", "low"] - Priority level
  - `reason`: str - Reason for recommendation
  - `estimated_hours`: float - Study time needed
  - `current_accuracy`: float - Current performance
  - `target_accuracy`: float - Target performance
  - `weightage`: float - Exam weightage

- **ResourceRecommendation** ([`models/ai_models.py`](models/ai_models.py:148))
  - `resource_id`: str - Resource identifier
  - `title`: str - Resource title
  - `type`: Literal["video", "article", "practice", "notes", "book"] - Resource type
  - `url`: Optional[str] - Resource URL
  - `description`: str - Resource description
  - `difficulty`: Literal["beginner", "intermediate", "advanced"] - Difficulty level
  - `duration`: Optional[str] - Duration/length
  - `rating`: float (0-5) - Resource rating
  - `relevance_score`: float (0-1) - Relevance to student

- **ExamReadiness** ([`models/ai_models.py`](models/ai_models.py:184))
  - `student_id`: str - Student identifier
  - `overall_readiness`: float (0-100) - Overall readiness percentage
  - `readiness_level`: Literal["not_ready", "needs_work", "good", "excellent"] - Readiness level
  - `subject_readiness`: Dict[str, float] - Subject-wise readiness
  - `topic_coverage`: float (0-100) - Topic coverage percentage
  - `practice_score`: float (0-100) - Practice test average
  - `consistency_score`: float (0-100) - Study consistency
  - `predicted_rank_range`: str - Predicted exam rank
  - `confidence`: float (0-100) - Prediction confidence
  - `gaps`: List[Dict] - Knowledge gaps
  - `recommendations`: List[str] - Recommendations
  - `days_to_exam`: int - Days until exam

- **MistakeAnalysis** ([`models/ai_models.py`](models/ai_models.py:271))
  - `student_id`: str - Student identifier
  - `total_mistakes`: int - Total mistakes analyzed
  - `analysis_period`: str - Analysis period
  - `patterns`: List[MistakePattern] - Identified patterns
  - `most_common_pattern`: str - Most common mistake type
  - `improvement_potential`: float (0-100) - Score improvement potential
  - `priority_actions`: List[str] - Priority actions
  - `subject_wise_mistakes`: Dict[str, int] - Mistakes by subject

- **MistakePattern** ([`models/ai_models.py`](models/ai_models.py:238))
  - `pattern_type`: Literal["calculation", "conceptual", "silly", "time_management", "incomplete"]
  - `frequency`: int - Number of occurrences
  - `percentage`: float (0-100) - Percentage of total mistakes
  - `subjects_affected`: List[str] - Affected subjects
  - `topics_affected`: List[str] - Affected topics
  - `examples`: List[Dict[str, str]] - Example mistakes
  - `impact`: Literal["high", "medium", "low"] - Impact on score
  - `recommendation`: str - How to fix pattern

## Service Dependencies

- **Gemini API**: AI content generation and analysis
- **Student Performance Service**: Performance data retrieval
- **Chat Service**: Conversation history management
- **Recommendation Engine**: Personalized recommendations
- **Analytics Service**: Data analysis for insights

## AI Features Explained

1. **AI Tutor**: Natural language Q&A with detailed explanations
2. **Smart Recommendations**: Personalized topic and resource suggestions
3. **Exam Readiness**: Comprehensive assessment with predictions
4. **Mistake Analysis**: Pattern recognition and improvement suggestions
5. **Chat History**: Conversation persistence and context

## Performance Considerations

1. **Response Time**: AI generation typically takes 2-5 seconds
2. **Data Requirements**: Features need sufficient student data
3. **API Limits**: Gemini API quota and rate limits apply
4. **Caching**: Responses are cached for identical questions
5. **Personalization**: Quality improves with more student data

## Additional Resources

- [AI Features Service](services/ai_features_service.py)
- [Gemini Service](services/gemini_service.py)
- [Student Analytics Service](services/student_analytics_service.py)
- [Recommendation Engine](services/recommendation_engine.py)
- [Gemini API Documentation](https://ai.google.dev/docs)