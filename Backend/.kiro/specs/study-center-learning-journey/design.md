# Study Center Learning Journey - Design Document

## Overview

The Study Center Learning Journey feature provides students with AI-powered personalized learning materials including notes, mind maps, practice questions, and progress tracking. The system leverages Google's Gemini Flash model to generate high-quality educational content tailored to each student's exam type and syllabus. All generated materials are cached in Firestore to optimize token usage and provide instant access.

### Key Design Principles

1. **Token Efficiency**: Cache all AI-generated content to minimize API costs
2. **Real Data**: No dummy data - all content generated from actual syllabus and student context
3. **Personalization**: Content adapted to student's exam type (JEE Main/Advanced, NEET)
4. **Progress-Driven**: Track and visualize learning journey to motivate students
5. **Parent Visibility**: Enable parents to monitor their child's learning progress

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend      │
│  (Next.js)      │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌───────────────────────────────────┐  │
│  │  Study Center Router              │  │
│  │  - Topic selection                │  │
│  │  - Material generation            │  │
│  │  - Progress tracking              │  │
│  └──────────┬────────────────────────┘  │
│             │                            │
│  ┌──────────▼────────────────────────┐  │
│  │  Study Center Service             │  │
│  │  - Material orchestration         │  │
│  │  - Cache management               │  │
│  │  - Progress calculation           │  │
│  └──────────┬────────────────────────┘  │
│             │                            │
│  ┌──────────▼────────────────────────┐  │
│  │  Learning Material Service        │  │
│  │  - Notes generation               │  │
│  │  - Mind map generation            │  │
│  │  - Teaching content               │  │
│  └──────────┬────────────────────────┘  │
│             │                            │
│  ┌──────────▼────────────────────────┐  │
│  │  Gemini AI Service                │  │
│  │  - Prompt engineering             │  │
│  │  - Content generation             │  │
│  │  - Response parsing               │  │
│  └──────────┬────────────────────────┘  │
└─────────────┼────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Firestore Database              │
│  - learning_materials (cached content)  │
│  - learning_progress (student tracking) │
│  - learning_sessions (time tracking)    │
│  - mind_maps (structured data)          │
└─────────────────────────────────────────┘
```

### Component Interaction Flow

```
Student selects topic
    │
    ▼
Check Firestore cache
    │
    ├─── Cache Hit ──────► Return cached material (< 500ms)
    │
    └─── Cache Miss ─────► Generate with Gemini AI
                              │
                              ▼
                          Parse & validate response
                              │
                              ▼
                          Store in Firestore cache
                              │
                              ▼
                          Return to student
                              │
                              ▼
                          Track learning session
```

## Components and Interfaces

### 1. Study Center Router (`routers/study_center_router.py`)

**Purpose**: Handle HTTP requests for study center features

**Endpoints**:

```python
# Topic Management
GET  /api/study-center/topics
     - Get available topics for student's exam
     - Query params: student_id, subject (optional)
     - Returns: List of topics with metadata

GET  /api/study-center/topics/{topic_id}
     - Get detailed topic information
     - Returns: Topic details with subtopics

# Learning Materials
GET  /api/study-center/materials/{topic_id}
     - Get all materials for a topic
     - Returns: Notes, mind maps, summaries
     - Checks cache first, generates if needed

POST /api/study-center/materials/generate
     - Force regenerate materials for a topic
     - Body: { topic_id, material_type }
     - Returns: Newly generated material

# Mind Maps
GET  /api/study-center/mindmap/{topic_id}
     - Get mind map for a topic
     - Returns: JSON structure + text representation

# Teaching Content
GET  /api/study-center/teach/{topic_id}
     - Get AI teaching content for a topic
     - Returns: Structured teaching material with examples

# Progress Tracking
GET  /api/study-center/progress/{student_id}
     - Get student's learning progress
     - Returns: Topic-wise completion, time spent

POST /api/study-center/progress/start
     - Start a learning session
     - Body: { student_id, topic_id }
     - Returns: session_id

POST /api/study-center/progress/complete
     - Mark topic as completed
     - Body: { student_id, topic_id, session_id }
     - Returns: Updated progress

# Learning Journey
GET  /api/study-center/journey/{student_id}
     - Get recommended learning sequence
     - Returns: Ordered topics with prerequisites

# Parent Dashboard
GET  /api/study-center/parent-progress/{child_id}
     - Get child's learning progress for parent
     - Returns: Detailed progress with insights
```

### 2. Study Center Service (`services/study_center_service.py`)

**Purpose**: Orchestrate study center operations

**Key Methods**:

```python
class StudyCenterService:
    def get_topics_for_student(student_id: str, subject: Optional[str]) -> List[Topic]
        """Get available topics based on student's exam type"""
    
    def get_learning_materials(topic_id: str, student_id: str) -> LearningMaterials
        """Get or generate learning materials for a topic"""
    
    def check_material_cache(topic_id: str, material_type: str) -> Optional[Dict]
        """Check if materials exist in cache"""
    
    def get_learning_journey(student_id: str) -> LearningJourney
        """Generate recommended learning sequence"""
    
    def get_progress_summary(student_id: str) -> ProgressSummary
        """Calculate student's overall progress"""
```

### 3. Learning Material Service (`services/learning_material_service.py`)

**Purpose**: Generate and manage learning materials using AI

**Key Methods**:

```python
class LearningMaterialService:
    def generate_notes(topic: str, exam_type: str, syllabus_context: str) -> str
        """Generate comprehensive notes using Gemini"""
    
    def generate_mind_map(topic: str, exam_type: str, syllabus_context: str) -> MindMap
        """Generate structured mind map using Gemini"""
    
    def generate_teaching_content(topic: str, exam_type: str, difficulty: str) -> TeachingContent
        """Generate teaching material with examples"""
    
    def parse_mind_map_response(response: str) -> MindMap
        """Parse Gemini response into structured mind map"""
    
    def validate_material_quality(material: str, topic: str) -> bool
        """Validate generated content matches topic"""
```

### 4. Progress Tracker Service (`services/progress_tracker_service.py`)

**Purpose**: Track and analyze student learning progress

**Key Methods**:

```python
class ProgressTrackerService:
    def start_learning_session(student_id: str, topic_id: str) -> str
        """Start a new learning session, return session_id"""
    
    def end_learning_session(session_id: str) -> Dict
        """End session and calculate duration"""
    
    def mark_topic_complete(student_id: str, topic_id: str) -> Dict
        """Mark topic as 100% complete"""
    
    def get_topic_progress(student_id: str, topic_id: str) -> float
        """Get completion percentage for a topic"""
    
    def get_all_progress(student_id: str) -> Dict
        """Get complete progress summary"""
    
    def calculate_study_streaks(student_id: str) -> int
        """Calculate consecutive study days"""
    
    def get_parent_insights(child_id: str) -> ParentInsights
        """Generate insights for parent dashboard"""
```

## Data Models

### Firestore Collections

#### 1. `learning_materials` Collection

```python
{
    "material_id": "mat_<uuid>",
    "topic_id": "topic_123",
    "topic_name": "Thermodynamics",
    "subject": "Physics",
    "exam_type": "JEE_MAIN",
    "material_type": "notes",  # notes, mind_map, teaching_content
    "content": "...",  # Generated content
    "metadata": {
        "generated_at": "2024-01-15T10:00:00Z",
        "model_version": "gemini-1.5-flash",
        "token_count": 1500,
        "generation_time_ms": 2500
    },
    "cache_expires_at": "2024-02-15T10:00:00Z",  # 30 days
    "access_count": 45,  # How many times accessed
    "last_accessed": "2024-01-20T15:30:00Z"
}
```

#### 2. `mind_maps` Collection

```python
{
    "mindmap_id": "mm_<uuid>",
    "topic_id": "topic_123",
    "topic_name": "Thermodynamics",
    "subject": "Physics",
    "exam_type": "JEE_MAIN",
    "structure": {
        "central_concept": "Thermodynamics",
        "main_branches": [
            {
                "name": "Laws of Thermodynamics",
                "sub_branches": [
                    "Zeroth Law",
                    "First Law",
                    "Second Law",
                    "Third Law"
                ]
            },
            {
                "name": "Thermodynamic Processes",
                "sub_branches": [
                    "Isothermal",
                    "Adiabatic",
                    "Isobaric",
                    "Isochoric"
                ]
            }
        ],
        "connections": [
            {"from": "First Law", "to": "Energy Conservation", "type": "implies"},
            {"from": "Second Law", "to": "Entropy", "type": "defines"}
        ]
    },
    "text_representation": "...",  # Markdown format
    "generated_at": "2024-01-15T10:00:00Z",
    "cache_expires_at": "2024-02-15T10:00:00Z"
}
```

#### 3. `learning_progress` Collection

```python
{
    "progress_id": "prog_<student_id>",
    "student_id": "student_123",
    "exam_type": "JEE_MAIN",
    "topics": {
        "topic_123": {
            "topic_name": "Thermodynamics",
            "subject": "Physics",
            "completion_percentage": 100,
            "time_spent_minutes": 180,
            "sessions_count": 5,
            "first_accessed": "2024-01-10T09:00:00Z",
            "last_accessed": "2024-01-15T16:00:00Z",
            "completed_at": "2024-01-15T16:00:00Z",
            "materials_accessed": ["notes", "mind_map", "teaching_content"]
        }
    },
    "overall_stats": {
        "total_topics": 50,
        "completed_topics": 12,
        "in_progress_topics": 8,
        "not_started_topics": 30,
        "total_study_time_minutes": 2400,
        "current_streak_days": 7,
        "longest_streak_days": 14
    },
    "last_updated": "2024-01-15T16:00:00Z"
}
```

#### 4. `learning_sessions` Collection

```python
{
    "session_id": "sess_<uuid>",
    "student_id": "student_123",
    "topic_id": "topic_123",
    "topic_name": "Thermodynamics",
    "subject": "Physics",
    "start_time": "2024-01-15T14:00:00Z",
    "end_time": "2024-01-15T15:30:00Z",
    "duration_minutes": 90,
    "materials_viewed": ["notes", "mind_map"],
    "completed": true,
    "session_date": "2024-01-15"
}
```

### Pydantic Models

#### Request/Response Models (`models/study_center_models.py`)

```python
class Topic(BaseModel):
    topic_id: str
    topic_name: str
    subject: str
    chapter: str
    difficulty: str
    estimated_hours: float
    prerequisites: List[str]
    is_completed: bool
    completion_percentage: float

class LearningMaterials(BaseModel):
    topic_id: str
    topic_name: str
    notes: Optional[str]
    mind_map: Optional[MindMap]
    teaching_content: Optional[TeachingContent]
    cached: bool
    generated_at: datetime

class MindMap(BaseModel):
    mindmap_id: str
    topic_id: str
    structure: Dict[str, Any]
    text_representation: str
    generated_at: datetime

class TeachingContent(BaseModel):
    topic_id: str
    introduction: str
    key_concepts: List[Dict[str, str]]
    examples: List[Dict[str, str]]
    summary: str
    difficulty_level: str

class LearningSession(BaseModel):
    session_id: str
    student_id: str
    topic_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]

class ProgressSummary(BaseModel):
    student_id: str
    total_topics: int
    completed_topics: int
    completion_percentage: float
    total_study_time_hours: float
    current_streak_days: int
    topics_by_subject: Dict[str, Dict[str, int]]

class LearningJourney(BaseModel):
    student_id: str
    recommended_sequence: List[Topic]
    next_topic: Topic
    prerequisites_pending: List[Topic]
    motivational_message: str

class ParentInsights(BaseModel):
    child_id: str
    child_name: str
    overall_progress: float
    topics_completed: int
    total_topics: int
    daily_average_minutes: float
    weekly_average_minutes: float
    most_studied_topics: List[Dict[str, Any]]
    least_studied_topics: List[Dict[str, Any]]
    current_streak: int
    last_study_session: datetime
    recommendations: List[str]
```

## AI Prompt Engineering

### Notes Generation Prompt Template

```python
def build_notes_prompt(topic: str, exam_type: str, syllabus_context: str) -> str:
    return f"""You are an expert {exam_type} tutor. Generate comprehensive study notes for the topic: {topic}

Syllabus Context:
{syllabus_context}

Generate detailed notes that include:
1. Introduction and overview
2. Key concepts and definitions
3. Important formulas and equations
4. Conceptual explanations
5. Common misconceptions
6. Exam-specific tips

Format the notes in clear markdown with proper headings, bullet points, and emphasis.
Focus on clarity and exam relevance. Include 2-3 worked examples.

Notes:"""
```

### Mind Map Generation Prompt Template

```python
def build_mindmap_prompt(topic: str, exam_type: str, syllabus_context: str) -> str:
    return f"""You are an expert {exam_type} tutor. Create a structured mind map for: {topic}

Syllabus Context:
{syllabus_context}

Generate a mind map in JSON format with the following structure:
{{
    "central_concept": "Main topic name",
    "main_branches": [
        {{
            "name": "Branch 1",
            "sub_branches": ["Sub 1.1", "Sub 1.2", "Sub 1.3"]
        }},
        {{
            "name": "Branch 2",
            "sub_branches": ["Sub 2.1", "Sub 2.2"]
        }}
    ],
    "connections": [
        {{"from": "Concept A", "to": "Concept B", "type": "implies"}},
        {{"from": "Concept C", "to": "Concept D", "type": "requires"}}
    ]
}}

Include at least 4-6 main branches with 3-5 sub-branches each.
Show important relationships between concepts.

Mind Map JSON:"""
```

### Teaching Content Prompt Template

```python
def build_teaching_prompt(topic: str, exam_type: str, difficulty: str) -> str:
    return f"""You are an expert {exam_type} tutor teaching: {topic}

Difficulty Level: {difficulty}

Create comprehensive teaching content with:

1. INTRODUCTION (2-3 paragraphs)
   - What is this topic about?
   - Why is it important for {exam_type}?
   - Real-world applications

2. KEY CONCEPTS (4-6 concepts)
   - Concept name
   - Clear explanation
   - Visual description if applicable

3. WORKED EXAMPLES (minimum 2)
   - Problem statement
   - Step-by-step solution
   - Key insights

4. SUMMARY
   - Main takeaways
   - Common mistakes to avoid
   - Exam tips

Format in clear markdown. Be thorough but concise.

Teaching Content:"""
```

## Error Handling

### Error Scenarios and Responses

1. **Gemini API Failure**
   - Retry up to 2 times with exponential backoff (2s, 4s)
   - If all retries fail, return user-friendly error
   - Log full error context for debugging

2. **Cache Miss + Generation Timeout**
   - Set 30-second timeout for generation
   - Show loading indicator to user
   - If timeout, return partial content or error

3. **Invalid Topic ID**
   - Return 404 with clear message
   - Suggest valid topics

4. **Student Not Found**
   - Return 404 with authentication prompt
   - Check token validity

5. **Rate Limiting**
   - Implement 10 requests/hour per student
   - Return 429 with retry-after header
   - Show friendly message to user

## Testing Strategy

### Unit Tests

1. **Service Layer Tests**
   - Test material generation with mocked Gemini responses
   - Test cache hit/miss logic
   - Test progress calculations
   - Test mind map parsing

2. **Model Validation Tests**
   - Test Pydantic model validation
   - Test edge cases for all fields

### Integration Tests

1. **End-to-End Flow Tests**
   - Test complete material generation flow
   - Test progress tracking flow
   - Test parent insights generation

2. **Database Tests**
   - Test Firestore read/write operations
   - Test cache expiration logic
   - Test concurrent access

### Performance Tests

1. **Response Time Tests**
   - Cached materials: < 500ms (95th percentile)
   - New generation: < 30s (95th percentile)

2. **Load Tests**
   - Test 100 concurrent requests
   - Test cache efficiency under load

## Security Considerations

1. **Authentication**
   - All endpoints require valid JWT token
   - Verify student/parent identity before returning data

2. **Authorization**
   - Students can only access their own progress
   - Parents can only access their child's data
   - Validate parent-child relationship

3. **Rate Limiting**
   - Per-student rate limits to prevent abuse
   - Per-IP rate limits for API protection

4. **Data Privacy**
   - No sharing of student data across accounts
   - Secure storage of learning materials
   - GDPR-compliant data handling

## Performance Optimization

1. **Caching Strategy**
   - Cache all generated materials for 30 days
   - Serve identical content to all students (same topic + exam type)
   - Implement LRU eviction if cache grows too large

2. **Database Indexing**
   - Index on `topic_id` + `exam_type` for fast lookups
   - Index on `student_id` for progress queries
   - Composite index on `student_id` + `session_date` for session queries

3. **Lazy Loading**
   - Load mind maps only when requested
   - Load teaching content on-demand
   - Paginate topic lists for large syllabi

4. **Token Optimization**
   - Reuse cached content aggressively
   - Batch similar requests when possible
   - Monitor token usage per topic

## Monitoring and Analytics

1. **Key Metrics**
   - Cache hit rate (target: > 80%)
   - Average response time
   - Token consumption per day
   - Student engagement (sessions per day)
   - Material generation success rate

2. **Logging**
   - Log all AI generation requests with token counts
   - Log cache hits/misses
   - Log errors with full context
   - Log performance metrics

3. **Alerts**
   - Alert on cache hit rate < 70%
   - Alert on response time > 1s for cached content
   - Alert on Gemini API errors > 5% of requests
   - Alert on token budget approaching limit
