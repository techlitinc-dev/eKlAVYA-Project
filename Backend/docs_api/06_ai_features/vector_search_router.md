# Vector Search Router API Testing Guide

## Overview

The Vector Search router provides endpoints for semantic search using Gemini API to find relevant syllabus topics based on natural language queries. It replaces traditional vector embeddings with Gemini-based semantic search for improved accuracy.

**Base URL:** `http://localhost:8000/api/vector-search`

## Authentication

All endpoints require JWT authentication:
```bash
Authorization: Bearer <access_token>
```

## Rate Limiting

- **50 search requests per minute per user**
- Rate limit headers included in responses
- Retry-After header indicates wait time on 429 responses

## Endpoints

### 1. Search for Similar Topics

**Endpoint:** `POST /api/vector-search/query`

Search for similar syllabus topics using Gemini-based semantic search.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/vector-search/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "query": "What are Newton'\''s laws of motion?",
    "top_k": 10,
    "filters": {
      "exam": "JEE_MAIN",
      "subject": "Physics",
      "difficulty": "medium"
    },
    "include_metadata": true,
    "min_similarity_score": 0.5
  }'
```

#### Request Example (Postman):
```json
{
  "query": "What are Newton's laws of motion?",
  "top_k": 10,
  "filters": {
    "exam": "JEE_MAIN",
    "subject": "Physics",
    "difficulty": "medium"
  },
  "include_metadata": true,
  "min_similarity_score": 0.5
}
```

#### Expected Response (200 OK):
```json
{
  "query": "What are Newton's laws of motion?",
  "results": [
    {
      "topic": "Newton's Laws of Motion",
      "chapter": "Mechanics",
      "content": "Newton's first law states that an object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced force.",
      "metadata": {
        "key_concepts": ["Inertia", "Force", "Motion"],
        "formulas": ["F = ma"],
        "chapter_weightage": 15.0,
        "topic_id": "T01",
        "subtopic_id": "ST01"
      },
      "similarity_score": 0.92,
      "rank": 1,
      "exam": "JEE_MAIN",
      "subject": "Physics",
      "difficulty": "medium",
      "weightage": 5.0
    },
    {
      "topic": "Newton's Second Law",
      "chapter": "Mechanics",
      "content": "Newton's second law states that the acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass.",
      "metadata": {
        "key_concepts": ["Force", "Mass", "Acceleration"],
        "formulas": ["F = ma"],
        "chapter_weightage": 15.0,
        "topic_id": "T02",
        "subtopic_id": "ST02"
      },
      "similarity_score": 0.88,
      "rank": 2,
      "exam": "JEE_MAIN",
      "subject": "Physics",
      "difficulty": "medium",
      "weightage": 5.0
    }
  ],
  "total_results": 2,
  "search_time_ms": 125.5,
  "cached": false,
  "filters_applied": {
    "exam": "JEE_MAIN",
    "subject": "Physics",
    "difficulty": "medium"
  },
  "embedding_time_ms": 45.2
}
```

#### Error Scenarios:

**400 Bad Request - Empty query:**
```json
{
  "detail": "Query cannot be empty or contain only whitespace"
}
```

**400 Bad Request - Query too long:**
```json
{
  "detail": "Query must be at most 500 characters long"
}
```

**400 Bad Request - Invalid similarity score:**
```json
{
  "detail": "min_similarity_score must be between 0 and 1"
}
```

**429 Too Many Requests - Rate limit exceeded:**
```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "message": "Maximum 50 search requests per minute allowed",
    "retry_after_seconds": 30
  }
}
```

**503 Service Unavailable - Gemini API down:**
```json
{
  "detail": {
    "error": "Gemini API Service Unavailable",
    "message": "Search service requires Gemini API to be accessible.",
    "note": "This feature uses Gemini API for semantic search"
  }
}
```

---

### 2. Batch Search Multiple Queries

**Endpoint:** `POST /api/vector-search/query/batch`

Search for similar topics using multiple queries with Gemini API.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/vector-search/query/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "queries": [
      "What are Newton'\''s laws?",
      "Explain electromagnetic induction",
      "What is organic chemistry?"
    ],
    "top_k": 5,
    "filters": {
      "exam": "JEE_MAIN"
    },
    "include_metadata": true
  }'
```

#### Expected Response (200 OK):
```json
{
  "queries": [
    "What are Newton's laws?",
    "Explain electromagnetic induction",
    "What is organic chemistry?"
  ],
  "results": [
    {
      "query": "What are Newton's laws?",
      "results": [...],
      "total_results": 5,
      "search_time_ms": 120.5,
      "cached": false,
      "filters_applied": {"exam": "JEE_MAIN"}
    },
    {
      "query": "Explain electromagnetic induction",
      "results": [...],
      "total_results": 5,
      "search_time_ms": 130.0,
      "cached": true,
      "filters_applied": {"exam": "JEE_MAIN"}
    },
    {
      "query": "What is organic chemistry?",
      "results": [...],
      "total_results": 5,
      "search_time_ms": 125.3,
      "cached": false,
      "filters_applied": {"exam": "JEE_MAIN"}
    }
  ],
  "total_queries": 3,
  "total_results": 15,
  "total_search_time_ms": 375.8,
  "average_search_time_ms": 125.27,
  "cache_hit_count": 1
}
```

#### Error Scenarios:

**400 Bad Request - Empty queries list:**
```json
{
  "detail": "Queries list cannot be empty"
}
```

**400 Bad Request - Too many queries:**
```json
{
  "detail": "List must have at most 20 items"
}
```

**400 Bad Request - Query too long:**
```json
{
  "detail": "Query at index 1 exceeds maximum length of 500 characters (current: 550 characters)"
}
```

---

### 3. Get Vector Search Index Status

**Endpoint:** `GET /api/vector-search/index/status`

Get the current status and statistics of the Gemini-based search service.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/vector-search/index/status \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "service": "gemini-search",
  "status": "healthy",
  "health": "healthy",
  "method": "gemini_api",
  "note": "Using Gemini API for semantic search (no vector embeddings required)",
  "timestamp": "2025-11-26T10:30:00.000Z",
  "search_stats": {
    "total_searches": 1250,
    "cache_hits": 450,
    "cache_misses": 800,
    "cache_hit_rate": 0.36,
    "total_results_returned": 12500,
    "average_results_per_search": 10.0,
    "cache_size": 500,
    "cache_max_size": 5000
  }
}
```

#### Error Response (Degraded status):
```json
{
  "service": "gemini-search",
  "status": "error",
  "health": "degraded",
  "method": "gemini_api",
  "timestamp": "2025-11-26T10:30:00.000Z",
  "error": "Failed to retrieve complete status",
  "message": "Gemini API connection timeout"
}
```

---

### 4. Get Syllabus Content

**Endpoint:** `GET /api/vector-search/syllabus/{exam}/{subject}`

Get syllabus topics and content for a specific exam and subject.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/vector-search/syllabus/JEE_MAIN/Physics \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "exam": "JEE_MAIN",
  "subject": "Physics",
  "topics": [
    {
      "topic_name": "Newton's Laws of Motion",
      "chapter_name": "Mechanics",
      "difficulty": "medium",
      "weightage": 5.0,
      "content": "Newton's first law states...",
      "key_concepts": ["Inertia", "Force"],
      "formulas": ["F = ma"]
    },
    {
      "topic_name": "Electromagnetic Induction",
      "chapter_name": "Electromagnetism",
      "difficulty": "hard",
      "weightage": 8.0,
      "content": "Faraday's law states...",
      "key_concepts": ["Magnetic flux", "Induced EMF"],
      "formulas": ["ε = -dΦ/dt"]
    }
  ],
  "total_topics": 150,
  "timestamp": "2025-11-26T10:30:00.000Z"
}
```

#### Error Scenarios:

**400 Bad Request - Invalid exam/subject combination:**
```json
{
  "detail": "Invalid combination: NEET exam does not have Mathematics subject"
}
```

**404 Not Found - Syllabus file missing:**
```json
{
  "detail": "Syllabus not found for JEE_MAIN - Biology"
}
```

---

### 5. Get Syllabus Statistics

**Endpoint:** `GET /api/vector-search/syllabus/stats`

Get comprehensive statistics about available syllabus content.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/vector-search/syllabus/stats \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "total_exams": 3,
  "total_subjects": 7,
  "total_chapters": 45,
  "total_topics": 450,
  "total_subtopics": 1250,
  "timestamp": "2025-11-26T10:30:00.000Z",
  "exams": {
    "JEE_MAIN": {
      "subjects": ["Physics", "Chemistry", "Mathematics"],
      "total_topics": 150,
      "total_chapters": 15,
      "total_subtopics": 420,
      "subjects_data": {
        "Physics": {
          "chapters": 5,
          "topics": 50,
          "subtopics": 140,
          "average_weightage": 6.5,
          "difficulty_distribution": {
            "easy": 0.3,
            "medium": 0.5,
            "hard": 0.2
          }
        }
      }
    },
    "JEE_ADVANCED": {
      "subjects": ["Physics", "Chemistry", "Mathematics"],
      "total_topics": 150,
      "total_chapters": 15,
      "total_subtopics": 420
    },
    "NEET": {
      "subjects": ["Physics", "Chemistry", "Biology"],
      "total_topics": 150,
      "total_chapters": 15,
      "total_subtopics": 410
    }
  }
}
```

#### Error Response (Partial data):
```json
{
  "error": "Failed to retrieve syllabus statistics",
  "message": "Some syllabus files are missing",
  "timestamp": "2025-11-26T10:30:00.000Z"
}
```

## Testing Workflow

### Complete Search Testing

1. **Check Index Status:**
   ```bash
   curl -X GET http://localhost:8000/api/vector-search/index/status
   ```

2. **Single Query Search:**
   ```bash
   curl -X POST http://localhost:8000/api/vector-search/query \
     -d '{"query":"Newton'\''s laws","top_k":10,"filters":{"exam":"JEE_MAIN"}}'
   ```

3. **Batch Search:**
   ```bash
   curl -X POST http://localhost:8000/api/vector-search/query/batch \
     -d '{"queries":["Physics","Chemistry"],"top_k":5,"filters":{"exam":"JEE_MAIN"}}'
   ```

4. **Get Syllabus Content:**
   ```bash
   curl -X GET http://localhost:8000/api/vector-search/syllabus/JEE_MAIN/Physics
   ```

5. **Get Syllabus Statistics:**
   ```bash
   curl -X GET http://localhost:8000/api/vector-search/syllabus/stats
   ```

6. **Test Rate Limiting:**
   ```bash
   # Send 51 rapid requests to trigger rate limit
   for i in {1..51}; do
     curl -X POST http://localhost:8000/api/vector-search/query \
       -d '{"query":"test'$i'","top_k":5}' \
       -o /dev/null -s -w "%{http_code}\n"
   done
   ```

## Troubleshooting

### Common Issues

1. **Gemini API Unavailable:**
   - Check index status at `/api/vector-search/index/status`
   - Verify Gemini API key is valid
   - Check network connectivity to Google services
   - Monitor API quota usage

2. **Poor Search Results:**
   - Check query spelling and clarity
   - Adjust similarity score threshold
   - Try different filters (exam, subject, difficulty)
   - Verify topic exists in syllabus

3. **Rate Limit Exceeded:**
   - Check `Retry-After` header in 429 response
   - Implement exponential backoff in client
   - Use batch search for multiple queries
   - Cache search results when possible

4. **Empty Syllabus Data:**
   - Verify exam/subject combination is valid
   - Check syllabus files exist in `data/syllabus/`
   - Validate JSON format of syllabus files
   - Check file permissions

5. **Slow Search Performance:**
   - Monitor search time in response
   - Check cache hit rate
   - Reduce top_k parameter for faster results
   - Optimize query specificity

### AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT/Claude when debugging vector search issues:

```
I'm testing Mentor AI vector search system and encountering an issue. Please help me debug:

**System Context:**
- Mentor AI uses Gemini API for semantic search (no vector embeddings)
- Supports JEE_MAIN, JEE_ADVANCED, NEET exams
- Subjects: Physics, Chemistry, Mathematics, Biology
- Rate limit: 50 search requests per minute per user
- Cache enabled for performance

**Issue Details:**
- Endpoint: [POST/GET endpoint URL]
- Request payload: [Copy exact JSON request]
- Error response: [Copy the exact error message]
- Expected behavior: [Describe what should happen]

**Environment:**
- Gemini API key: [Valid/Invalid/Expired]
- Syllabus data: [Complete/Partial/Missing]
- Testing mode: [Yes/No]
- Cache enabled: [Yes/No]

**Questions:**
1. What's causing this search error based on the response?
2. How can I improve search result quality?
3. What additional logs should I check?
4. Are there any workarounds for this issue?

Please provide specific steps to resolve this vector search issue.
```

## Reference Models

### Request Models

- **SearchRequest** ([`models/vector_search_models.py`](models/vector_search_models.py:121))
  - `query`: str (1-500 chars) - Search query text
  - `top_k`: int (1-50) - Number of results
  - `filters`: Optional[SearchFilters] - Result filters
  - `include_metadata`: bool - Include full metadata
  - `min_similarity_score`: float (0-1) - Similarity threshold

- **BatchSearchRequest** ([`models/vector_search_models.py`](models/vector_search_models.py:536))
  - `queries`: List[str] (1-20 items) - Multiple queries
  - `top_k`: int (1-50) - Results per query
  - `filters`: Optional[SearchFilters] - Applied to all queries
  - `include_metadata`: bool - Include metadata
  - `min_similarity_score`: float - Similarity threshold

- **SearchFilters** ([`models/vector_search_models.py`](models/vector_search_models.py:25))
  - `exam`: Optional[Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]]
  - `subject`: Optional[Literal["Physics", "Chemistry", "Mathematics", "Biology"]]
  - `difficulty`: Optional[Literal["easy", "medium", "hard"]]
  - `chapter_id`: Optional[str] - Specific chapter filter
  - `min_weightage`: Optional[float] - Minimum weightage
  - `max_weightage`: Optional[float] - Maximum weightage

### Response Models

- **SearchResponse** ([`models/vector_search_models.py`](models/vector_search_models.py:399))
  - `query`: str - Original search query
  - `results`: List[SearchResult] - Ranked results
  - `total_results`: int - Number of results
  - `search_time_ms`: float - Search time
  - `cached`: bool - From cache or new
  - `filters_applied`: Optional[SearchFilters] - Applied filters
  - `embedding_time_ms`: Optional[float] - Query processing time

- **BatchSearchResponse** ([`models/vector_search_models.py`](models/vector_search_models.py:645))
  - `queries`: List[str] - Original queries
  - `results`: List[SearchResponse] - Response per query
  - `total_queries`: int - Number of queries
  - `total_results`: int - Total results across queries
  - `total_search_time_ms`: float - Total time
  - `average_search_time_ms`: float - Average per query
  - `cache_hit_count`: int - Cache hits

- **SearchResult** ([`models/vector_search_models.py`](models/vector_search_models.py:286))
  - `topic`: str - Topic name
  - `chapter`: str - Chapter name
  - `content`: str - Topic content
  - `metadata`: Dict[str, Any] - Additional metadata
  - `similarity_score`: float (0-1) - Similarity score
  - `rank`: int - Result ranking
  - `exam`: str - Exam type
  - `subject`: str - Subject name
  - `difficulty`: str - Difficulty level
  - `weightage`: float - Topic weightage

## Service Dependencies

- **Gemini API**: Semantic search engine
- **Syllabus Service**: Topic and content management
- **Cache Service**: Search result caching
- **Authentication Service**: JWT token validation
- **Rate Limiter**: Request rate limiting

## Search Features

1. **Semantic Understanding**: Natural language query processing
2. **Contextual Results**: Topic and chapter context
3. **Flexible Filtering**: Multiple filter options
4. **Relevance Scoring**: Similarity-based ranking
5. **Batch Processing**: Multiple queries in single request
6. **Performance Caching**: Automatic result caching

## Additional Resources

- [Syllabus Data Structure](data/syllabus/)
- [Vector Search Service](services/vector_search_service.py)
- [Syllabus Service](services/syllabus_service.py)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Search Algorithm Documentation](docs/vector_search_algorithm.md)