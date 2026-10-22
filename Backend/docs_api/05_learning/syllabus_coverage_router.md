# Syllabus Coverage Router API Documentation

## Overview

The Syllabus Coverage Router provides endpoints for tracking and reporting syllabus coverage. It analyzes student performance across topics, identifies weak areas, and provides recommendations for focused study.

## Base URL
```
/api/syllabus/coverage
```

## Endpoints

### 1. Get Student Coverage

**Endpoint:** `GET /api/syllabus/coverage/{student_id}`

**Description:** Get complete syllabus coverage data for a student including overall coverage percentage, subject-wise coverage, chapter-wise coverage, topic-level details, weak topics, and untested topics.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/student_123?exam_type=JEE_MAIN" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)
- `exam_type`: Exam type (JEE_MAIN, JEE_ADVANCED, NEET) (required)

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "overall_coverage": {
    "percentage": 65.5,
    "covered_topics": 45,
    "total_topics": 69,
    "untested_topics": 24,
    "weak_topics": ["Thermodynamics", "Organic Chemistry", "Integration"]
  },
  "subject_coverage": {
    "Physics": 70.2,
    "Chemistry": 62.5,
    "Mathematics": 63.8
  },
  "chapter_coverage": {
    "Mechanics": 80.0,
    "Thermodynamics": 45.0,
    "Electromagnetism": 75.0,
    "Optics": 60.0,
    "Modern Physics": 65.0,
    "Physical Chemistry": 70.0,
    "Organic Chemistry": 55.0,
    "Inorganic Chemistry": 60.0,
    "Algebra": 65.0,
    "Calculus": 70.0,
    "Trigonometry": 60.0,
    "Coordinate Geometry": 55.0
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### Coverage Metrics
- **Overall Coverage**: Percentage of syllabus covered
- **Subject Coverage**: Breakdown by subject
- **Chapter Coverage**: Detailed chapter-wise percentages
- **Topic Status**: Individual topic completion status
- **Weak Topics**: Areas needing improvement
- **Untested Topics**: Topics not yet attempted

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Access denied (student ID mismatch)
- **404 Not Found:** Coverage data not found
- **500 Internal Server Error:** Failed to retrieve coverage

#### Troubleshooting
- Verify student_id matches authenticated user
- Check exam_type is valid
- Ensure student has taken at least one test
- Verify coverage data exists for the exam type

---

### 2. Get Untested Topics

**Endpoint:** `GET /api/syllabus/coverage/{student_id}/untested`

**Description:** Get list of topics that haven't been tested yet. Useful for identifying gaps in learning.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/student_123/untested?exam_type=JEE_MAIN&subject=Physics&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)
- `exam_type`: Exam type (required)
- `subject`: Filter by subject (optional)
- `limit`: Maximum topics to return (default: 20, max: 100)

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "subject": "Physics",
  "total_untested": 24,
  "topics": [
    {
      "topic_id": "T15",
      "topic_name": "Semiconductors",
      "subject": "Physics",
      "chapter": "Modern Physics",
      "difficulty": "medium",
      "estimated_hours": 4.0,
      "prerequisites": ["Solid State Physics"],
      "priority": "medium"
    },
    {
      "topic_id": "T16",
      "topic_name": "Communication Systems",
      "subject": "Physics",
      "chapter": "Modern Physics",
      "difficulty": "hard",
      "estimated_hours": 6.0,
      "prerequisites": ["Electromagnetic Waves"],
      "priority": "high"
    },
    {
      "topic_id": "T17",
      "topic_name": "Nuclear Physics",
      "subject": "Physics",
      "chapter": "Modern Physics",
      "difficulty": "hard",
      "estimated_hours": 5.0,
      "prerequisites": ["Atomic Structure"],
      "priority": "high"
    }
  ]
}
```

#### Use Cases
- Identify learning gaps
- Plan next study topics
- Prioritize untested areas
- Create focused study schedules

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Access denied
- **500 Internal Server Error:** Failed to retrieve untested topics

---

### 3. Get Weak Topics

**Endpoint:** `GET /api/syllabus/coverage/{student_id}/weak`

**Description:** Get topics where student performed poorly (below threshold). Helps identify areas needing focused practice.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/student_123/weak?exam_type=JEE_MAIN&subject=Physics&threshold=50.0&limit=15" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)
- `exam_type`: Exam type (required)
- `subject`: Filter by subject (optional)
- `threshold`: Score threshold (default: 60.0, range: 0-100)
- `limit`: Maximum topics to return (default: 20, max: 100)

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "subject": "Physics",
  "threshold": 50.0,
  "total_weak": 12,
  "topics": [
    {
      "topic_id": "T05",
      "topic_name": "Thermodynamics",
      "subject": "Physics",
      "chapter": "Thermodynamics",
      "average_score": 35.5,
      "times_tested": 3,
      "last_tested": "2024-01-10T14:30:00Z",
      "difficulty": "hard",
      "priority": "high",
      "recommended_actions": [
        "Review fundamental concepts",
        "Practice numerical problems",
        "Focus on First and Second Laws"
      ]
    },
    {
      "topic_id": "T08",
      "topic_name": "Optics",
      "subject": "Physics",
      "chapter": "Optics",
      "average_score": 45.0,
      "times_tested": 2,
      "last_tested": "2024-01-08T16:45:00Z",
      "difficulty": "medium",
      "priority": "medium",
      "recommended_actions": [
        "Practice ray diagrams",
        "Review lens formulas",
        "Work on interference concepts"
      ]
    }
  ]
}
```

#### Weak Topic Analysis
- Performance score below threshold
- Historical test performance
- Difficulty level and priority
- Recommended improvement actions
- Last tested date for recency

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Access denied
- **500 Internal Server Error:** Failed to retrieve weak topics

---

### 4. Get Coverage Recommendations

**Endpoint:** `GET /api/syllabus/coverage/{student_id}/recommendations`

**Description:** Get recommended topics for next test based on coverage analysis. Prioritizes untested topics (40%), weak topics (40%), and revision topics (20%).

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/student_123/recommendations?exam_type=JEE_MAIN&num_topics=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: Student identifier (required)
- `exam_type`: Exam type (required)
- `num_topics`: Number of topics to recommend (default: 10, range: 1-50)

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "recommendations": [
    {
      "topic_id": "T15",
      "topic_name": "Semiconductors",
      "subject": "Physics",
      "chapter": "Modern Physics",
      "priority": "high",
      "recommendation_type": "untested",
      "reason": "Never tested, high weightage in exam",
      "estimated_difficulty": "medium",
      "study_hours_recommended": 6.0
    },
    {
      "topic_id": "T05",
      "topic_name": "Thermodynamics",
      "subject": "Physics",
      "chapter": "Thermodynamics",
      "priority": "high",
      "recommendation_type": "weak",
      "reason": "Average score 35.5% below threshold",
      "estimated_difficulty": "hard",
      "study_hours_recommended": 8.0
    },
    {
      "topic_id": "T03",
      "topic_name": "Kinematics",
      "subject": "Physics",
      "chapter": "Mechanics",
      "priority": "medium",
      "recommendation_type": "revision",
      "reason": "Last tested 30 days ago, needs refresh",
      "estimated_difficulty": "easy",
      "study_hours_recommended": 2.0
    }
  ],
  "generated_at": "2024-01-15T11:00:00Z"
}
```

#### Recommendation Types
- **untested**: Topics never attempted (40% weight)
- **weak**: Topics with poor performance (40% weight)
- **revision**: Topics tested long ago (20% weight)

#### Priority Logic
- High: Untested + high exam weightage
- Medium: Weak topics or moderate weightage
- Low: Revision topics

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Access denied
- **500 Internal Server Error:** Failed to generate recommendations

---

### 5. Get Coverage Progress

**Endpoint:** `GET /api/syllabus/coverage/{student_id}/progress`

**Description:** Get coverage progress over time with subject-wise status and performance indicators.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/student_123/progress?exam_type=JEE_MAIN" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "exam_type": "JEE_MAIN",
  "current_coverage": 65.5,
  "covered_topics": 45,
  "total_topics": 69,
  "subjects": {
    "Physics": {
      "coverage_percentage": 70.2,
      "status": "good",
      "topics_covered": 18,
      "topics_total": 25
    },
    "Chemistry": {
      "coverage_percentage": 62.5,
      "status": "needs_improvement",
      "topics_covered": 15,
      "topics_total": 24
    },
    "Mathematics": {
      "coverage_percentage": 63.8,
      "status": "needs_improvement",
      "topics_covered": 12,
      "topics_total": 20
    }
  }
}
```

#### Status Classifications
- **excellent**: ≥80% coverage
- **good**: 60-79% coverage
- **needs_improvement**: <60% coverage

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Access denied
- **500 Internal Server Error:** Failed to get progress

---

### 6. Get Topic Details

**Endpoint:** `GET /api/syllabus/coverage/{student_id}/topic/{topic_id}`

**Description:** Get detailed coverage information for a specific topic including test history, performance statistics, and timeline.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/student_123/topic/T05?exam_type=JEE_MAIN" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "student_id": "student_123",
  "topic_id": "T05",
  "topic_name": "Thermodynamics",
  "subject": "Physics",
  "chapter": "Thermodynamics",
  "status": "tested",
  "statistics": {
    "times_tested": 3,
    "total_questions": 45,
    "correct_answers": 16,
    "incorrect_answers": 29,
    "average_score": 35.5,
    "performance": "needs_improvement",
    "first_tested": "2023-12-01T10:00:00Z",
    "last_tested": "2024-01-10T14:30:00Z",
    "improvement_trend": -5.2
  },
  "timeline": {
    "first_tested": "2023-12-01T10:00:00Z",
    "last_tested": "2024-01-10T14:30:00Z",
    "total_tests": 3,
    "test_dates": [
      "2023-12-01T10:00:00Z",
      "2024-01-05T16:20:00Z",
      "2024-01-10T14:30:00Z"
    ]
  },
  "recommendations": [
    "Focus on First and Second Laws",
    "Practice numerical problems on heat engines",
    "Review concepts of entropy and enthalpy"
  ]
}
```

#### Performance Metrics
- Test frequency and recency
- Score trends over time
- Question-level accuracy
- Improvement/degradation indicators

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Access denied
- **404 Not Found:** Topic not found
- **500 Internal Server Error:** Failed to get topic details

---

### 7. Health Check

**Endpoint:** `GET /api/syllabus/coverage/health`

**Description:** Check if the coverage service is operational.

**Authentication:** None

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/health"
```

#### Expected Response (200 OK)
```json
{
  "status": "healthy",
  "service": "syllabus-coverage",
  "timestamp": "2024-01-15T12:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "connected",
    "analytics_service": "available",
    "cache_service": "operational"
  }
}
```

#### Health Indicators
- Service availability
- Database connectivity
- Dependency service status
- Cache service operational status
- Service version information

---

## Testing Workflows

### Complete Coverage Analysis Workflow

1. **Get Overall Coverage**
   ```bash
   curl -X GET "/api/syllabus/coverage/student_123?exam_type=JEE_MAIN" \
     -H "Authorization: Bearer TOKEN"
   ```

2. **Identify Weak Areas**
   ```bash
   curl -X GET "/api/syllabus/coverage/student_123/weak?exam_type=JEE_MAIN&threshold=60" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **Find Untested Topics**
   ```bash
   curl -X GET "/api/syllabus/coverage/student_123/untested?exam_type=JEE_MAIN&limit=10" \
     -H "Authorization: Bearer TOKEN"
   ```

4. **Get Recommendations**
   ```bash
   curl -X GET "/api/syllabus/coverage/student_123/recommendations?exam_type=JEE_MAIN&num_topics=5" \
     -H "Authorization: Bearer TOKEN"
   ```

5. **Check Progress Timeline**
   ```bash
   curl -X GET "/api/syllabus/coverage/student_123/progress?exam_type=JEE_MAIN" \
     -H "Authorization: Bearer TOKEN"
   ```

6. **Analyze Specific Topic**
   ```bash
   curl -X GET "/api/syllabus/coverage/student_123/topic/T05?exam_type=JEE_MAIN" \
     -H "Authorization: Bearer TOKEN"
   ```

---

## Coverage Analysis Features

### Intelligent Recommendations
- **Priority-Based**: High-priority untested topics first
- **Performance-Based**: Weak areas get higher weight
- **Time-Based**: Recently tested topics prioritized for revision
- **Exam Weightage**: Topics aligned with exam pattern

### Coverage Metrics
- **Granular Tracking**: Topic, chapter, subject levels
- **Temporal Analysis**: Progress over time
- **Performance Trends**: Improvement/degradation tracking
- **Gap Identification**: Untested and weak area detection

### Visual Analytics
- **Coverage Heatmaps**: Visual representation of syllabus coverage
- **Progress Charts**: Time-series coverage data
- **Subject Comparisons**: Relative performance across subjects
- **Topic Networks**: Prerequisite and dependency mapping

---

## Common Issues and Solutions

### 1. Coverage Not Updating
**Problem:** Coverage percentage not changing after new tests
**Solution:** 
- Verify test results are properly recorded
- Check if test is linked to correct exam type
- Ensure coverage calculation includes latest test data

### 2. Incorrect Weak Topic Detection
**Problem:** Topics incorrectly flagged as weak
**Solution:** 
- Verify threshold value is appropriate
- Check if recent performance improvement is considered
- Ensure test data quality and scoring accuracy

### 3. Missing Untested Topics
**Problem:** Untested topics list is empty when it shouldn't be
**Solution:** 
- Verify syllabus mapping is complete
- Check if topic status is properly tracked
- Ensure exam type matches syllabus structure

### 4. Recommendation Quality Issues
**Problem:** Recommendations don't match student needs
**Solution:** 
- Verify recommendation algorithm weights
- Check if student performance data is current
- Ensure exam pattern weightages are up-to-date

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing Syllabus Coverage Router in Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Syllabus Coverage Router tracks student performance across exam syllabus
- Coverage analysis includes overall, subject, chapter, and topic levels
- Weak topic identification uses configurable thresholds
- Recommendations prioritize untested (40%), weak (40%), and revision (20%) topics
- Progress tracking includes temporal analysis and performance trends
- Service supports JEE_MAIN, JEE_ADVANCED, and NEET exam types

**Question:** Can you help me debug this issue by:
1. Analyzing the coverage calculation logic and request parameters
2. Checking if student performance data is being processed correctly
3. Identifying common issues with threshold-based filtering
4. Suggesting specific fixes or debugging steps

**Additional Information:**
- Student ID: [STUDENT_ID]
- Exam Type: [EXAM_TYPE]
- Threshold Used: [THRESHOLD_IF_APPLICABLE]
- Topic ID: [TOPIC_ID_IF_APPLICABLE]
- [Add any relevant logs or observations]
```

---

## Related Models and Services

### Models
- `models.syllabus_models.CoverageData`
- `models.syllabus_models.TopicCoverage`
- `models.syllabus_models.ChapterCoverage`
- `models.syllabus_models.WeakTopic`
- `models.syllabus_models.CoverageRecommendation`

### Services
- `services.syllabus_coverage_tracker.SyllabusCoverageTracker`

### Data Sources
- Test results database
- Student performance analytics
- Exam syllabus mappings
- Historical coverage data

---

## Performance Considerations

1. **Coverage Calculation**: Optimized for large syllabus datasets
2. **Caching**: Coverage data cached for 1 hour
3. **Database Queries**: Efficient Firestore queries with proper indexes
4. **Batch Processing**: Support for multiple topic analysis
5. **Background Tasks**: Recommendation generation runs asynchronously

---

## Security Notes

1. **Access Control**: Students can only access their own coverage data
2. **Data Privacy**: Performance data anonymized for analytics
3. **Input Validation**: All parameters validated and sanitized
4. **Rate Limiting**: Protection against excessive API calls
5. **Audit Logging**: All coverage calculations and recommendations logged

---

## Testing Best Practices

1. **Coverage Accuracy**: Test with known student data and verify calculations
2. **Threshold Testing**: Test various threshold values and recommendations
3. **Edge Cases**: Test with students having no test data
4. **Performance Testing**: Test with large syllabus datasets
5. **Integration Testing**: Verify with test management and analytics systems