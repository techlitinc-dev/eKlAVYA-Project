# Analytics Router API Documentation

## Overview

The Analytics Router provides endpoints for analytics generation and retrieval, including performance analysis, AI insights, and study recommendations. It processes test results to generate comprehensive reports with AI-powered insights.

## Base URL
```
/api/analytics
```

## Endpoints

### 1. Generate Analytics Report

**Endpoint:** `POST /api/analytics/generate`

**Description:** Generate a comprehensive analytics report for a student's test performance. This is an asynchronous operation that returns an analytics_id immediately and processes the report in the background.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/analytics/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test_123",
    "student_id": "student_456",
    "answers": {
      "1": "A",
      "2": "B",
      "3": "C",
      "4": "D",
      "5": "A"
    },
    "include_ai_insights": true,
    "use_cache": false
  }'
```

#### Request Body
- `test_id`: ID of the test to analyze (required)
- `student_id`: ID of the student (required)
- `answers`: Student's answers (can be dict or list of QuestionAnswer objects)
- `include_ai_insights`: Whether to include AI-generated insights (default: true)
- `use_cache`: Whether to use cached analytics if available (default: true)

#### Expected Response (202 Accepted)
```json
{
  "analytics_id": "analytics_test123_student456_1234567890",
  "status": "pending",
  "message": "Analytics generation in progress"
}
```

#### Process
1. Retrieves test questions from database
2. Calculates scores with exam-specific marking schemes
3. Analyzes performance patterns and identifies strengths/weaknesses
4. Generates AI-powered insights using Gemini Flash
5. Assembles complete report with visualizations
6. Stores report for future retrieval

#### Rate Limiting
- 10 requests per minute per user
- 100 requests per hour per IP

#### Error Scenarios
- **400 Bad Request:** Invalid request data
- **401 Unauthorized:** Authentication required
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Analytics generation failed

#### Troubleshooting
- Verify test_id exists and belongs to student
- Check answers format matches expected structure
- Ensure student has permission to access this test
- Wait for processing to complete before retrieving results

---

### 2. Get Analytics Report

**Endpoint:** `GET /api/analytics/{analytics_id}`

**Description:** Retrieve a complete analytics report by ID. Returns full analytics report including performance overview, subject analysis, topic-wise performance, AI-generated insights, visualizations, and priority topics.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/analytics/analytics_test123_student456_1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "analytics_id": "analytics_test123_student456_1234567890",
  "overview": {
    "student_id": "student_456",
    "test_id": "test_123",
    "exam_type": "JEE_MAIN",
    "test_date": "2024-01-15T10:00:00Z",
    "total_questions": 90,
    "total_score": 280,
    "total_marks": 360,
    "percentage": 77.78,
    "rank_prediction": "5000-6000",
    "time_taken": "2h 45m",
    "generated_at": "2024-01-15T11:30:00Z"
  },
  "subject_analysis": {
    "Physics": {
      "score": 96,
      "total_marks": 120,
      "percentage": 80.0,
      "questions_attempted": 30,
      "correct_answers": 24,
      "incorrect_answers": 6,
      "accuracy": 80.0,
      "performance_level": "excellent"
    },
    "Chemistry": {
      "score": 92,
      "total_marks": 120,
      "percentage": 76.67,
      "questions_attempted": 30,
      "correct_answers": 23,
      "incorrect_answers": 7,
      "accuracy": 76.67,
      "performance_level": "good"
    },
    "Mathematics": {
      "score": 92,
      "total_marks": 120,
      "percentage": 76.67,
      "questions_attempted": 30,
      "correct_answers": 23,
      "incorrect_answers": 7,
      "accuracy": 76.67,
      "performance_level": "good"
    }
  },
  "topic_wise_performance": [
    {
      "topic_id": "T01",
      "topic_name": "Kinematics",
      "subject": "Physics",
      "questions": 10,
      "correct": 8,
      "incorrect": 2,
      "accuracy": 80.0,
      "difficulty_level": "medium",
      "performance": "strong"
    },
    {
      "topic_id": "T05",
      "topic_name": "Thermodynamics",
      "subject": "Physics",
      "questions": 8,
      "correct": 2,
      "incorrect": 6,
      "accuracy": 25.0,
      "difficulty_level": "hard",
      "performance": "weak"
    }
  ],
  "ai_insights": {
    "strengths": [
      {
        "area": "Mechanics",
        "description": "Strong conceptual understanding and problem-solving skills",
        "evidence": "80% accuracy in Kinematics and Dynamics topics",
        "recommendation": "Continue practicing advanced problems"
      }
    ],
    "weaknesses": [
      {
        "area": "Thermodynamics",
        "description": "Difficulty with heat transfer and entropy concepts",
        "evidence": "25% accuracy, conceptual gaps in Second Law",
        "recommendation": "Focus on fundamental concepts and numerical problems"
      }
    ],
    "study_recommendations": [
      {
        "priority": "high",
        "topic": "Thermodynamics",
        "action": "Dedicated practice time with focus on numerical problems",
        "time_allocation": "2 hours daily for 2 weeks"
      },
      {
        "priority": "medium",
        "topic": "Optics",
        "action": "Review ray diagrams and lens formulas",
        "time_allocation": "1 hour daily for 1 week"
      }
    ],
    "improvement_suggestions": [
      "Practice time-bound questions",
      "Focus on conceptual clarity before numerical problems",
      "Revise formulas regularly",
      "Take mock tests weekly"
    ]
  },
  "visualizations": {
    "performance_chart": {
      "type": "radar",
      "data": {
        "Physics": 80.0,
        "Chemistry": 76.67,
        "Mathematics": 76.67
      }
    },
    "topic_performance": {
      "type": "bar",
      "data": [
        {"topic": "Kinematics", "accuracy": 80.0},
        {"topic": "Thermodynamics", "accuracy": 25.0}
      ]
    },
    "time_analysis": {
      "type": "timeline",
      "data": {
        "labels": ["Q1", "Q2", "Q3"],
        "datasets": [
          {
            "label": "Accuracy",
            "data": [75.0, 78.5, 77.8]
          }
        ]
      }
    }
  },
  "priority_topics": [
    {
      "topic_id": "T05",
      "topic_name": "Thermodynamics",
      "subject": "Physics",
      "priority": "HIGH",
      "reason": "Very low accuracy (25%) in high-weightage area",
      "recommended_hours": 15,
      "deadline": "2024-02-01"
    }
  ],
  "generated_at": "2024-01-15T11:30:00Z"
}
```

#### Report Components
- **Overview**: Summary statistics and predictions
- **Subject Analysis**: Performance breakdown by subject
- **Topic-wise Performance**: Detailed topic-level analysis
- **AI Insights**: Strengths, weaknesses, and recommendations
- **Visualizations**: Charts and graphs for dashboard
- **Priority Topics**: High-priority areas for focus

#### Error Scenarios
- **404 Not Found:** Analytics report not found
- **401 Unauthorized:** Access denied
- **500 Internal Server Error:** Failed to retrieve analytics

---

### 3. Get Student Analytics History

**Endpoint:** `GET /api/analytics/student/{student_id}`

**Description:** Retrieve analytics history for a student. Returns a list of analytics reports ordered by generation date (newest first).

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/analytics/student/student_456?limit=5&offset=0" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)
- `limit`: Number of reports to return (default: 10, max: 50)
- `offset`: Number of reports to skip (default: 0)

#### Expected Response (200 OK)
```json
[
  {
    "analytics_id": "analytics_test123_student456_1234567890",
    "overview": {
      "student_id": "student_456",
      "test_id": "test_123",
      "percentage": 77.78,
      "generated_at": "2024-01-15T11:30:00Z"
    },
    "subject_analysis": {...},
    "priority_topics": [...],
    "generated_at": "2024-01-15T11:30:00Z"
  },
  {
    "analytics_id": "analytics_test124_student456_1234567891",
    "overview": {
      "student_id": "student_456",
      "test_id": "test_124",
      "percentage": 82.5,
      "generated_at": "2024-01-08T14:20:00Z"
    },
    "subject_analysis": {...},
    "priority_topics": [...],
    "generated_at": "2024-01-08T14:20:00Z"
  }
]
```

#### Use Cases
- Track performance over time
- Compare different test performances
- Analyze improvement trends
- Review historical AI insights

#### Error Scenarios
- **401 Unauthorized:** Access denied
- **500 Internal Server Error:** Failed to retrieve student analytics

---

### 4. Get Analytics by Test

**Endpoint:** `GET /api/analytics/test/{test_id}`

**Description:** Retrieve all analytics reports for a specific test. Returns analytics reports for all students who took the specified test, ordered by generation date (newest first).

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/analytics/test/test_123?limit=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `test_id`: Test identifier (required)
- `limit`: Number of reports to return (default: 50, max: 100)

#### Expected Response (200 OK)
```json
[
  {
    "analytics_id": "analytics_test123_student456_1234567890",
    "overview": {
      "student_id": "student_456",
      "test_id": "test_123",
      "percentage": 77.78,
      "rank": 1245,
      "generated_at": "2024-01-15T11:30:00Z"
    }
  },
  {
    "analytics_id": "analytics_test125_student789_1234567892",
    "overview": {
      "student_id": "student_789",
      "test_id": "test_123",
      "percentage": 65.2,
      "rank": 3421,
      "generated_at": "2024-01-14T16:45:00Z"
    }
  }
]
```

#### Use Cases
- Compare performance across students for same test
- Analyze test difficulty and average scores
- Identify top performers and improvement areas
- Generate test-level insights

#### Error Scenarios
- **401 Unauthorized:** Access denied
- **404 Not Found:** No analytics found for test
- **500 Internal Server Error:** Failed to retrieve test analytics

---

### 5. Get AI Insights Only

**Endpoint:** `GET /api/analytics/{analytics_id}/insights`

**Description:** Extract and return only AI-generated insights from an analytics report. Provides quick access to AI-powered analysis without the overhead of complete report.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/analytics/analytics_test123_student456_1234567890/insights" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "analytics_id": "analytics_test123_student456_1234567890",
  "strengths": [
    {
      "area": "Mechanics",
      "description": "Strong conceptual understanding and problem-solving skills",
      "evidence": "80% accuracy in Kinematics and Dynamics topics",
      "recommendation": "Continue practicing advanced problems",
      "confidence_score": 85.5
    }
  ],
  "weaknesses": [
    {
      "area": "Thermodynamics",
      "description": "Difficulty with heat transfer and entropy concepts",
      "evidence": "25% accuracy, conceptual gaps in Second Law",
      "recommendation": "Focus on fundamental concepts and numerical problems",
      "urgency_score": 78.2
    }
  ],
  "study_recommendations": [
    {
      "priority": "high",
      "topic": "Thermodynamics",
      "action": "Dedicated practice time with focus on numerical problems",
      "time_allocation": "2 hours daily for 2 weeks",
      "expected_improvement": "+15% accuracy"
    },
    {
      "priority": "medium",
      "topic": "Optics",
      "action": "Review ray diagrams and lens formulas",
      "time_allocation": "1 hour daily for 1 week",
      "expected_improvement": "+8% accuracy"
    }
  ],
  "improvement_suggestions": [
    "Practice time-bound questions",
    "Focus on conceptual clarity before numerical problems",
    "Revise formulas regularly",
    "Take mock tests weekly"
  ],
  "learning_style_analysis": {
    "preferred_style": "visual",
    "recommended_approach": "Use diagrams and visualizations for Physics concepts",
    "effectiveness_score": 72.3
  },
  "generated_at": "2024-01-15T11:30:00Z"
}
```

#### AI Insights Features
- **Strengths Analysis**: Areas of high performance
- **Weaknesses Detection**: Topics needing improvement
- **Study Recommendations**: Personalized action plans
- **Learning Style**: Adapted approach suggestions
- **Confidence Scores**: Quantified assessment certainty

#### Error Scenarios
- **404 Not Found:** Analytics report not found
- **404 Not Found:** No AI insights available for analytics
- **401 Unauthorized:** Access denied
- **500 Internal Server Error:** Failed to retrieve insights

---

### 6. Get Weak Topics

**Endpoint:** `GET /api/analytics/{analytics_id}/weak-topics`

**Description:** Extract and return only high-priority weak topics from an analytics report. Provides quick access to most critical topics that need immediate attention.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/analytics/analytics_test123_student456_1234567890/weak-topics" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
[
  {
    "topic_id": "T05",
    "topic_name": "Thermodynamics",
    "subject": "Physics",
    "priority": "HIGH",
    "reason": "Very low accuracy (25%) in high-weightage area",
    "current_accuracy": 25.0,
    "target_accuracy": 70.0,
    "improvement_needed": "+45%",
    "recommended_hours": 15,
    "deadline": "2024-02-01",
    "resources": [
      {
        "type": "video",
        "title": "Thermodynamics Fundamentals",
        "url": "https://example.com/thermo-basics",
        "duration_minutes": 45
      },
      {
        "type": "practice",
        "title": "Thermodynamics Problem Set",
        "url": "https://example.com/thermo-practice",
        "questions_count": 50
      }
    ]
  },
  {
    "topic_id": "T08",
    "topic_name": "Organic Chemistry",
    "subject": "Chemistry",
    "priority": "HIGH",
    "reason": "Consistent poor performance across multiple tests",
    "current_accuracy": 42.5,
    "target_accuracy": 75.0,
    "improvement_needed": "+32.5%",
    "recommended_hours": 12,
    "deadline": "2024-01-25",
    "resources": [...]
  }
]
```

#### Priority Classification
- **HIGH**: Critical areas needing immediate attention
- **MEDIUM**: Important areas for improvement
- **LOW**: Areas for occasional review

#### Weak Topic Criteria
- Low accuracy scores
- Poor performance in high-weightage areas
- Consistent weakness across multiple tests
- Negative improvement trends

#### Error Scenarios
- **404 Not Found:** Analytics report not found
- **401 Unauthorized:** Access denied
- **500 Internal Server Error:** Failed to retrieve weak topics

---

## Testing Workflows

### Complete Analytics Workflow

1. **Generate Analytics**
   ```bash
   curl -X POST "/api/analytics/generate" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"test_id": "test_123", "student_id": "student_456", "answers": {...}}'
   ```

2. **Check Generation Status**
   ```bash
   # Poll for completion (this would be implemented in a real system)
   curl -X GET "/api/analytics/analytics_test123_student456_1234567890" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **Get Full Report**
   ```bash
   curl -X GET "/api/analytics/analytics_test123_student456_1234567890" \
     -H "Authorization: Bearer TOKEN"
   ```

4. **Get AI Insights Only**
   ```bash
   curl -X GET "/api/analytics/analytics_test123_student456_1234567890/insights" \
     -H "Authorization: Bearer TOKEN"
   ```

5. **Get Weak Topics**
   ```bash
   curl -X GET "/api/analytics/analytics_test123_student456_1234567890/weak-topics" \
     -H "Authorization: Bearer TOKEN"
   ```

6. **Get Student History**
   ```bash
   curl -X GET "/api/analytics/student/student_456?limit=10" \
     -H "Authorization: Bearer TOKEN"
   ```

---

## AI-Powered Analytics Features

### Performance Analysis
- **Pattern Recognition**: Identifies learning patterns and trends
- **Comparative Analysis**: Benchmarks against peer performance
- **Predictive Modeling**: Forecasts future performance
- **Gap Detection**: Identifies knowledge gaps

### Insight Generation
- **Strengths Assessment**: Analyzes areas of excellence
- **Weakness Identification**: Pinpoints improvement areas
- **Recommendation Engine**: Personalized study suggestions
- **Learning Style**: Adapts to individual preferences

### Visual Analytics
- **Performance Charts**: Radar, bar, and line charts
- **Topic Networks**: Visualizes topic relationships
- **Progress Timelines**: Time-series performance data
- **Comparative Analytics**: Peer and historical comparisons

---

## Common Issues and Solutions

### 1. Analytics Generation Timeout
**Problem:** Analytics generation taking too long or timing out
**Solution:** 
- Check if test data is complete and valid
- Verify AI service (Gemini) is available
- Consider reducing complexity with fewer test questions
- Use cache=false to force fresh generation

### 2. Missing AI Insights
**Problem:** AI insights not available in report
**Solution:** 
- Verify include_ai_insights was set to true
- Check if AI service is operational
- Ensure test has sufficient data for analysis
- Try regenerating with use_cache=false

### 3. Incorrect Performance Calculations
**Problem:** Scores or percentages don't match expected
**Solution:** 
- Verify exam type and marking scheme
- Check answer key and scoring logic
- Ensure question weights are correctly applied
- Validate negative marking rules

### 4. Weak Topic Priority Issues
**Problem:** Topics incorrectly prioritized
**Solution:** 
- Verify weightage calculations for exam type
- Check accuracy thresholds and scoring
- Ensure historical performance data is accurate
- Review priority algorithm parameters

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing Analytics Router in Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Analytics Router processes test results to generate comprehensive reports
- AI insights are generated using Gemini Flash 1.5
- Performance analysis includes subject-wise and topic-wise breakdown
- Weak topics are prioritized based on accuracy and exam weightage
- Visualizations are generated for dashboard display
- Rate limiting: 10 requests/minute/user, 100 requests/hour/IP

**Question:** Can you help me debug this issue by:
1. Analyzing the analytics generation pipeline and AI processing
2. Checking if test data format and scoring are correct
3. Identifying common issues with AI insight generation
4. Suggesting specific fixes or debugging steps

**Additional Information:**
- Test ID: [TEST_ID]
- Student ID: [STUDENT_ID]
- Analytics ID: [ANALYTICS_ID_IF_AVAILABLE]
- Include AI Insights: [TRUE/FALSE]
- [Add any relevant logs or observations]
```

---

## Related Models and Services

### Models
- `models.analytics_models.AnalyticsRequest`
- `models.analytics_models.AnalyticsResponse`
- `models.analytics_models.AnalyticsReport`
- `models.analytics_models.AnalyticsInsights`
- `models.analytics_models.PriorityTopic`

### Services
- `services.analytics_service.AnalyticsService`

### Dependencies
- `services.gemini_service.GeminiService`
- `services.test_scoring_service.TestScoringService`
- `services.performance_analytics.PerformanceAnalytics`

---

## Performance Considerations

1. **AI Generation**: Analytics generation takes 5-10 seconds
2. **Caching**: Analytics reports cached for 24 hours
3. **Background Processing**: Async generation with status polling
4. **Database Optimization**: Efficient queries with proper indexes
5. **Rate Limiting**: Protection against excessive API calls

---

## Security Notes

1. **Access Control**: Students/parents can only access their own analytics
2. **Data Privacy**: Performance data anonymized for comparisons
3. **Input Validation**: All test data validated and sanitized
4. **Secure Processing**: Analytics data processed in secure environment
5. **Audit Logging**: All analytics generations and retrievals are logged

---

## Testing Best Practices

1. **Complete Workflow**: Test end-to-end analytics generation
2. **Performance Testing**: Test with various test sizes and complexity
3. **AI Validation**: Verify AI insights quality and relevance
4. **Edge Cases**: Test with incomplete or invalid test data
5. **Integration Testing**: Verify with test management systems