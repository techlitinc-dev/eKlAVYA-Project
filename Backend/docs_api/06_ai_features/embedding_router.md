# Embedding Router API Testing Guide

## Overview

The Embedding router provides endpoints for generating text embeddings using Google Cloud Vertex AI. It converts text into high-dimensional vector representations (768 dimensions) that can be used for semantic search, similarity comparison, and other NLP tasks.

**Base URL:** `http://localhost:8000/api/vector-search/embeddings`

## Authentication

All endpoints require JWT authentication:
```bash
Authorization: Bearer <access_token>
```

## Rate Limiting

- **100 requests per minute per user**
- Rate limit headers included in responses
- Retry-After header indicates wait time on 429 responses

## Endpoints

### 1. Generate Single Embedding

**Endpoint:** `POST /api/vector-search/embeddings/generate`

Generate embedding vector for a single text input using Vertex AI.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/vector-search/embeddings/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "text": "Newton'\''s laws of motion explain the relationship between force and motion",
    "task_type": "RETRIEVAL_DOCUMENT",
    "include_metadata": true
  }'
```

#### Request Example (Postman):
```json
{
  "text": "Newton's laws of motion explain the relationship between force and motion",
  "task_type": "RETRIEVAL_DOCUMENT",
  "include_metadata": true
}
```

#### Expected Response (200 OK):
```json
{
  "embedding": [0.123, -0.456, 0.789, 0.012, -0.345, "..."],
  "dimension": 768,
  "model": "textembedding-gecko@003",
  "timestamp": "2025-11-26T10:30:00.000Z",
  "metadata": {
    "model": "textembedding-gecko@003",
    "dimension": 768,
    "timestamp": "2025-11-26T10:30:00.000Z",
    "cached": false,
    "text_length": 75,
    "processing_time_ms": 120.5
  }
}
```

#### Error Scenarios:

**400 Bad Request - Empty text:**
```json
{
  "detail": "Text cannot be empty or contain only whitespace"
}
```

**400 Bad Request - Text too long:**
```json
{
  "detail": "Text must be at most 3000 characters long"
}
```

**401 Unauthorized - Invalid token:**
```json
{
  "detail": "Could not validate credentials"
}
```

**429 Too Many Requests - Rate limit exceeded:**
```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "message": "Maximum 100 requests per minute allowed",
    "retry_after_seconds": 45
  }
}
```

**503 Service Unavailable - Vertex AI not initialized:**
```json
{
  "detail": "Embedding service is currently unavailable. Please try again later."
}
```

**503 Service Unavailable - Vertex AI API not enabled:**
```json
{
  "detail": {
    "error": "Vertex AI API Not Enabled",
    "message": "The Vertex AI embedding model is not accessible. Please enable the Vertex AI API for your project.",
    "action": "Visit https://console.cloud.google.com/apis/library/aiplatform.googleapis.com to enable the API",
    "note": "After enabling the API, wait a few minutes for changes to propagate"
  }
}
```

---

### 2. Generate Batch Embeddings

**Endpoint:** `POST /api/vector-search/embeddings/batch`

Generate embeddings for multiple text inputs in a single request.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/vector-search/embeddings/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "texts": [
      "Newton'\''s laws of motion",
      "Electromagnetic induction principles",
      "Organic chemistry reaction mechanisms"
    ],
    "task_type": "RETRIEVAL_DOCUMENT",
    "include_metadata": true
  }'
```

#### Expected Response (200 OK):
```json
{
  "embeddings": [
    {
      "embedding": [0.123, -0.456, 0.789, "..."],
      "dimension": 768,
      "model": "textembedding-gecko@003",
      "timestamp": "2025-11-26T10:30:00.000Z",
      "metadata": {
        "model": "textembedding-gecko@003",
        "dimension": 768,
        "timestamp": "2025-11-26T10:30:00.000Z",
        "cached": false,
        "text_length": 28,
        "processing_time_ms": 115.3
      }
    },
    {
      "embedding": [0.234, -0.567, 0.890, "..."],
      "dimension": 768,
      "model": "textembedding-gecko@003",
      "timestamp": "2025-11-26T10:30:00.100Z",
      "metadata": {
        "model": "textembedding-gecko@003",
        "dimension": 768,
        "timestamp": "2025-11-26T10:30:00.100Z",
        "cached": true,
        "text_length": 33,
        "processing_time_ms": 5.2
      }
    },
    {
      "embedding": [0.345, -0.678, 0.901, "..."],
      "dimension": 768,
      "model": "textembedding-gecko@003",
      "timestamp": "2025-11-26T10:30:00.200Z",
      "metadata": {
        "model": "textembedding-gecko@003",
        "dimension": 768,
        "timestamp": "2025-11-26T10:30:00.200Z",
        "cached": false,
        "text_length": 35,
        "processing_time_ms": 118.7
      }
    }
  ],
  "total_count": 3,
  "successful_count": 3,
  "failed_count": 0,
  "total_processing_time_ms": 350.2,
  "cache_hit_count": 1
}
```

#### Error Scenarios:

**400 Bad Request - Empty texts list:**
```json
{
  "detail": "Texts list cannot be empty"
}
```

**400 Bad Request - Too many texts:**
```json
{
  "detail": "List must have at most 100 items"
}
```

**400 Bad Request - Text exceeds length:**
```json
{
  "detail": "Text at index 2 exceeds maximum length of 3000 characters (current: 3500 characters)"
}
```

---

### 3. Get Embedding Service Status

**Endpoint:** `GET /api/vector-search/embeddings/status`

Get the current status and statistics of the embedding service.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/vector-search/embeddings/status \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "service": "embedding-service",
  "status": "healthy",
  "timestamp": "2025-11-26T10:30:00.000Z",
  "vertex_ai": {
    "initialized": true,
    "project_id": "mentor-ai-project",
    "location": "us-central1",
    "model": "textembedding-gecko@003",
    "dimension": 768,
    "regions_supported": ["us-central1", "us-east1", "us-west1"]
  },
  "cache": {
    "total_requests": 500,
    "hits": 150,
    "misses": 75,
    "hit_rate": 0.6667,
    "size": 1250,
    "max_size": 5000,
    "fill_percentage": 25.0
  },
  "rate_limit": {
    "max_requests_per_minute": 100,
    "window_seconds": 60,
    "user_current_count": 5
  }
}
```

#### Error Response (Degraded status):
```json
{
  "service": "embedding-service",
  "status": "error",
  "timestamp": "2025-11-26T10:30:00.000Z",
  "error": "Failed to retrieve complete status",
  "message": "Vertex AI connection timeout"
}
```

## Testing Workflow

### Complete Embedding Testing

1. **Check Service Status:**
   ```bash
   curl -X GET http://localhost:8000/api/vector-search/embeddings/status
   ```

2. **Generate Single Embedding:**
   ```bash
   curl -X POST http://localhost:8000/api/vector-search/embeddings/generate \
     -d '{"text":"Newton'\''s laws of motion","task_type":"RETRIEVAL_DOCUMENT"}'
   ```

3. **Generate Batch Embeddings:**
   ```bash
   curl -X POST http://localhost:8000/api/vector-search/embeddings/batch \
     -d '{"texts":["Physics","Chemistry","Mathematics"],"task_type":"RETRIEVAL_DOCUMENT"}'
   ```

4. **Test Rate Limiting:**
   ```bash
   # Send 101 rapid requests to trigger rate limit
   for i in {1..101}; do
     curl -X POST http://localhost:8000/api/vector-search/embeddings/generate \
       -d '{"text":"test text'$i'","task_type":"RETRIEVAL_DOCUMENT"}' \
       -o /dev/null -s -w "%{http_code}\n"
   done
   ```

5. **Test Cache Performance:**
   ```bash
   # First request (cache miss)
   curl -X POST http://localhost:8000/api/vector-search/embeddings/generate \
     -d '{"text":"test cache","include_metadata":true}'
   
   # Second request (cache hit)
   curl -X POST http://localhost:8000/api/vector-search/embeddings/generate \
     -d '{"text":"test cache","include_metadata":true}'
   ```

## Troubleshooting

### Common Issues

1. **Vertex AI Not Initialized:**
   - Check service status at `/status` endpoint
   - Verify `GOOGLE_APPLICATION_CREDENTIALS` environment variable
   - Ensure Vertex AI API is enabled in Google Cloud project
   - Check service account permissions

2. **Rate Limit Exceeded:**
   - Check `Retry-After` header in 429 response
   - Implement exponential backoff in client
   - Use batch embedding for multiple texts
   - Cache embeddings locally when possible

3. **Invalid Text Input:**
   - Verify text is not empty or whitespace only
   - Check text length (max 3000 characters)
   - Ensure proper UTF-8 encoding
   - Escape special characters in JSON

4. **Slow Performance:**
   - Check processing time in metadata
   - Monitor cache hit rate
   - Consider batch processing for multiple texts
   - Verify network connectivity to Vertex AI

5. **API Quota Issues:**
   - Monitor Vertex AI quota usage
   - Check project quota limits in Google Cloud Console
   - Implement request queuing for high volume
   - Use caching to reduce API calls

### AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT/Claude when debugging embedding issues:

```
I'm testing the Mentor AI embedding generation system and encountering an issue. Please help me debug:

**System Context:**
- Mentor AI uses Google Cloud Vertex AI for text embeddings
- Model: textembedding-gecko@003 (768 dimensions)
- Supports RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING
- Rate limit: 100 requests per minute per user
- Cache enabled for performance

**Issue Details:**
- Endpoint: [POST/GET endpoint URL]
- Request payload: [Copy the exact JSON request]
- Error response: [Copy the exact error message]
- Expected behavior: [Describe what should happen]

**Environment:**
- Google Cloud project: [Project ID]
- Service account: [Configured/Not configured]
- API enabled: [Yes/No]
- Testing mode: [Yes/No]

**Questions:**
1. What's causing this error based on the response?
2. How can I fix this Vertex AI configuration issue?
3. What additional logs should I check?
4. Are there any workarounds for this issue?

Please provide specific steps to resolve this embedding generation issue.
```

## Reference Models

### Request Models

- **EmbeddingRequest** ([`models/embedding_models.py`](models/embedding_models.py:24))
  - `text`: str (1-3000 chars) - Text to embed
  - `task_type`: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY", "SEMANTIC_SIMILARITY", "CLASSIFICATION", "CLUSTERING"]
  - `include_metadata`: bool - Include processing metadata

- **BatchEmbeddingRequest** ([`models/embedding_models.py`](models/embedding_models.py:268))
  - `texts`: List[str] (1-100 items) - Multiple texts
  - `task_type`: Task type for all texts
  - `include_metadata`: bool - Include metadata for each

### Response Models

- **EmbeddingResponse** ([`models/embedding_models.py`](models/embedding_models.py:179))
  - `embedding`: List[float] - 768-dimensional vector
  - `dimension`: int - Vector dimension (768)
  - `model`: str - Model name
  - `timestamp`: datetime - Generation time
  - `metadata`: Optional[EmbeddingMetadata] - Processing details

- **BatchEmbeddingResponse** ([`models/embedding_models.py`](models/embedding_models.py:362))
  - `embeddings`: List[EmbeddingResponse] - All embeddings
  - `total_count`: int - Total texts processed
  - `successful_count`: int - Successful embeddings
  - `failed_count`: int - Failed embeddings
  - `total_processing_time_ms`: float - Total time
  - `cache_hit_count`: int - Cache hits

- **EmbeddingMetadata** ([`models/embedding_models.py`](models/embedding_models.py:106))
  - `model`: str - Model name
  - `dimension`: int - Vector dimension
  - `timestamp`: datetime - Generation time
  - `cached`: bool - From cache or new
  - `text_length`: int - Input text length
  - `processing_time_ms`: Optional[float] - Processing time

## Service Dependencies

- **Google Cloud Vertex AI**: Embedding generation service
- **textembedding-gecko@003**: Google's embedding model (768 dimensions)
- **Authentication Service**: JWT token validation
- **Cache Service**: In-memory caching for performance
- **Rate Limiter**: Request rate limiting per user

## Task Types Explained

- **RETRIEVAL_DOCUMENT**: For documents that will be searched/retrieved
- **RETRIEVAL_QUERY**: For search queries against documents
- **SEMANTIC_SIMILARITY**: For comparing text similarity
- **CLASSIFICATION**: For text classification tasks
- **CLUSTERING**: For text clustering/grouping

## Performance Considerations

1. **Batch Processing**: More efficient than individual requests
2. **Caching**: Automatic caching reduces API calls and latency
3. **Rate Limits**: Implement backoff strategy in clients
4. **Text Length**: Optimal performance under 1000 characters
5. **Regional Deployment**: Use nearest Vertex AI region

## Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Embedding Service Implementation](services/embedding_service.py)
- [Vertex AI Client](utils/vertex_ai_client.py)
- [Google Cloud Console](https://console.cloud.google.com/)