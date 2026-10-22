# Question Router API Documentation

## Overview

The Question Router provides endpoints for question management and retrieval using RAG (Retrieval-Augmented Generation). It supports generating new questions, retrieving existing questions, validating quality, and searching with filters.

## Base URL
```
/api/questions
```

## Endpoints

### 1. Generate Questions

**Endpoint:** `POST /api/questions/generate`

**Description:** Generate new questions using RAG (Retrieval-Augmented Generation) pipeline.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/questions/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Limits and Continuity",
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "num_questions": 5,
    "use_cache": true
  }'
```

#### Expected Response (200 OK)
```json
{
  "questions": [
    {
      "question_id": "q_abc123",
      "question": "What is the limit of sin(x)/x as x approaches 0?",
      "options": {
        "A": "0",
        "B": "1",
        "C": "∞",
        "D": "Does not exist"
      },
      "correct_answer": "B",
      "explanation": "The limit of sin(x)/x as x approaches 0 is 1, which is a standard limit result.",
      "difficulty": "medium",
      "topic": "Limits and Continuity",
      "subtopic": "Standard Limits",
      "subject": "Mathematics",
      "exam_type": "JEE_MAIN",
      "question_type": "single_correct",
      "marks": 4,
      "time_estimate_minutes": 2,
      "metadata": {
        "validation_score": 92,
        "created_at": "2024-01-15T10:30:00Z",
        "rag_context_used": true,
        "syllabus_aligned": true
      }
    }
  ],
  "metadata": {
    "topic": "Limits and Continuity",
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "total_requested": 5,
    "total_generated": 5,
    "generation_method": "rag",
    "model_used": "gemini-flash-1.5"
  },
  "generation_time": 2.3,
  "quality_stats": {
    "average_score": 88.5,
    "above_threshold": 5,
    "below_threshold": 0,
    "threshold_used": 80
  },
  "cache_hit": false,
  "total_questions": 5
}
```

#### Features
- Automatic storage in Firestore
- Quality filtering (score > 80)
- Caching support
- Metadata tracking

#### Process
1. Retrieves relevant context from syllabus
2. Generates questions using Gemini Flash
3. Validates and filters for quality
4. Stores in Firestore automatically
5. Returns generated questions with metadata

#### Error Scenarios
- **400 Bad Request:** Invalid request parameters
- **500 Internal Server Error:** Generation failed

#### Troubleshooting
- Verify topic exists in syllabus
- Check exam_type is valid (JEE_MAIN, JEE_ADVANCED, NEET)
- Ensure difficulty is valid (easy, medium, hard)
- Check num_questions is reasonable (1-50)

---

### 2. Get Question by ID

**Endpoint:** `GET /api/questions/{question_id}`

**Description:** Retrieve a specific question by its Firestore document ID.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/questions/q_abc123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "question_id": "q_abc123",
  "question": "What is the limit of sin(x)/x as x approaches 0?",
  "options": {
    "A": "0",
    "B": "1",
    "C": "∞",
    "D": "Does not exist"
  },
  "correct_answer": "B",
  "explanation": "The limit of sin(x)/x as x approaches 0 is 1, which is a standard limit result.",
  "difficulty": "medium",
  "topic": "Limits and Continuity",
  "subtopic": "Standard Limits",
  "subject": "Mathematics",
  "exam_type": "JEE_MAIN",
  "question_type": "single_correct",
  "marks": 4,
  "time_estimate_minutes": 2,
  "metadata": {
    "validation_score": 92,
    "created_at": "2024-01-15T10:30:00Z",
    "rag_context_used": true,
    "syllabus_aligned": true
  }
}
```

#### Use Cases
- Displaying question details
- Editing existing questions
- Reviewing question quality

#### Error Scenarios
- **404 Not Found:** Question not found
- **500 Internal Server Error:** Database error

---

### 3. Get Questions by Topic

**Endpoint:** `GET /api/questions/by-topic/{topic}`

**Description:** Retrieve all questions for a specific topic with optional filtering and pagination.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/questions/by-topic/Calculus?exam_type=JEE_MAIN&difficulty=medium&limit=5&sort_by=quality_score&sort_order=desc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `exam_type`: Filter by exam type (JEE_MAIN, JEE_ADVANCED, NEET)
- `difficulty`: Filter by difficulty (easy, medium, hard)
- `limit`: Number of questions to return (default: 20, max: 100)
- `offset`: Number of questions to skip (for pagination)
- `sort_by`: Sort field (created_at, quality_score, difficulty)
- `sort_order`: Sort order (asc, desc)

#### Expected Response (200 OK)
```json
{
  "questions": [
    {
      "question_id": "q_def456",
      "question": "Find the derivative of x² + 3x + 2",
      "options": {
        "A": "2x + 3",
        "B": "2x + 2",
        "C": "x + 3",
        "D": "2x"
      },
      "correct_answer": "A",
      "explanation": "Using the power rule, d/dx(x²) = 2x, d/dx(3x) = 3, d/dx(2) = 0. So derivative is 2x + 3.",
      "difficulty": "medium",
      "topic": "Calculus",
      "subtopic": "Differentiation",
      "subject": "Mathematics",
      "exam_type": "JEE_MAIN",
      "question_type": "single_correct",
      "marks": 4,
      "time_estimate_minutes": 1,
      "metadata": {
        "validation_score": 95,
        "created_at": "2024-01-14T15:20:00Z"
      }
    }
  ],
  "total_count": 1,
  "avg_quality_score": 95.0,
  "topics_covered": ["Calculus", "Differentiation"],
  "generation_time": 0.0
}
```

#### Features
- Pagination support
- Multiple filter options
- Sorting capabilities
- Aggregate statistics

#### Use Cases
- Topic-based practice sets
- Question bank browsing
- Building custom tests

#### Error Scenarios
- **400 Bad Request:** Invalid query parameters
- **500 Internal Server Error:** Database error

---

### 4. Validate Question

**Endpoint:** `POST /api/questions/validate`

**Description:** Validate a question for structural correctness and quality.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/questions/validate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the derivative of sin(x)?",
    "options": {
      "A": "cos(x)",
      "B": "-cos(x)",
      "C": "sin(x)",
      "D": "-sin(x)"
    },
    "correct_answer": "A",
    "explanation": "The derivative of sin(x) is cos(x) by standard rules.",
    "difficulty": "easy",
    "topic": "Calculus",
    "exam_type": "JEE_MAIN",
    "subject": "Math"
  }'
```

#### Expected Response (200 OK)
```json
{
  "is_valid": true,
  "quality_score": 85,
  "issues": [],
  "warnings": ["Question could be more concise"],
  "category_scores": {
    "structure": 100,
    "quality": 90,
    "context": 95
  },
  "validation_details": {
    "question_length": "appropriate",
    "options_distinct": true,
    "answer_in_options": true,
    "grammar_correct": true,
    "syllabus_aligned": true,
    "difficulty_appropriate": true
  }
}
```

#### Validation Categories
- **Structure**: Question length, options format, answer placement
- **Quality**: Distinct options, no placeholders, grammar
- **Context**: Syllabus alignment, topic relevance

#### Features
- Multi-category scoring (structure, quality, context)
- Detailed issue reporting
- Quality score (0-100)
- Non-critical warnings

#### Use Cases
- Validating manually created questions
- Quality assurance
- Pre-submission checks

#### Error Scenarios
- **400 Bad Request:** Invalid question format
- **500 Internal Server Error:** Validation failed

---

### 5. Search Questions

**Endpoint:** `POST /api/questions/search`

**Description:** Search questions using multiple filter criteria.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/questions/search?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "JEE_MAIN",
    "subject": "Math",
    "difficulty": "medium",
    "min_quality_score": 80,
    "question_type": "single_correct",
    "topic": "Calculus"
  }'
```

#### Expected Response (200 OK)
```json
{
  "questions": [
    {
      "question_id": "q_ghi789",
      "question": "Evaluate the limit: lim(x→0) (sin(2x)/x)",
      "options": {
        "A": "0",
        "B": "1",
        "C": "2",
        "D": "∞"
      },
      "correct_answer": "C",
      "explanation": "Using the standard limit sin(x)/x → 1 as x→0, we have sin(2x)/x = 2(sin(2x)/(2x)) → 2×1 = 2.",
      "difficulty": "medium",
      "topic": "Calculus",
      "subject": "Math",
      "exam_type": "JEE_MAIN",
      "question_type": "single_correct",
      "metadata": {
        "validation_score": 88
      }
    }
  ],
  "total_count": 1,
  "avg_quality_score": 88.0,
  "topics_covered": ["Calculus"],
  "generation_time": 0.0
}
```

#### Supported Filters
- `exam_type`: JEE_MAIN, JEE_ADVANCED, NEET
- `subject`: Physics, Chemistry, Math, Biology
- `topic`: Any topic name
- `difficulty`: easy, medium, hard
- `min_quality_score`: Minimum validation score (0-100)
- `question_type`: single_correct, multiple_correct, numerical

#### Features
- Multi-criteria filtering
- Quality-based filtering
- Pagination support
- Aggregate statistics

#### Use Cases
- Advanced question search
- Building filtered question sets
- Quality-based curation

#### Error Scenarios
- **400 Bad Request:** Invalid filter criteria
- **500 Internal Server Error:** Search failed

---

### 6. Get Question Statistics

**Endpoint:** `GET /api/questions/stats`

**Description:** Get comprehensive statistics about questions in database.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/questions/stats?exam_type=JEE_MAIN&subject=Math" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `exam_type`: Filter stats by exam type
- `subject`: Filter stats by subject

#### Expected Response (200 OK)
```json
{
  "total_questions": 500,
  "by_topic": {
    "Calculus": 50,
    "Algebra": 45,
    "Mechanics": 60,
    "Thermodynamics": 40,
    "Organic Chemistry": 35
  },
  "by_difficulty": {
    "easy": 150,
    "medium": 250,
    "hard": 100
  },
  "by_exam_type": {
    "JEE_MAIN": 300,
    "JEE_ADVANCED": 200,
    "NEET": 150
  },
  "by_subject": {
    "Physics": 180,
    "Chemistry": 160,
    "Math": 160,
    "Biology": 50
  },
  "by_question_type": {
    "single_correct": 400,
    "multiple_correct": 75,
    "numerical": 25
  },
  "avg_quality_score": 85.5,
  "quality_distribution": {
    "90-100": 200,
    "80-89": 200,
    "70-79": 75,
    "below_70": 25
  },
  "filters_applied": {
    "exam_type": "JEE_MAIN",
    "subject": "Math"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Statistics Included
- Total questions count
- Questions by topic
- Questions by difficulty
- Questions by exam type
- Questions by subject
- Average quality score
- Quality distribution

#### Use Cases
- Dashboard metrics
- Content gap analysis
- Quality monitoring
- Capacity planning

#### Error Scenarios
- **500 Internal Server Error:** Statistics retrieval failed

---

## Testing Workflows

### Complete Question Management Workflow

1. **Generate New Questions**
   ```bash
   curl -X POST "/api/questions/generate" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"topic": "Calculus", "exam_type": "JEE_MAIN", "difficulty": "medium", "num_questions": 5}'
   ```

2. **Validate Question Quality**
   ```bash
   curl -X POST "/api/questions/validate" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"question": "...", "options": {...}, "correct_answer": "A"}'
   ```

3. **Search for Questions**
   ```bash
   curl -X POST "/api/questions/search" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"exam_type": "JEE_MAIN", "subject": "Math", "difficulty": "medium"}'
   ```

4. **Get Questions by Topic**
   ```bash
   curl -X GET "/api/questions/by-topic/Calculus?exam_type=JEE_MAIN&limit=10" \
     -H "Authorization: Bearer TOKEN"
   ```

5. **Get Specific Question**
   ```bash
   curl -X GET "/api/questions/q_abc123" \
     -H "Authorization: Bearer TOKEN"
   ```

6. **Get Statistics**
   ```bash
   curl -X GET "/api/questions/stats?exam_type=JEE_MAIN" \
     -H "Authorization: Bearer TOKEN"
   ```

---

## RAG (Retrieval-Augmented Generation) Details

### RAG Pipeline Process
1. **Context Retrieval**: Fetches relevant syllabus content
2. **Knowledge Integration**: Combines context with AI capabilities
3. **Question Generation**: Creates contextually relevant questions
4. **Quality Validation**: Ensures educational standards
5. **Metadata Enrichment**: Adds validation and tracking data

### Context Sources
- Exam syllabus documents
- Previous year questions
- Concept explanations
- Practice problem sets
- Educational resources

### Quality Assurance
- Structural validation (format, grammar)
- Educational alignment (syllabus mapping)
- Difficulty calibration (consistent standards)
- Answer verification (accuracy checks)

---

## Common Issues and Solutions

### 1. Question Generation Failed
**Problem:** Getting 500 error when generating questions
**Solution:** 
- Verify topic exists in syllabus
- Check exam_type and difficulty are valid
- Ensure num_questions is reasonable (1-50)
- Check Gemini API service status

### 2. Low Quality Scores
**Problem:** Generated questions have low validation scores
**Solution:** 
- Check if topic is well-defined
- Verify sufficient context is available
- Review question complexity
- Consider breaking down broad topics

### 3. Search Returns No Results
**Problem:** Search endpoint returns empty results
**Solution:** 
- Verify filter combinations are realistic
- Check if questions exist for criteria
- Try broader search terms
- Review question database population

### 4. Validation Errors
**Problem:** Question validation returns low scores
**Solution:** 
- Ensure all required fields are present
- Check options are distinct and plausible
- Verify correct answer is in options
- Review question clarity and grammar

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing the Question Router in Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Question Router uses RAG (Retrieval-Augmented Generation) with Gemini AI
- Questions are generated based on syllabus context and educational standards
- Quality validation includes structure, content, and educational alignment
- Questions support JEE_MAIN, JEE_ADVANCED, and NEET exam patterns
- RAG pipeline retrieves context from syllabus documents before generation

**Question:** Can you help me debug this issue by:
1. Analyzing the RAG generation request and response
2. Checking if question format and content are appropriate
3. Identifying common quality validation issues
4. Suggesting specific fixes or debugging steps

**Additional Information:**
- Topic: [TOPIC_NAME]
- Exam Type: [EXAM_TYPE]
- Difficulty: [DIFFICULTY_LEVEL]
- Validation Score: [SCORE_IF_AVAILABLE]
- [Add any relevant logs or observations]
```

---

## Related Models and Services

### Models
- `models.rag_models.RAGRequest`
- `models.rag_models.RAGResponse`
- `models.question_models.Question`
- `models.question_models.QuestionFilter`
- `models.question_models.QuestionBatch`
- `models.question_models.QuestionMetadata`

### Services
- `services.rag_service.RAGService`
- `services.question_validator.QuestionValidator`

### Database
- Firestore collection: `questions`
- Indexes: topic, exam_type, difficulty, subject

---

## Performance Considerations

1. **RAG Generation**: Takes 2-5 seconds per question batch
2. **Quality Validation**: Automated scoring takes 0.5-1 second
3. **Search Performance**: Optimized with Firestore indexes
4. **Caching**: Generated questions cached for 24 hours
5. **Batch Operations**: Support for bulk generation (up to 50 questions)

---

## Security Notes

1. **Access Control:** All endpoints require JWT authentication
2. **Input Validation:** All inputs validated before processing
3. **Content Filtering:** Generated content filtered for appropriateness
4. **Quality Assurance:** All questions pass quality validation
5. **Audit Trail**: All generation and modifications are logged

---

## Testing Best Practices

1. **RAG Testing**: Test with various topics and complexity levels
2. **Quality Validation**: Test validation with different question types
3. **Search Testing**: Test various filter combinations
4. **Performance Testing**: Test with large question sets
5. **Edge Cases**: Test with invalid or edge-case inputs