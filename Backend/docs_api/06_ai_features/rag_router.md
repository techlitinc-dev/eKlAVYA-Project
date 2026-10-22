# RAG Router API Testing Guide

## Overview

The RAG (Retrieval-Augmented Generation) router provides endpoints for generating high-quality exam questions using the Gemini API. It uses semantic search to retrieve relevant syllabus context and generates questions with automatic quality validation.

**Base URL:** `http://localhost:8000/api/rag`

## Authentication

All endpoints require JWT authentication:
```bash
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Generate Questions for Single Topic

**Endpoint:** `POST /api/rag/generate-questions`

Generate high-quality exam questions for a single topic using RAG pipeline.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/rag/generate-questions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "topic": "Limits and Continuity",
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "num_questions": 5,
    "include_explanations": true,
    "question_type": "single_correct",
    "use_cache": true
  }'
```

#### Request Example (Postman):
```json
{
  "topic": "Limits and Continuity",
  "exam_type": "JEE_MAIN",
  "difficulty": "medium",
  "num_questions": 5,
  "include_explanations": true,
  "question_type": "single_correct",
  "use_cache": true
}
```

#### Expected Response (200 OK):
```json
{
  "questions": [
    {
      "question_id": "q_12345",
      "question_text": "What is the limit of f(x) = (x^2 - 4)/(x - 2) as x approaches 2?",
      "options": [
        {"option": "0", "label": "A"},
        {"option": "2", "label": "B"},
        {"option": "4", "label": "C"},
        {"option": "Undefined", "label": "D"}
      ],
      "correct_answer": "4",
      "explanation": "By factoring numerator: (x-2)(x+2)/(x-2) = x+2. As x→2, limit is 4.",
      "difficulty": "medium",
      "topic": "Limits and Continuity",
      "subject": "Mathematics"
    }
  ],
  "metadata": {
    "topic": "Limits and Continuity",
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "generation_method": "RAG",
    "vector_search_used": true,
    "llm_calls": 1,
    "validation_pass_rate": 0.8
  },
  "generation_time": 3.2,
  "quality_stats": {
    "average_score": 85.5,
    "min_score": 78.0,
    "max_score": 95.0,
    "high_quality_count": 5,
    "total_count": 5,
    "valid_count": 5,
    "invalid_count": 0
  },
  "cache_hit": false,
  "total_questions": 5
}
```

#### Error Scenarios:

**400 Bad Request - Invalid topic:**
```json
{
  "detail": "Topic cannot be empty or whitespace only"
}
```

**400 Bad Request - Invalid exam type:**
```json
{
  "detail": "exam_type must be one of: JEE_MAIN, JEE_ADVANCED, NEET"
}
```

**500 Internal Server Error - Generation failed:**
```json
{
  "detail": "Failed to generate questions: Gemini API quota exceeded"
}
```

**503 Service Unavailable - RAG service down:**
```json
{
  "detail": "RAG service is currently unavailable"
}
```

---

### 2. Generate Questions for Multiple Topics (Batch)

**Endpoint:** `POST /api/rag/generate-batch`

Generate questions for multiple topics in a single request.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/rag/generate-batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "topics": ["Calculus", "Algebra", "Trigonometry"],
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "questions_per_topic": 5,
    "filters": {"subject": "Mathematics"},
    "include_explanations": true,
    "question_type": "single_correct"
  }'
```

#### Expected Response (200 OK):
```json
{
  "Calculus": {
    "questions": [...],
    "metadata": {...},
    "generation_time": 3.2,
    "quality_stats": {...},
    "cache_hit": false,
    "total_questions": 5
  },
  "Algebra": {
    "questions": [...],
    "metadata": {...},
    "generation_time": 2.8,
    "quality_stats": {...},
    "cache_hit": true,
    "total_questions": 5
  },
  "Trigonometry": {
    "questions": [...],
    "metadata": {...},
    "generation_time": 3.0,
    "quality_stats": {...},
    "cache_hit": false,
    "total_questions": 5
  }
}
```

#### Error Scenarios:

**400 Bad Request - Empty topics list:**
```json
{
  "detail": "Topics list cannot be empty"
}
```

**400 Bad Request - Too many topics:**
```json
{
  "detail": "Maximum 10 topics allowed per batch request"
}
```

---

### 3. Build Context (Testing)

**Endpoint:** `POST /api/rag/context/build`

Build and return context for a topic using Gemini-based semantic search (testing endpoint).

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/rag/context/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "topic": "Limits and Continuity",
    "exam_type": "JEE_MAIN"
  }'
```

#### Expected Response (200 OK):
```json
{
  "context": "Limits and Continuity is a fundamental concept in calculus...",
  "sources": "Gemini-based semantic search",
  "token_count": 1500,
  "topic": "Limits and Continuity",
  "exam_type": "JEE_MAIN",
  "method": "gemini_api",
  "timestamp": "2024-11-27T10:30:00.000Z"
}
```

---

### 4. Preview Context

**Endpoint:** `POST /api/rag/context/preview`

Preview context and metadata without generating questions.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/rag/context/preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "topic": "Thermodynamics",
    "exam_type": "JEE_ADVANCED"
  }'
```

#### Expected Response (200 OK):
```json
{
  "context_preview": "Thermodynamics is the branch of physics dealing with heat, work, and energy...",
  "full_length": 2500,
  "token_count": 625,
  "estimated_cost": 0.000078,
  "topic": "Thermodynamics",
  "exam_type": "JEE_ADVANCED",
  "timestamp": "2024-11-27T10:30:00.000Z"
}
```

---

### 5. Check Pipeline Status

**Endpoint:** `GET /api/rag/pipeline/status`

Check the health status of the RAG pipeline and all its dependencies.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/rag/pipeline/status \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "all_systems_ok": true,
  "components": {
    "gemini": "healthy",
    "firestore": "healthy",
    "question_generator": "healthy"
  },
  "quotas": {
    "gemini": {
      "remaining_calls": 750,
      "total_calls": 1000,
      "reset_time": "2024-11-28T00:00:00Z",
      "usage_percentage": 25.0
    }
  },
  "last_check": "2024-11-27T10:30:00Z",
  "message": "All systems operational"
}
```

---

### 6. Get Generation Metrics

**Endpoint:** `GET /api/rag/metrics`

Retrieve comprehensive performance metrics for the RAG system.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/rag/metrics \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "total_generated": 500,
  "success_rate": 0.95,
  "avg_quality_score": 85.5,
  "avg_generation_time": 3.2,
  "cache_hit_rate": 0.3,
  "total_requests": 100,
  "failed_requests": 5,
  "high_quality_rate": 0.88
}
```

## Testing Workflow

### Complete Question Generation Testing

1. **Check Pipeline Health:**
   ```bash
   curl -X GET http://localhost:8000/api/rag/pipeline/status
   ```

2. **Preview Context (Optional):**
   ```bash
   curl -X POST http://localhost:8000/api/rag/context/preview \
     -d '{"topic":"Calculus","exam_type":"JEE_MAIN"}'
   ```

3. **Generate Single Topic Questions:**
   ```bash
   curl -X POST http://localhost:8000/api/rag/generate-questions \
     -d '{"topic":"Calculus","exam_type":"JEE_MAIN","difficulty":"medium","num_questions":5}'
   ```

4. **Generate Batch Questions:**
   ```bash
   curl -X POST http://localhost:8000/api/rag/generate-batch \
     -d '{"topics":["Calculus","Algebra"],"exam_type":"JEE_MAIN","questions_per_topic":5}'
   ```

5. **Check Metrics:**
   ```bash
   curl -X GET http://localhost:8000/api/rag/metrics
   ```

## Troubleshooting

### Common Issues

1. **Gemini API Quota Exceeded:**
   - Check quota status at `/api/rag/pipeline/status`
   - Wait for quota reset or upgrade API plan
   - Use cache more frequently (`"use_cache": true`)

2. **Low Quality Questions:**
   - Check quality stats in response
   - Try different difficulty level
   - Verify topic spelling and specificity
   - Check if syllabus data exists for topic

3. **Slow Generation:**
   - Check generation time in response
   - Enable caching (`"use_cache": true`)
   - Reduce number of questions per request
   - Check network connectivity to Gemini API

4. **Empty Results:**
   - Verify topic exists in syllabus
   - Check exam type spelling
   - Try broader topic name
   - Use context preview to debug

### AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT/Claude when debugging RAG issues:

```
I'm testing the Mentor AI RAG question generation system and encountering an issue. Please help me debug:

**System Context:**
- Mentor AI uses Gemini Flash 1.5 for question generation
- RAG pipeline retrieves syllabus context using semantic search
- Questions are validated for quality (score > 80)
- System supports JEE_MAIN, JEE_ADVANCED, NEET exams

**Issue Details:**
- Endpoint: [POST/GET endpoint URL]
- Request payload: [Copy the exact JSON request]
- Error response: [Copy the exact error message]
- Expected behavior: [Describe what should happen]

**Environment:**
- Testing mode: [Yes/No]
- Mock services: [Yes/No]
- API key status: [Valid/Invalid/Expired]

**Questions:**
1. What's causing this error based on the response?
2. How can I fix this issue?
3. What additional logs should I check?
4. Are there any workarounds?

Please provide specific steps to resolve this issue.
```

## Reference Models

### Request Models

- **RAGRequest** ([`models/rag_models.py`](models/rag_models.py:40))
  - `topic`: str (3-200 chars) - Topic name
  - `exam_type`: Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]
  - `difficulty`: Literal["easy", "medium", "hard"]
  - `num_questions`: int (1-20) - Number of questions
  - `include_explanations`: bool - Include explanations
  - `question_type`: Literal["single_correct", "multiple_correct", "numerical"]
  - `use_cache`: bool - Use cached results

- **QuestionGenerationRequest** ([`models/rag_models.py`](models/rag_models.py:147))
  - `topics`: List[str] (1-10 items) - Multiple topics
  - `exam_type`: Exam type for all topics
  - `difficulty`: Difficulty for all topics
  - `questions_per_topic`: int (1-10) - Questions per topic
  - `filters`: Optional[Dict] - Additional filters
  - `include_explanations`: bool - Include explanations
  - `question_type`: Question type for all topics

### Response Models

- **RAGResponse** ([`models/rag_models.py`](models/rag_models.py:457))
  - `questions`: List[Question] - Generated questions
  - `metadata`: RAGMetadata - Generation metadata
  - `generation_time`: float - Time in seconds
  - `quality_stats`: QualityStats - Quality metrics
  - `cache_hit`: bool - From cache or new
  - `total_questions`: int - Total questions returned

- **HealthStatus** ([`models/rag_models.py`](models/rag_models.py:690))
  - `all_systems_ok`: bool - System health
  - `components`: Dict[str, str] - Component status
  - `quotas`: Optional[Dict[str, QuotaInfo]] - API quotas
  - `last_check`: datetime - Last check time
  - `message`: Optional[str] - Status message

- **GenerationMetrics** ([`models/rag_models.py`](models/rag_models.py:771))
  - `total_generated`: int - Total questions
  - `success_rate`: float - Success percentage
  - `avg_quality_score`: float - Average quality
  - `avg_generation_time`: float - Average time
  - `cache_hit_rate`: float - Cache hit percentage
  - `total_requests`: int - Total requests
  - `failed_requests`: int - Failed requests
  - `high_quality_rate`: float - High-quality percentage

## Service Dependencies

- **Gemini Flash 1.5**: Question generation and semantic search
- **Firestore**: Question storage and caching
- **Syllabus Service**: Topic context retrieval
- **Question Generator**: Core generation logic
- **Validation Service**: Question quality scoring

## Rate Limits

- **Generation endpoints**: No hard limit (limited by Gemini API quota)
- **Status/Metrics endpoints**: Standard API rate limits apply
- **Cache TTL**: 7 days for generated questions

## Additional Resources

- [RAG Service Implementation](services/rag_service.py)
- [Question Generator Service](services/question_generator.py)
- [Gemini Service](services/gemini_service.py)
- [Validation Service](services/validation_service.py)