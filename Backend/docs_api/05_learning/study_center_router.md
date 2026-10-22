# Study Center Router API Documentation

## Overview

The Study Center Router provides endpoints for the Study Center Learning Journey feature in Mentor AI platform. It handles topic management, learning materials generation, progress tracking, and personalized learning journeys with AI-powered content generation.

## Base URL
```
/api/study-center
```

## Endpoints

### 1. Get Available Topics

**Endpoint:** `GET /api/study-center/topics`

**Description:** Get all available topics for a student's exam type. Optionally filter by subject.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/topics?student_id=student_123&subject=Physics" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `student_id`: ID of the student (required)
- `subject`: Optional subject filter (Physics, Chemistry, Mathematics)

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Topics retrieved successfully",
  "data": {
    "topics": [
      {
        "topic_id": "T01",
        "topic_name": "Kinematics",
        "subject": "Physics",
        "chapter": "Mechanics",
        "difficulty": "medium",
        "estimated_hours": 5.0,
        "prerequisites": ["Basic Mathematics"],
        "is_completed": false,
        "completion_percentage": 0
      },
      {
        "topic_id": "T02",
        "topic_name": "Thermodynamics",
        "subject": "Physics",
        "chapter": "Thermodynamics",
        "difficulty": "hard",
        "estimated_hours": 8.0,
        "prerequisites": ["Kinematics", "Basic Chemistry"],
        "is_completed": false,
        "completion_percentage": 0
      }
    ],
    "total_count": 2
  }
}
```

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve topics

#### Troubleshooting
- Verify JWT token is valid and not expired
- Check student_id exists in system
- Ensure subject filter uses valid values

---

### 2. Get Topic Details

**Endpoint:** `GET /api/study-center/topics/{topic_id}`

**Description:** Get detailed information for a specific topic including progress and metadata.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/topics/T02" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Topic details retrieved successfully",
  "data": {
    "topic": {
      "topic_id": "T02",
      "topic_name": "Thermodynamics",
      "subject": "Physics",
      "chapter": "Thermodynamics",
      "difficulty": "hard",
      "estimated_hours": 8.0,
      "prerequisites": ["Kinematics", "Basic Chemistry"],
      "is_completed": false,
      "completion_percentage": 25,
      "last_studied": "2024-01-10T10:30:00Z",
      "study_sessions_count": 3,
      "average_session_duration": 45,
      "concepts_mastered": ["First Law of Thermodynamics"],
      "concepts_pending": ["Second Law", "Entropy"]
    }
  }
}
```

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve topic details

#### Troubleshooting
- Verify topic_id exists in syllabus
- Check if student has access to this topic
- Ensure topic is part of student's exam syllabus

---

### 3. Get Learning Materials

**Endpoint:** `GET /api/study-center/materials/{topic_id}`

**Description:** Get all learning materials (notes, mind map, teaching content) for a specific topic. Checks cache first.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/materials/T02" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Learning materials retrieved successfully",
  "data": {
    "topic_id": "T02",
    "topic_name": "Thermodynamics",
    "cached": true,
    "generated_at": "2024-01-15T10:30:00Z",
    "has_notes": true,
    "has_mind_map": true,
    "has_teaching_content": true,
    "notes": "Thermodynamics is the branch of physics that deals with heat and temperature...",
    "mind_map": {
      "mindmap_id": "mm_T02",
      "topic_id": "T02",
      "structure": {
        "central_concept": "Thermodynamics",
        "branches": [
          {
            "name": "Laws of Thermodynamics",
            "sub_branches": [
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
              "Isobaric"
            ]
          }
        ]
      },
      "text_representation": "Thermodynamics → Laws → First Law, Second Law..."
    },
    "teaching_content": {
      "teaching_id": "tc_T02",
      "topic_id": "T02",
      "introduction": "Thermodynamics is a fundamental branch of physics...",
      "key_concepts": [
        {
          "concept": "First Law of Thermodynamics",
          "explanation": "Energy cannot be created or destroyed...",
          "examples": ["Heat engine efficiency", "Internal energy changes"]
        }
      ],
      "examples": [
        {
          "title": "Calculating Work Done",
          "problem": "A gas expands from 2L to 5L at constant pressure...",
          "solution": "Using W = PΔV, W = 101325 Pa × (5-2)×10⁻³ m³...",
          "steps": ["Identify given values", "Apply formula", "Calculate result"]
        }
      ],
      "practice_problems": [
        {
          "problem_id": "pp_T02_1",
          "question": "Calculate the work done when...",
          "difficulty": "medium",
          "hints": ["Use the formula W = PΔV"],
          "solution": "The work done is..."
        }
      ]
    }
  }
}
```

#### Features
- Checks cache first for faster response
- Returns structured materials for different learning styles
- Includes metadata about generation and caching

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve learning materials

#### Troubleshooting
- Check if materials have been generated for this topic
- Verify student has access to this topic
- If materials not available, try force generation endpoint

---

### 4. Generate Learning Materials

**Endpoint:** `POST /api/study-center/materials/generate`

**Description:** Force regeneration of learning materials for a topic, bypassing cache if content exists.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/study-center/materials/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123",
    "topic_id": "T02",
    "material_type": "all"
  }'
```

#### Request Body
- `student_id`: ID of the student
- `topic_id`: ID of the topic
- `material_type`: Type to generate (notes, mind_map, teaching_content, all)

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Learning materials generated successfully",
  "data": {
    "topic_id": "T02",
    "topic_name": "Thermodynamics",
    "cached": false,
    "generated_at": "2024-01-15T11:00:00Z",
    "material_types": ["notes", "mind_map", "teaching_content"],
    "notes": "Freshly generated notes content...",
    "mind_map": {
      "mindmap_id": "mm_T02_new",
      "topic_id": "T02",
      "structure": {...},
      "text_representation": "Freshly generated mind map..."
    },
    "teaching_content": {
      "teaching_id": "tc_T02_new",
      "topic_id": "T02",
      "introduction": "Freshly generated teaching content...",
      "key_concepts": [...],
      "examples": [...],
      "practice_problems": [...]
    }
  }
}
```

#### Material Types
- `notes`: Text-based learning notes
- `mind_map`: Visual hierarchical structure
- `teaching_content`: Comprehensive teaching material with examples
- `all`: Generate all material types

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to generate materials

#### Troubleshooting
- Verify student exists and has access to topic
- Check if topic is part of student's exam syllabus
- Ensure material_type is valid
- Wait a few minutes for AI generation to complete

---

### 5. Get Mind Map

**Endpoint:** `GET /api/study-center/mindmap/{topic_id}`

**Description:** Get structured mind map for a specific topic.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/mindmap/T02" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Mind map retrieved successfully",
  "data": {
    "mindmap_id": "mm_T02",
    "topic_id": "T02",
    "structure": {
      "central_concept": "Thermodynamics",
      "branches": [
        {
          "name": "Laws of Thermodynamics",
          "sub_branches": [
            {
              "name": "First Law",
              "sub_branches": ["Energy Conservation", "Internal Energy"]
            },
            {
              "name": "Second Law",
              "sub_branches": ["Entropy", "Heat Flow"]
            }
          ]
        },
        {
          "name": "Thermodynamic Processes",
          "sub_branches": [
            {
              "name": "Isothermal Process",
              "sub_branches": ["Constant Temperature", "PV=nRT"]
            },
            {
              "name": "Adiabatic Process",
              "sub_branches": ["No Heat Transfer", "PV^γ=constant"]
            }
          ]
        }
      ]
    },
    "text_representation": "Thermodynamics → Laws → First Law (Energy Conservation, Internal Energy), Second Law (Entropy, Heat Flow) → Processes → Isothermal (Constant Temperature, PV=nRT), Adiabatic (No Heat Transfer, PV^γ=constant)"
  }
}
```

#### Features
- Hierarchical structure with central concept and branches
- Text representation for accessibility
- Optimized for visual learning

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve mind map

---

### 6. Get Teaching Content

**Endpoint:** `GET /api/study-center/teach/{topic_id}`

**Description:** Get AI-generated teaching content with examples for a specific topic.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/teach/T02" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Teaching content retrieved successfully",
  "data": {
    "teaching_id": "tc_T02",
    "topic_id": "T02",
    "introduction": "Thermodynamics is a fundamental branch of physics that deals with heat, work, and energy...",
    "key_concepts": [
      {
        "concept": "First Law of Thermodynamics",
        "explanation": "The first law states that energy cannot be created or destroyed, only transformed from one form to another...",
        "examples": [
          "Heat engine converting heat to mechanical work",
          "Refrigerator using work to transfer heat"
        ],
        "importance": "Fundamental principle governing all energy transformations"
      }
    ],
    "examples": [
      {
        "title": "Calculating Work Done in Isothermal Expansion",
        "problem": "2 moles of ideal gas expand isothermally at 300K from 10L to 20L...",
        "solution": "Using W = nRT ln(V₂/V₁), W = 2 × 8.314 × 300 × ln(20/10) = 2 × 8.314 × 300 × 0.693 = 3456 J...",
        "steps": [
          "Identify the process: Isothermal expansion",
          "Write the work formula: W = nRT ln(V₂/V₁)",
          "Substitute values and calculate"
        ]
      }
    ],
    "practice_problems": [
      {
        "problem_id": "pp_T02_1",
        "question": "A gas undergoes an adiabatic expansion from 5L to 15L. If the initial temperature is 400K and γ=1.4, find the final temperature.",
        "difficulty": "hard",
        "hints": [
          "Use the adiabatic relation: TV^(γ-1) = constant",
          "Remember: T₁V₁^(γ-1) = T₂V₂^(γ-1)"
        ],
        "solution": "Using T₁V₁^(γ-1) = T₂V₂^(γ-1): 400 × 5^(0.4) = T₂ × 15^(0.4)...",
        "answer_key": "T₂ ≈ 254K"
      }
    ]
  }
}
```

#### Content Structure
- Introduction with topic overview
- Key concepts with explanations and examples
- Worked examples with step-by-step solutions
- Practice problems with hints and solutions

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve teaching content

---

### 7. Get Student Progress

**Endpoint:** `GET /api/study-center/progress/{student_id}`

**Description:** Get comprehensive progress summary for a student including completion percentages and study time.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/progress/student_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Progress retrieved successfully",
  "data": {
    "student_id": "student_123",
    "overall_progress": {
      "completion_percentage": 35.5,
      "topics_completed": 7,
      "total_topics": 20,
      "total_study_hours": 45.5,
      "average_session_duration": 52,
      "study_streak": 5,
      "last_activity": "2024-01-15T14:30:00Z"
    },
    "subject_progress": {
      "Physics": {
        "completion_percentage": 40.0,
        "topics_completed": 4,
        "total_topics": 10,
        "strong_areas": ["Kinematics", "Waves"],
        "weak_areas": ["Thermodynamics", "Optics"]
      },
      "Chemistry": {
        "completion_percentage": 30.0,
        "topics_completed": 3,
        "total_topics": 10,
        "strong_areas": ["Organic Chemistry"],
        "weak_areas": ["Physical Chemistry", "Inorganic Chemistry"]
      },
      "Mathematics": {
        "completion_percentage": 36.7,
        "topics_completed": 0,
        "total_topics": 0,
        "strong_areas": [],
        "weak_areas": []
      }
    },
    "recent_sessions": [
      {
        "session_id": "sess_001",
        "topic_id": "T02",
        "topic_name": "Thermodynamics",
        "start_time": "2024-01-15T10:00:00Z",
        "end_time": "2024-01-15T10:45:00Z",
        "duration_minutes": 45,
        "completion_percentage": 15
      }
    ],
    "achievements": [
      {
        "achievement_id": "ach_7day_streak",
        "name": "Week Warrior",
        "earned_date": "2024-01-12T00:00:00Z"
      }
    ]
  }
}
```

#### Progress Metrics
- Overall completion percentage
- Subject-wise progress with strengths/weaknesses
- Study time analytics
- Recent session history
- Achievement tracking

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve progress

---

### 8. Start Learning Session

**Endpoint:** `POST /api/study-center/progress/start`

**Description:** Start a new learning session for tracking study time and progress.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/study-center/progress/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123",
    "topic_id": "T02",
    "topic_name": "Thermodynamics",
    "subject": "Physics"
  }'
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Learning session started successfully",
  "data": {
    "session_id": "session_abc123",
    "topic_id": "T02",
    "topic_name": "Thermodynamics",
    "start_time": "2024-01-15T10:00:00Z"
  }
}
```

#### Use Cases
- Track study time for analytics
- Monitor active learning sessions
- Enable session-based progress tracking

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to start session

---

### 9. Complete Learning Session

**Endpoint:** `POST /api/study-center/progress/complete`

**Description:** Mark a learning session as completed and update topic progress.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/study-center/progress/complete" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123",
    "topic_id": "T02",
    "session_id": "session_abc123"
  }'
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Learning session completed successfully",
  "data": {
    "session_id": "session_abc123",
    "duration_minutes": 45,
    "topic_progress_updated": {
      "topic_id": "T02",
      "previous_completion": 25,
      "new_completion": 35,
      "improvement": 10
    },
    "points_earned": 25,
    "achievements_unlocked": [
      {
        "achievement_id": "ach_first_thermo_session",
        "name": "Thermodynamics Beginner"
      }
    ]
  }
}
```

#### Progress Updates
- Calculates session duration
- Updates topic completion percentage
- Awards points and achievements
- Tracks learning patterns

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to complete session

---

### 10. Get Learning Journey

**Endpoint:** `GET /api/study-center/journey/{student_id}`

**Description:** Get personalized learning journey with recommended topics, prerequisites, and next steps.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/journey/student_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Learning journey retrieved successfully",
  "data": {
    "student_id": "student_123",
    "motivational_message": "You're making great progress! Keep up the excellent work in Physics.",
    "next_topic": {
      "topic_id": "T03",
      "topic_name": "Optics",
      "subject": "Physics",
      "difficulty": "medium",
      "estimated_hours": 6.0,
      "prerequisites_met": true,
      "priority": "high"
    },
    "prerequisites_pending": [
      {
        "topic_id": "T04",
        "topic_name": "Modern Physics",
        "subject": "Physics",
        "reason": "Not enough foundation in Quantum Mechanics",
        "suggested_prerequisite": "T05: Quantum Mechanics Basics"
      }
    ],
    "recommended_sequence": [
      {
        "topic_id": "T03",
        "topic_name": "Optics",
        "priority": "high",
        "reason": "Strong foundation in Mechanics"
      },
      {
        "topic_id": "T06",
        "topic_name": "Electromagnetism",
        "priority": "medium",
        "reason": "Good progress in related topics"
      },
      {
        "topic_id": "T02",
        "topic_name": "Thermodynamics",
        "priority": "low",
        "reason": "Revision recommended"
      }
    ],
    "journey_stats": {
      "total_topics_in_journey": 15,
      "completed_topics": 7,
      "estimated_completion_date": "2024-03-15",
      "on_track_percentage": 85
    }
  }
}
```

#### Journey Features
- Personalized recommendations based on progress
- Prerequisite tracking and warnings
- Optimized learning sequence
- Motivational messaging

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **500 Internal Server Error:** Failed to retrieve learning journey

---

### 11. Get Parent Insights

**Endpoint:** `GET /api/study-center/parent-progress/{child_id}`

**Description:** Get comprehensive progress insights for a parent to view their child's learning patterns.

**Authentication:** Required (JWT token - parent account)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/study-center/parent-progress/student_456?child_name=John" \
  -H "Authorization: Bearer PARENT_JWT_TOKEN"
```

#### Query Parameters
- `child_id`: ID of the child student (required)
- `child_name`: Name of the child (optional)

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Parent insights retrieved successfully",
  "data": {
    "child_id": "student_456",
    "child_name": "John",
    "overall_progress": 45.5,
    "topics_completed": 9,
    "total_topics": 20,
    "study_time_this_week": 12.5,
    "average_session_duration": 48,
    "strong_subjects": ["Physics"],
    "weak_subjects": ["Chemistry"],
    "recent_achievements": [
      {
        "achievement_id": "ach_7day_streak",
        "name": "Week Warrior",
        "earned_date": "2024-01-12T00:00:00Z"
      }
    ],
    "recommendations": [
      "Encourage your child to focus on Chemistry concepts",
      "Suggest additional practice time for weak areas",
      "Celebrate the excellent progress in Physics"
    ],
    "last_active": "2024-01-15T16:30:00Z",
    "weekly_goals_met": 3,
    "weekly_goals_total": 5
  }
}
```

#### Parent Dashboard Features
- Child's overall progress and subject performance
- Study time analytics and patterns
- Achievement and milestone tracking
- Actionable recommendations for support
- Goal setting and monitoring

#### Error Scenarios
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Not authorized to view this child's progress
- **500 Internal Server Error:** Failed to retrieve parent insights

---

## Testing Workflows

### Complete Learning Journey Workflow

1. **Get Available Topics**
   ```bash
   curl -X GET "/api/study-center/topics?student_id=student_123" \
     -H "Authorization: Bearer TOKEN"
   ```

2. **Get Topic Details**
   ```bash
   curl -X GET "/api/study-center/topics/T02" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **Get Learning Materials**
   ```bash
   curl -X GET "/api/study-center/materials/T02" \
     -H "Authorization: Bearer TOKEN"
   ```

4. **Start Learning Session**
   ```bash
   curl -X POST "/api/study-center/progress/start" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"student_id": "student_123", "topic_id": "T02", "topic_name": "Thermodynamics"}'
   ```

5. **Complete Learning Session**
   ```bash
   curl -X POST "/api/study-center/progress/complete" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"student_id": "student_123", "topic_id": "T02", "session_id": "session_abc123"}'
   ```

6. **Get Progress**
   ```bash
   curl -X GET "/api/study-center/progress/student_123" \
     -H "Authorization: Bearer TOKEN"
   ```

7. **Get Learning Journey**
   ```bash
   curl -X GET "/api/study-center/journey/student_123" \
     -H "Authorization: Bearer TOKEN"
   ```

---

## AI-Powered Features

### Content Generation
- **Notes**: AI-generated comprehensive study notes
- **Mind Maps**: Hierarchical visual structures
- **Teaching Content**: Full lessons with examples and practice problems
- **Personalization**: Adapted to student's learning level and progress

### Learning Analytics
- **Progress Tracking**: Session-based time and completion tracking
- **Performance Analysis**: Subject-wise strengths and weaknesses
- **Recommendation Engine**: AI-powered topic sequencing
- **Motivation**: Personalized messages and achievement system

### Adaptive Learning
- **Prerequisites**: Automatic prerequisite checking
- **Difficulty Adjustment**: Content adapts to student's level
- **Learning Path Optimization**: AI-optimized topic sequences
- **Study Pattern Recognition**: Identifies optimal study times

---

## Common Issues and Solutions

### 1. Materials Not Available
**Problem:** Getting empty materials for a topic
**Solution:** 
- Use the generate endpoint to create materials
- Check if topic is part of student's syllabus
- Wait for AI generation to complete (2-3 minutes)

### 2. Session Tracking Issues
**Problem:** Session start/complete not working
**Solution:** 
- Verify session_id is valid and matches
- Check student_id matches authenticated user
- Ensure proper request format

### 3. Progress Not Updating
**Problem:** Topic completion percentage not changing
**Solution:** 
- Ensure sessions are properly completed
- Check if session duration is sufficient (>5 minutes)
- Verify topic_id matches in start and complete calls

### 4. Parent Access Issues
**Problem:** Parents cannot see child's progress
**Solution:** 
- Verify parent-child relationship in database
- Check parent JWT token has proper permissions
- Ensure child_id is correct

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing Study Center Router in Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Study Center Router provides AI-powered learning materials and progress tracking
- Materials are generated using Gemini AI with syllabus context
- Progress tracking uses session-based analytics
- Learning journeys are personalized based on performance data
- Parent insights provide comprehensive child progress analytics

**Question:** Can you help me debug this issue by:
1. Analyzing the AI content generation request and response
2. Checking if the learning materials format is correct
3. Identifying common progress tracking issues
4. Suggesting specific fixes or debugging steps

**Additional Information:**
- Topic ID: [TOPIC_ID]
- Student ID: [STUDENT_ID]
- Material Type: [MATERIAL_TYPE_IF_APPLICABLE]
- Session ID: [SESSION_ID_IF_APPLICABLE]
- [Add any relevant logs or observations]
```

---

## Related Models and Services

### Models
- `models.study_center_models.Topic`
- `models.study_center_models.LearningMaterials`
- `models.study_center_models.MindMap`
- `models.study_center_models.TeachingContent`
- `models.study_center_models.LearningSession`
- `models.study_center_models.ProgressSummary`
- `models.study_center_models.LearningJourney`
- `models.study_center_models.ParentInsights`

### Services
- `services.study_center_service.StudyCenterService`
- `services.progress_tracker_service.ProgressTrackerService`
- `services.learning_material_service.LearningMaterialService`

### Authentication
- `middleware.testing_auth.get_current_user_testing`

---

## Performance Considerations

1. **Material Generation**: AI generation takes 2-5 seconds per material type
2. **Caching**: Materials cached for 24 hours
3. **Progress Tracking**: Lightweight session tracking
4. **Database Queries**: Optimized with Firestore indexes
5. **Batch Operations**: Support for multiple topic operations

---

## Security Notes

1. **Access Control**: Students can only access their own data
2. **Parent Access**: Separate authentication for parent endpoints
3. **Content Filtering**: AI-generated content is filtered and validated
4. **Session Security**: Session IDs are cryptographically generated
5. **Data Privacy**: All learning data is encrypted and access-controlled

---

## Testing Best Practices

1. **Material Generation**: Test with various topics and complexity levels
2. **Session Tracking**: Test complete session lifecycle
3. **Progress Accuracy**: Verify progress calculations are correct
4. **Parent Access**: Test parent-child relationship permissions
5. **AI Content**: Validate AI-generated content quality and relevance