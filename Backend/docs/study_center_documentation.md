# Study Center Learning Journey - Documentation

## Overview

The Study Center Learning Journey is a comprehensive feature in the Mentor AI EdTech Platform that provides students with AI-powered learning materials, progress tracking, and personalized learning paths. This feature integrates multiple services to create a seamless learning experience.

## Features Implemented

### 1. Data Models (`models/study_center_models.py`)

Complete Pydantic models for data validation and API documentation:

- **Topic**: Syllabus topic with progress information
- **LearningMaterials**: Complete learning materials for a topic
- **MindMap**: Structured mind map data in JSON format
- **TeachingContent**: AI-generated teaching materials with examples
- **LearningSession**: Student learning session tracking
- **ProgressSummary**: Student's overall learning progress analytics
- **LearningJourney**: Recommended learning sequence with prerequisites
- **ParentInsights**: Progress insights for parents
- **Request/Response Models**: API endpoint models

### 2. Learning Material Service (`services/learning_material_service.py`)

AI-powered content generation with caching and rate limiting:

- **AI Content Generation**: Uses Google Gemini Flash model
- **Material Types**: Study notes, mind maps, teaching content
- **Caching System**: 30-day cache expiration in Firestore
- **Rate Limiting**: 10 requests per hour per student
- **Retry Logic**: Exponential backoff (2s, 4s) with 2 retries
- **Error Handling**: Comprehensive logging and graceful degradation

### 3. Progress Tracker Service (`services/progress_tracker_service.py`)

Comprehensive progress tracking and analytics:

- **Session Management**: Start/end sessions with duration tracking
- **Progress Calculation**: Topic completion percentages and overall analytics
- **Study Streaks**: Consecutive study day calculation
- **Achievement System**: Badge awarding for milestones
- **Parent Insights**: Detailed analytics for parents with recommendations
- **Timezone Support**: UTC-aware datetime handling

### 4. Study Center Orchestration Service (`services/study_center_service.py`)

High-level service coordinating all study center operations:

- **Topic Management**: Load from syllabus JSON files
- **Material Orchestration**: Cache-first approach with AI generation fallback
- **Learning Journey**: Prerequisite-aware sequencing with motivation
- **Progress Integration**: Real-time progress updates
- **Subject Support**: JEE_MAIN, JEE_ADVANCED, NEET

### 5. API Router (`routers/study_center_router.py`)

Complete REST API endpoints:

- **Topic Management**: Get available topics, topic details
- **Learning Materials**: Generate/retrieve notes, mind maps, teaching content
- **Progress Tracking**: Start/end sessions, get progress summary
- **Learning Journey**: Get recommended learning path
- **Parent Dashboard**: Get child's progress insights
- **Authentication**: Proper user authentication and authorization
- **Error Handling**: Standardized error responses

### 6. Database Optimization (`scripts/setup_study_center_indexes.py`)

Firestore index creation and management:

- **Index Definitions**: Composite indexes for optimal query performance
- **Manual Instructions**: Firebase Console and gcloud CLI setup
- **Performance Monitoring**: Index creation tracking and verification

## API Endpoints

### Topic Management

#### `GET /api/study-center/topics`
Get available topics for a student's exam type.

**Request:**
```json
{
  "student_id": "student_123",
  "subject": "Physics"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Topics retrieved successfully",
  "data": {
    "topics": [
      {
        "topic_id": "T01",
        "topic_name": "Units and Measurements",
        "subject": "Physics",
        "chapter": "Mechanics",
        "difficulty": "easy",
        "estimated_hours": 3.0,
        "prerequisites": [],
        "is_completed": false,
        "completion_percentage": 0.0
      }
    ]
  }
}
```

#### `GET /api/study-center/topics/{topic_id}`
Get detailed information about a specific topic.

**Request:**
```json
{
  "student_id": "student_123",
  "topic_id": "T01"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Topic details retrieved successfully",
  "data": {
    "topic": {
      "topic_id": "T01",
      "topic_name": "Units and Measurements",
      "subject": "Physics",
      "chapter": "Mechanics",
      "difficulty": "easy",
      "estimated_hours": 3.0,
      "prerequisites": [],
      "is_completed": false,
      "completion_percentage": 0.0
    }
  }
}
```

### Learning Materials

#### `GET /api/study-center/materials/{topic_id}`
Get or generate learning materials for a topic.

**Request:**
```json
{
  "student_id": "student_123",
  "topic_id": "T01",
  "material_types": ["notes", "mind_map", "teaching_content"]  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Materials retrieved successfully",
  "data": {
    "topic_id": "T01",
    "topic_name": "Units and Measurements",
    "notes": "# Units and Measurements\n\n## Introduction...",
    "mind_map": {
      "mindmap_id": "mm_T01_123456",
      "structure": {
        "central_concept": "Units and Measurements",
        "main_branches": [...]
      }
    },
    "teaching_content": {
      "topic_id": "T01",
      "introduction": "Units and Measurements is the foundation...",
      "key_concepts": [...],
      "examples": [...],
      "summary": "Key takeaways..."
    },
    "cached": false
  }
}
```

### Progress Tracking

#### `POST /api/study-center/sessions/start`
Start a new learning session.

**Request:**
```json
{
  "student_id": "student_123",
  "topic_id": "T01",
  "topic_name": "Units and Measurements",  // Optional
  "subject": "Physics"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Learning session started successfully",
  "data": {
    "session_id": "sess_student_123_T01_123456789",
    "start_time": "2024-01-15T10:00:00Z"
  }
}
```

#### `POST /api/study-center/sessions/end`
End a learning session and calculate duration.

**Request:**
```json
{
  "student_id": "student_123",
  "session_id": "sess_student_123_T01_123456789",
  "progress_percentage": 75.0,
  "completed": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Learning session ended successfully",
  "data": {
    "session_id": "sess_student_123_T01_123456789",
    "duration_minutes": 45,
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:45:00Z",
    "progress_percentage": 75.0
  }
}
```

### Learning Journey

#### `GET /api/study-center/journey`
Get personalized learning journey with next steps.

**Request:**
```json
{
  "student_id": "student_123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Learning journey retrieved successfully",
  "data": {
    "student_id": "student_123",
    "recommended_sequence": [...],
    "next_topic": {
      "topic_id": "T02",
      "topic_name": "Kinematics",
      "is_completed": false,
      "completion_percentage": 0.0
    },
    "prerequisites_pending": [],
    "motivational_message": "Great job completing Units and Measurements! Let's move on to Kinematics."
  }
}
```

### Parent Dashboard

#### `GET /api/study-center/parent-insights/{child_id}`
Get comprehensive progress insights for parents.

**Request:**
```json
{
  "parent_id": "parent_123",
  "child_id": "student_123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Parent insights retrieved successfully",
  "data": {
    "child_id": "student_123",
    "child_name": "John Doe",
    "overall_progress": 65.0,
    "topics_completed": 13,
    "total_topics": 20,
    "daily_average_minutes": 65.0,
    "weekly_average_minutes": 455.0,
    "most_studied_topics": [
      {
        "topic_name": "Units and Measurements",
        "time_spent_minutes": 180,
        "sessions_count": 5
      }
    ],
    "least_studied_topics": [...],
    "current_streak": 7,
    "last_study_session": "2024-01-15T16:00:00Z",
    "recommendations": [
      "Encourage consistent daily study sessions",
      "Focus on completing Thermodynamics topic",
      "Maintain current 7-day study streak"
    ]
  }
}
```

## Database Schema

### Collections

#### `learning_materials`
Cached AI-generated content with 30-day expiration.

```javascript
{
  material_id: string,
  topic_id: string,
  topic_name: string,
  exam_type: string,
  material_type: string,
  content: string,
  cache_expires_at: timestamp,
  access_count: number,
  last_accessed: timestamp,
  metadata: object
}
```

#### `mind_maps`
Structured mind maps in JSON format.

```javascript
{
  mindmap_id: string,
  topic_id: string,
  topic_name: string,
  exam_type: string,
  structure: object,
  text_representation: string,
  generated_at: timestamp,
  cache_expires_at: timestamp
}
```

#### `learning_progress`
Student progress tracking by topic.

```javascript
{
  progress_id: string,
  student_id: string,
  exam_type: string,
  topics: object,
  overall_stats: object,
  last_updated: timestamp
}
```

#### `learning_sessions`
Learning session tracking with timestamps.

```javascript
{
  session_id: string,
  student_id: string,
  topic_id: string,
  topic_name: string,
  subject: string,
  start_time: timestamp,
  end_time: timestamp,
  duration_minutes: number,
  materials_viewed: array,
  completed: boolean,
  session_date: string
}
```

## Configuration

### Environment Variables

```bash
# Study Center Configuration
STUDY_CENTER_CACHE_EXPIRY_DAYS=30
STUDY_CENTER_RATE_LIMIT_PER_HOUR=10
STUDY_CENTER_MAX_RETRIES=2
STUDY_CENTER_RETRY_DELAY=2
```

### Firebase Indexes

Required composite indexes for optimal performance:

1. **learning_materials**: `(topic_id, exam_type, material_type)`
2. **mind_maps**: `(topic_id, exam_type)`
3. **learning_progress**: `(student_id)`
4. **learning_sessions**: `(student_id, session_date)`

Create indexes using:
```bash
python scripts/setup_study_center_indexes.py
```

Or manually via Firebase Console:
https://console.firebase.google.com/v1/r/project/your-project-id/firestore/indexes
```

## Integration Guide

### Frontend Integration

```typescript
// API Client Setup
import { StudyCenterAPI } from '@/lib/api/study-center';

const studyCenterAPI = new StudyCenterAPI();

// Get topics
const topics = await studyCenterAPI.getTopics(studentId);
const materials = await studyCenterAPI.getMaterials(studentId, topicId);
const journey = await studyCenterAPI.getLearningJourney(studentId);

// Start session
const sessionId = await studyCenterAPI.startSession(studentId, topicId);

// End session
await studyCenterAPI.endSession(studentId, sessionId, progressPercentage);
```

### Service Initialization

```python
from services.study_center_service import get_study_center_service
from services.progress_tracker_service import get_progress_tracker_service

# Initialize services
study_service = get_study_center_service()
progress_service = get_progress_tracker_service()
```

## Performance Considerations

### Caching Strategy

- **Cache-First**: Always check Firestore cache before AI generation
- **30-Day Expiration**: Balance between freshness and storage costs
- **Hit Tracking**: Monitor cache hit rates for optimization
- **Intelligent Refresh**: Update cache when syllabus changes

### Rate Limiting

- **Per-Student Limits**: 10 requests per hour
- **Sliding Window**: Reset limits every hour
- **Graceful Degradation**: Return cached content when rate limited

### Error Handling

- **Retry Logic**: Exponential backoff (2s, 4s, 8s)
- **Timeout Protection**: 30-second generation timeout
- **Fallback Content**: Return basic content when AI fails
- **Comprehensive Logging**: Log all errors with context

## Security Considerations

### Authentication

- **Required Headers**: All endpoints require valid JWT token
- **Parent-Child Access**: Verify parent-child relationships
- **Rate Limiting**: Apply to all API endpoints
- **Input Validation**: Validate all request parameters

### Data Privacy

- **Student Data**: Only access own progress data
- **Parent Insights**: Aggregate data, no personal information
- **Session Data**: Anonymize sensitive information

## Monitoring and Analytics

### Key Metrics

- **API Response Times**: Track average response times
- **Cache Hit Rates**: Monitor cache effectiveness
- **AI Generation Success**: Track content generation success rates
- **User Engagement**: Daily active users, session duration
- **Error Rates**: API error frequencies and types

### Logging Strategy

```python
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('study_center.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

## Deployment

### Environment Setup

```bash
# Production Environment
export NODE_ENV=production
export GEMINI_API_KEY=your-api-key
export FIREBASE_PROJECT_ID=your-project-id

# Start Application
python main.py
```

### Health Checks

```bash
# API Health Check
curl -X GET "https://your-api.com/api/study-center/health" \
  -H "Authorization: Bearer your-jwt-token"

# Database Connectivity
python -c "
from utils.firebase_config import get_firestore_client
db = get_firestore_client()
print('Firestore connection successful')
"
```

## Troubleshooting

### Common Issues

1. **AI Generation Failures**
   - Check Gemini API key and quotas
   - Verify prompt length and content
   - Monitor retry patterns

2. **Cache Misses**
   - Verify Firestore indexes are created
   - Check cache expiration logic
   - Monitor query performance

3. **Progress Tracking Issues**
   - Verify datetime timezone handling
   - Check session ID uniqueness
   - Validate progress calculation logic

4. **Performance Issues**
   - Monitor database query times
   - Check for N+1 query problems
   - Verify index creation

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Test with mock data
python test_study_center_api.py --debug
```

## Future Enhancements

### Planned Features

1. **Adaptive Learning Paths**
   - ML-based topic sequencing
   - Personalized difficulty adjustment
   - Learning style adaptation

2. **Enhanced AI Content**
   - Interactive examples
   - Visual content generation
   - Multi-modal content (text, images, videos)

3. **Social Learning**
   - Study groups and collaboration
   - Peer-to-peer learning
   - Achievement sharing

4. **Advanced Analytics**
   - Learning pattern analysis
   - Performance prediction
   - Engagement metrics

## Support

### Documentation

- **API Documentation**: OpenAPI/Swagger specs
- **Integration Guides**: Frontend examples
- **Troubleshooting Guide**: Common issues and solutions
- **Best Practices**: Performance and security guidelines

### Contact

For technical support and questions:
- **Development Team**: Mentor AI Team
- **Documentation**: This file and inline code comments
- **Issues**: Create GitHub issues with appropriate labels

---

**Last Updated**: December 2, 2024
**Version**: 1.0.0
**Status**: Production Ready