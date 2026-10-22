# Design Document

## Overview

Mentor AI is a comprehensive EdTech platform that enables parents to guide their children through competitive exam preparation (JEE Main, JEE Advanced, NEET, MHT CET) at home, eliminating the need for expensive coaching classes. The platform features a dual-user system where parents create and manage accounts while students access personalized learning content. The system leverages AI (Gemini Flash) for intelligent study planning, diagnostic analytics, and adaptive scheduling based on exam dates and student performance.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Parent Web App  │         │ Student Web App  │         │
│  │  (React/Next.js) │         │ (React/Next.js)  │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway Layer                          │
│              (Authentication & Routing)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Auth       │  │   User       │  │  Diagnostic  │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Analytics   │  │  Schedule    │  │   Payment    │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Question    │  │  Teaching    │  │   Content    │     │
│  │  Generation  │  │  Resources   │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI/ML Layer (Vertex AI)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Gemini Flash │  │  Google RAG  │  │   Pattern    │     │
│  │   (Study     │  │  (Question   │  │   Analysis   │     │
│  │   Planning)  │  │  Generation) │  │   Engine     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Vector     │  │  Text-to-    │                        │
│  │   Search     │  │   Speech     │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer (Firebase + GCP)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Firebase   │  │    Vector    │  │   Firebase   │     │
│  │  Firestore   │  │    Search    │  │   Storage    │     │
│  │   (NoSQL)    │  │  (Syllabus)  │  │   (Files)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Google     │  │   Razorpay   │  │   Email/SMS  │     │
│  │    OAuth     │  │   Payment    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- React.js / Next.js for web application
- Tailwind CSS for styling
- Multi-language support (i18n)
- Responsive design for mobile and desktop

**Backend:**
- Python with FastAPI
- RESTful API architecture
- JWT-based authentication
- Async/await for high performance
- Pydantic for data validation
- Compatible with Google Cloud Run for serverless deployment

**AI/ML:**
- Google Gemini Flash API for study planning and analytics
- Google RAG (Retrieval-Augmented Generation) for context-aware content generation
- LLM for question generation with RAG
- Google Vector Search (Vertex AI) for syllabus embeddings

**Database:**
- Firebase Firestore for primary NoSQL data storage
- Firebase Realtime Database for real-time updates
- Firebase Authentication for user management
- Google Vector Search for syllabus content and semantic search

**External Integrations:**
- Firebase Authentication (Google OAuth, Email, Phone)
- Razorpay for payment processing
- Firebase Cloud Messaging for notifications
- Google Text-to-Speech API for audio summaries

**Cloud Infrastructure:**
- Google Cloud Run for containerized API deployment
- Firebase Firestore for NoSQL database
- Firebase Storage for file uploads and static assets
- Vertex AI for Vector Search and RAG
- Firebase Hosting for frontend deployment

## Components and Interfaces

### 1. Authentication Service (Firebase Auth)

**Responsibilities:**
- Handle parent registration (email, phone, Google OAuth) via Firebase Auth
- Manage login sessions for parents and students
- Generate and manage student credentials
- Password reset and verification

**Firebase Auth Integration:**
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import firebase_admin
from firebase_admin import auth, firestore

# Initialize Firebase
firebase_admin.initialize_app()
db = firestore.client()

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class ParentRegister(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    google_token: Optional[str] = None
    language: str

@router.post("/register/parent")
async def register_parent(data: ParentRegister):
    """Register new parent account using Firebase Auth"""
    try:
        if data.google_token:
            # Verify Google token
            decoded_token = auth.verify_id_token(data.google_token)
            uid = decoded_token['uid']
        elif data.email:
            # Create email user
            user = auth.create_user(email=data.email)
            uid = user.uid
            # Send verification email
            auth.generate_email_verification_link(data.email)
        elif data.phone:
            # Create phone user
            user = auth.create_user(phone_number=data.phone)
            uid = user.uid
        
        # Store parent profile in Firestore
        db.collection('parents').document(uid).set({
            'language': data.language,
            'created_at': firestore.SERVER_TIMESTAMP,
            'subscription_status': 'FREE'
        })
        
        return {"parent_id": uid, "verification_required": bool(data.email)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(firebase_token: str):
    """Verify Firebase token and return user profile"""
    try:
        decoded_token = auth.verify_id_token(firebase_token)
        uid = decoded_token['uid']
        
        # Check if parent or student
        parent_doc = db.collection('parents').document(uid).get()
        if parent_doc.exists:
            return {
                "user_type": "parent",
                "profile": parent_doc.to_dict()
            }
        
        student_doc = db.collection('students').document(uid).get()
        if student_doc.exists:
            return {
                "user_type": "student",
                "profile": student_doc.to_dict()
            }
        
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Key APIs:**
```
POST /api/auth/register/parent
  - Body: { email?, phone?, googleToken?, language }
  - Response: { parentId, verificationRequired }

POST /api/auth/verify
  - Body: { parentId, code }
  - Response: { token, parentProfile }

POST /api/auth/login
  - Body: { email/phone/googleToken, password? }
  - Response: { token, userType, profile }

POST /api/auth/student/credentials
  - Body: { parentId, childId }
  - Response: { username, password }
```

### 2. User Service

**Responsibilities:**
- Manage parent and student profiles
- Handle child onboarding (one child per parent)
- Store preferences (language, study times, educational background)
- Manage exam selection and exam dates

**Key APIs:**
```
POST /api/users/parent/preferences
  - Body: { language, notificationPrefs, studyTimes, education }
  
POST /api/users/child
  - Body: { name, age, grade, school, prepStatus }
  - Response: { childId, studentCredentials }

PUT /api/users/child/{childId}/exam
  - Body: { examType, session, year, examDate }
  
GET /api/users/parent/dashboard
  - Response: { childProfile, progress, schedule, analytics }
```

### 3. Diagnostic Test Service

**Responsibilities:**
- Generate 200-question diagnostic tests based on exam type
- Apply 10-year pattern analysis for question distribution
- Implement weightage system and negative marking
- Save responses and calculate scores

**Key APIs:**
```
POST /api/diagnostic/generate
  - Body: { examType, childId }
  - Response: { testId, questions[], duration, instructions }

POST /api/diagnostic/submit-answer
  - Body: { testId, questionId, answer }
  - Response: { saved: true }

POST /api/diagnostic/submit-test
  - Body: { testId }
  - Response: { overallScore, topicScores, analyticsId }
```

**Data Model:**
```typescript
interface DiagnosticTest {
  id: string;
  childId: string;
  examType: 'JEE_MAIN' | 'JEE_ADVANCED' | 'NEET' | 'MHT_CET';
  questions: Question[];
  startedAt: Date;
  submittedAt?: Date;
  overallScore?: number;
  topicScores: TopicScore[];
}

interface Question {
  id: string;
  topic: string;
  subtopic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  type: 'MCQ' | 'MULTIPLE_CORRECT' | 'INTEGER';
  question: string;
  options: string[];
  correctAnswer: string | string[];
  explanation: string;
  weightage: number;
}
```

### 4. Analytics Service

**Responsibilities:**
- Use Gemini Flash to analyze diagnostic test results
- Identify weak subjects and topics with percentages
- Generate improvement strategies
- Provide parent-specific guidance

**Key APIs:**
```
POST /api/analytics/generate
  - Body: { testId, topicWeightages }
  - Response: { analyticsId, weakSubjects, weakTopics, strategies }

GET /api/analytics/{analyticsId}
  - Response: { 
      weakSubjects: SubjectAnalysis[],
      weakTopics: TopicAnalysis[],
      strategies: ImprovementStrategy[],
      visualCharts: ChartData[]
    }
```

**Gemini Flash Integration:**
```typescript
interface AnalyticsPrompt {
  diagnosticResults: {
    overallScore: number;
    subjectScores: { subject: string; score: number; weightage: number }[];
    topicScores: { topic: string; score: number; weightage: number }[];
  };
  examType: string;
  daysRemaining: number;
  
  prompt: `
    Analyze the following diagnostic test results for ${examType}:
    - Overall Score: ${overallScore}%
    - Subject Scores: ${JSON.stringify(subjectScores)}
    - Topic Scores: ${JSON.stringify(topicScores)}
    - Days until exam: ${daysRemaining}
    
    Provide:
    1. Weak subjects (< 60%) with specific reasons
    2. Weak topics within each subject with accuracy percentages
    3. Improvement strategies for each weak area considering topic weightage
    4. Recommended focus areas with time estimates
    5. Parent-specific guidance on how to help
  `;
}
```

### 5. Schedule Service

**Responsibilities:**
- Use Gemini Flash to generate day-by-day study schedules
- Consider exam date, weak areas, topic weightages
- Implement adaptive rescheduling for missed sessions
- Adjust schedule based on practice test performance

**Key APIs:**
```
POST /api/schedule/generate
  - Body: { childId, analyticsId, examDate, preferences }
  - Response: { scheduleId, dailyTasks[], milestones[] }

GET /api/schedule/{scheduleId}
  - Response: { schedule, progress, adjustments }

POST /api/schedule/reschedule
  - Body: { scheduleId, reason: 'MISSED_SESSION' | 'PRACTICE_TEST' }
  - Response: { updatedSchedule, changes[] }
```

**Gemini Flash Integration:**
```typescript
interface SchedulePrompt {
  analyticsData: AnalyticsResult;
  examDate: Date;
  daysRemaining: number;
  topicWeightages: { topic: string; weightage: number }[];
  preferredStudyTimes: string[];
  currentPrepStatus: string;
  
  prompt: `
    Generate a day-by-day study schedule for ${examType} preparation:
    - Exam Date: ${examDate}
    - Days Remaining: ${daysRemaining}
    - Weak Topics: ${JSON.stringify(weakTopics)}
    - Topic Weightages: ${JSON.stringify(topicWeightages)}
    - Preferred Study Times: ${preferredStudyTimes}
    
    Requirements:
    1. Prioritize high-weightage weak topics
    2. Allocate time proportional to weightage and weakness
    3. Include practice modules, review sessions, mock tests
    4. Maintain realistic daily study hours (4-6 hours)
    5. Include weekly milestones and monthly goals
    6. Provide daily task breakdown with estimated hours
  `;
}
```

### 6. Question Generation Service (Google RAG)

**Responsibilities:**
- Generate practice questions using Google RAG
- Retrieve syllabus context from Google Vector Search
- Ensure questions match exam pattern and difficulty
- Implement adaptive difficulty based on performance

**Google RAG Integration:**
```python
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# Initialize RAG with Vector Search
rag_corpus = aiplatform.RagCorpus(
    display_name="exam_syllabus",
    vector_search_config={
        "index_endpoint": vector_search_endpoint,
        "index": syllabus_index
    }
)

# Generate questions with RAG
def generate_questions(topic: str, difficulty: str, exam_type: str):
    # RAG retrieves relevant syllabus content
    context = rag_corpus.retrieve(
        query=f"{topic} {exam_type} syllabus",
        top_k=5
    )
    
    # Gemini generates questions with retrieved context
    model = GenerativeModel("gemini-2.5-flash-lite")
    prompt = f"""
    Using the following syllabus context:
    {context}
    
    Generate 10 {difficulty} level questions for {topic} in {exam_type} format.
    Include: question, 4 options, correct answer, explanation.
    """
    
    response = model.generate_content(prompt)
    return parse_questions(response.text)
```

**Key APIs:**
```
POST /api/questions/generate
  - Body: { topic, difficulty, count, examType }
  - Response: { questions[] }

POST /api/questions/practice-session
  - Body: { childId, topic, sessionType }
  - Response: { sessionId, questions[] }
```

### 7. Teaching Resources Service

**Responsibilities:**
- Generate teaching notes in native language using Gemini Flash
- Create teaching methodology guides
- Generate mindmaps and audio summaries
- Provide prerequisite concepts for parents

**Key APIs:**
```
GET /api/teaching/notes/{topic}
  - Query: { language, examType }
  - Response: { notes, examples, formulas }

GET /api/teaching/methodology/{topic}
  - Response: { teachingGuide, commonDifficulties, activities }

GET /api/teaching/mindmap/{topic}
  - Query: { language }
  - Response: { mindmapData, imageUrl }

GET /api/teaching/audio-summary/{topic}
  - Query: { language }
  - Response: { audioUrl, transcript }
```

### 8. Payment Service

**Responsibilities:**
- Integrate with Razorpay for payment processing
- Manage subscription plans and renewals
- Handle refunds and payment history
- Update account status on successful payment

**Key APIs:**
```
POST /api/payment/create-order
  - Body: { parentId, planId }
  - Response: { orderId, razorpayOrderId, amount }

POST /api/payment/verify
  - Body: { orderId, razorpayPaymentId, razorpaySignature }
  - Response: { verified, subscriptionActive }

GET /api/payment/history/{parentId}
  - Response: { transactions[], currentPlan, renewalDate }

POST /api/payment/refund
  - Body: { paymentId, reason }
  - Response: { refundId, status }
```

## Data Models (Firestore Collections)

### Firestore Structure

```
/parents/{parentId}
  - email: string
  - phone: string
  - language: string
  - preferences: map
    - notifications: boolean
    - studyTimes: array
    - educationalBackground: string
  - subscriptionStatus: string (FREE | PREMIUM)
  - subscriptionExpiry: timestamp
  - createdAt: timestamp

/students/{studentId}
  - parentId: string (reference to parent)
  - name: string
  - age: number
  - grade: number
  - school: string
  - prepStatus: string (NOT_STARTED | SELF_STUDYING | ATTENDING_COACHING)
  - firebaseUid: string (for authentication)
  - examType: string (JEE_MAIN | JEE_ADVANCED | NEET | MHT_CET)
  - examSession: string
  - examYear: number
  - examDate: timestamp
  - diagnosticCompleted: boolean
  - createdAt: timestamp

/diagnostic_tests/{testId}
  - studentId: string (reference)
  - examType: string
  - questions: array
  - responses: map
  - startedAt: timestamp
  - submittedAt: timestamp
  - overallScore: number
  - topicScores: array

/analytics/{analyticsId}
  - testId: string (reference)
  - studentId: string (reference)
  - weakSubjects: array
  - weakTopics: array
  - strategies: array
  - generatedAt: timestamp

/schedules/{scheduleId}
  - studentId: string (reference)
  - analyticsId: string (reference)
  - examDate: timestamp
  - dailyTasks: array
  - milestones: array
  - adjustments: array
  - lastModified: timestamp

/payments/{paymentId}
  - parentId: string (reference)
  - razorpayOrderId: string
  - razorpayPaymentId: string
  - amount: number
  - status: string
  - createdAt: timestamp
```

### Python Models (Pydantic)

```python
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SubscriptionStatus(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"

class ExamType(str, Enum):
    JEE_MAIN = "JEE_MAIN"
    JEE_ADVANCED = "JEE_ADVANCED"
    NEET = "NEET"
    MHT_CET = "MHT_CET"

class Parent(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    language: str
    preferences: dict
    subscription_status: SubscriptionStatus
    subscription_expiry: Optional[datetime] = None
    created_at: datetime

class Student(BaseModel):
    id: str
    parent_id: str
    name: str
    age: int
    grade: int
    school: str
    prep_status: str
    firebase_uid: str
    exam_type: ExamType
    exam_session: str
    exam_year: int
    exam_date: datetime
    diagnostic_completed: bool
    created_at: datetime
```

### Test and Analytics Models

```typescript
interface TopicScore {
  topic: string;
  subtopic: string;
  totalQuestions: number;
  correctAnswers: number;
  score: number;
  weightage: number;
  category: 'WEAK' | 'MODERATE' | 'STRONG';
}

interface Analytics {
  id: string;
  testId: string;
  childId: string;
  weakSubjects: SubjectAnalysis[];
  weakTopics: TopicAnalysis[];
  strategies: ImprovementStrategy[];
  generatedAt: Date;
}

interface SubjectAnalysis {
  subject: string;
  score: number;
  weightage: number;
  weakTopics: string[];
  reason: string;
}

interface ImprovementStrategy {
  topic: string;
  weightage: number;
  focusAreas: string[];
  studyTechniques: string[];
  estimatedTime: string;
  parentGuidance: string;
}
```

### Schedule Models

```typescript
interface Schedule {
  id: string;
  childId: string;
  analyticsId: string;
  examDate: Date;
  generatedAt: Date;
  lastModified: Date;
  dailyTasks: DailyTask[];
  milestones: Milestone[];
  adjustments: ScheduleAdjustment[];
}

interface DailyTask {
  date: Date;
  topics: string[];
  activities: Activity[];
  estimatedHours: number;
  completed: boolean;
}

interface Activity {
  type: 'PRACTICE' | 'REVIEW' | 'MOCK_TEST' | 'CONCEPT_LEARNING';
  topic: string;
  duration: number;
  weightage: number;
}

interface ScheduleAdjustment {
  date: Date;
  reason: 'MISSED_SESSION' | 'PRACTICE_TEST_PERFORMANCE';
  changes: string[];
}
```

## Error Handling

### Error Response Format

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: Date;
  path: string;
}
```

### Error Codes

- `AUTH_001`: Invalid credentials
- `AUTH_002`: Verification required
- `AUTH_003`: Google OAuth failed
- `USER_001`: Child limit reached (only one child allowed)
- `USER_002`: Invalid exam selection
- `TEST_001`: Diagnostic test generation failed
- `TEST_002`: Invalid test submission
- `ANALYTICS_001`: Gemini Flash API error
- `SCHEDULE_001`: Schedule generation failed
- `PAYMENT_001`: Razorpay payment failed
- `PAYMENT_002`: Invalid payment verification

### Retry Logic

- Gemini Flash API calls: Retry up to 3 times with exponential backoff
- Payment verification: Retry up to 2 times
- Database operations: Retry once on connection failure

## Testing Strategy

### Unit Tests
- Test individual service methods
- Mock external dependencies (Gemini Flash, Razorpay, Google OAuth)
- Test data validation and transformation logic
- Test error handling and edge cases

### Integration Tests
- Test API endpoints with real database
- Test authentication flows (email, phone, Google)
- Test diagnostic test flow end-to-end
- Test payment integration with Razorpay sandbox
- Test schedule generation and rescheduling

### E2E Tests
- Parent registration and onboarding flow
- Student login and diagnostic test
- Analytics generation and viewing
- Schedule creation and adaptive rescheduling
- Payment and subscription upgrade

### Performance Tests
- Load test diagnostic test generation (100 concurrent users)
- Test Gemini Flash API response times
- Test database query performance
- Test caching effectiveness

### Security Tests
- Test authentication and authorization
- Test SQL injection prevention
- Test XSS prevention
- Test payment security (PCI compliance)
- Test data encryption at rest and in transit

## Firebase Setup and Configuration

### Firebase Project Structure

```
mentor-ai-dev (Development)
├── Firestore Database
├── Authentication
├── Storage
└── Hosting

mentor-ai-staging (Staging)
├── Firestore Database
├── Authentication
├── Storage
└── Hosting

mentor-ai-prod (Production)
├── Firestore Database
├── Authentication
├── Storage
└── Hosting
```

### Firebase Security Rules

**Firestore Rules:**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Parents can only access their own data
    match /parents/{parentId} {
      allow read, write: if request.auth.uid == parentId;
    }
    
    // Students can read their own data, parents can read/write
    match /students/{studentId} {
      allow read: if request.auth.uid == studentId 
                  || request.auth.uid == resource.data.parentId;
      allow write: if request.auth.uid == resource.data.parentId;
    }
    
    // Diagnostic tests - students can read/write their own
    match /diagnostic_tests/{testId} {
      allow read, write: if request.auth.uid == resource.data.studentId
                         || request.auth.uid == get(/databases/$(database)/documents/students/$(resource.data.studentId)).data.parentId;
    }
    
    // Analytics - read only for student and parent
    match /analytics/{analyticsId} {
      allow read: if request.auth.uid == resource.data.studentId
                  || request.auth.uid == get(/databases/$(database)/documents/students/$(resource.data.studentId)).data.parentId;
    }
    
    // Schedules - read only for student and parent
    match /schedules/{scheduleId} {
      allow read: if request.auth.uid == resource.data.studentId
                  || request.auth.uid == get(/databases/$(database)/documents/students/$(resource.data.studentId)).data.parentId;
    }
    
    // Payments - parents only
    match /payments/{paymentId} {
      allow read: if request.auth.uid == resource.data.parentId;
    }
  }
}
```

**Storage Rules:**
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // User uploads
    match /uploads/{userId}/{allPaths=**} {
      allow read, write: if request.auth.uid == userId;
    }
    
    // Public assets
    match /public/{allPaths=**} {
      allow read: if true;
    }
  }
}
```

### Firebase Admin SDK Integration

```python
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from fastapi import FastAPI

# Initialize Firebase Admin
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'mentor-ai-prod',
    'storageBucket': 'mentor-ai-prod.appspot.com'
})

# Get Firestore client
db = firestore.client()

# Get Storage bucket
bucket = storage.bucket()

# Example: Create parent document
def create_parent(parent_id: str, data: dict):
    db.collection('parents').document(parent_id).set(data)

# Example: Query students by parent
def get_students_by_parent(parent_id: str):
    students = db.collection('students')\
        .where('parentId', '==', parent_id)\
        .stream()
    return [student.to_dict() for student in students]

# Example: Real-time listener
def listen_to_schedule_changes(schedule_id: str, callback):
    doc_ref = db.collection('schedules').document(schedule_id)
    doc_watch = doc_ref.on_snapshot(callback)
    return doc_watch
```

### Firebase Emulator for Local Development

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize Firebase emulators
firebase init emulators

# Start emulators
firebase emulators:start

# Emulators running on:
# - Firestore: localhost:8080
# - Authentication: localhost:9099
# - Storage: localhost:9199
```

```python
# Connect to emulators in development
import os

if os.getenv('ENVIRONMENT') == 'development':
    os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
    os.environ['FIREBASE_AUTH_EMULATOR_HOST'] = 'localhost:9099'
    os.environ['FIREBASE_STORAGE_EMULATOR_HOST'] = 'localhost:9199'
```

## Google Vector Search Setup

### Syllabus Embedding and Indexing

**1. Prepare Syllabus Data:**
```python
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

# Initialize embedding model
embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

# Chunk syllabus content
def chunk_syllabus(syllabus_text: str, chunk_size: int = 500):
    """Break syllabus into 200-500 word chunks"""
    chunks = []
    # Implementation for chunking
    return chunks

# Generate embeddings
def generate_embeddings(chunks: list):
    embeddings = []
    for chunk in chunks:
        embedding = embedding_model.get_embeddings([chunk])[0].values
        embeddings.append({
            "id": chunk["id"],
            "embedding": embedding,
            "metadata": {
                "topic": chunk["topic"],
                "subject": chunk["subject"],
                "exam_type": chunk["exam_type"],
                "difficulty": chunk["difficulty"]
            }
        })
    return embeddings
```

**2. Create Vector Search Index:**
```python
# Create index
index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="exam_syllabus_index",
    dimensions=768,  # textembedding-gecko dimensions
    approximate_neighbors_count=10,
    distance_measure_type="DOT_PRODUCT_DISTANCE",
    leaf_node_embedding_count=500,
    leaf_nodes_to_search_percent=7,
)

# Deploy index to endpoint
index_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="exam_syllabus_endpoint",
    public_endpoint_enabled=True,
)

index_endpoint.deploy_index(
    index=index,
    deployed_index_id="syllabus_deployed",
    min_replica_count=1,
    max_replica_count=10,
)
```

**3. Query Vector Search:**
```python
def retrieve_syllabus_context(query: str, exam_type: str, top_k: int = 5):
    """Retrieve relevant syllabus chunks for question generation"""
    
    # Generate query embedding
    query_embedding = embedding_model.get_embeddings([query])[0].values
    
    # Search vector index
    response = index_endpoint.find_neighbors(
        deployed_index_id="syllabus_deployed",
        queries=[query_embedding],
        num_neighbors=top_k,
        filter=[{"exam_type": exam_type}]  # Filter by exam type
    )
    
    # Return relevant chunks
    return [neighbor.metadata for neighbor in response[0]]
```

**4. Update Syllabus:**
```python
def update_syllabus(new_chunks: list):
    """Update vector index when syllabus changes"""
    
    # Generate embeddings for new chunks
    new_embeddings = generate_embeddings(new_chunks)
    
    # Update index
    index.upsert_datapoints(
        datapoints=new_embeddings
    )
```

## Multi-Language Support

### Implementation Strategy

**Frontend:**
- Use i18next for internationalization
- Store translations in JSON files per language
- Support English, Hindi, Marathi, and other regional languages
- Allow language switching in real-time

**Backend:**
- Store user language preference in database
- Pass language parameter to Gemini Flash for content generation
- Use language-specific text-to-speech for audio summaries
- Translate technical terms with English reference in parentheses

**Content Generation:**
- All AI-generated content (notes, strategies, summaries) in user's language
- Mindmaps with labels in native language
- Audio summaries with proper pronunciation

## Performance Optimization

### Caching Strategy (In-Memory + Firestore)
- Cache diagnostic test questions in memory (1 hour TTL)
- Cache teaching resources in memory (24 hours TTL)
- Cache analytics results in Firestore (until new test taken)
- Cache schedule in Firestore (until adjustment needed)
- Use Python `functools.lru_cache` for frequently accessed data

### Firestore Optimization
- Create composite indexes for common queries:
  - `students` collection: (parentId, examType)
  - `diagnostic_tests` collection: (studentId, submittedAt)
  - `schedules` collection: (studentId, lastModified)
- Use Firestore offline persistence for mobile apps
- Implement pagination for large result sets
- Use Firestore transactions for atomic operations
- Batch writes for bulk operations

### AI API Optimization
- Batch Gemini Flash requests where possible
- Cache common prompts and responses
- Implement rate limiting to avoid quota exhaustion
- Use streaming responses for long-running operations

## Security Considerations

### Authentication
- JWT tokens with 24-hour expiry
- Refresh tokens for extended sessions
- Google OAuth with secure token validation
- Password hashing with bcrypt (10 rounds)

### Authorization
- Role-based access control (Parent, Student)
- Parents can only access their own child's data
- Students cannot modify exam settings or payment info
- API rate limiting per user

### Data Protection
- Encrypt sensitive data at rest (PII, payment info)
- Use HTTPS for all communications
- Implement CORS policies
- Sanitize all user inputs
- Regular security audits

### Payment Security
- PCI DSS compliance through Razorpay
- Never store card details
- Verify payment signatures
- Log all payment transactions

## Deployment Architecture

### Google Cloud Run Deployment

**Container Configuration:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for Cloud Run
EXPOSE 8080

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Cloud Run Service:**
- Serverless deployment with auto-scaling
- Min instances: 1 (to avoid cold starts)
- Max instances: 100
- Memory: 2GB per instance
- CPU: 2 vCPU per instance
- Timeout: 300 seconds
- Concurrency: 80 requests per instance

**Infrastructure Components:**
- **Cloud Run**: FastAPI application
- **Firebase Firestore**: NoSQL database for all application data
- **Firebase Authentication**: User authentication and management
- **Firebase Storage**: File uploads and static assets
- **Firebase Hosting**: Frontend deployment with CDN
- **Vertex AI**: Vector Search, Gemini Flash, RAG
- **Cloud Load Balancing**: Global load balancer
- **Cloud Armor**: DDoS protection and WAF

### Environments
- **Development**: Local with Firebase emulators + staging Vertex AI
- **Staging**: Cloud Run + Firebase staging project + staging Vector Search
- **Production**: Multi-region Cloud Run + Firebase production project + production Vertex AI

### Monitoring (Google Cloud Operations)
- **Cloud Logging**: Application and system logs
- **Cloud Monitoring**: Metrics, dashboards, alerts
- **Cloud Trace**: Distributed tracing for API calls
- **Cloud Profiler**: Performance profiling
- **Error Reporting**: Automatic error detection and grouping
- **Uptime Checks**: Health monitoring and alerting

### CI/CD Pipeline (Cloud Build)
```yaml
# cloudbuild.yaml
steps:
  # Run tests
  - name: 'python:3.11'
    entrypoint: 'pytest'
    args: ['tests/']
  
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/mentor-ai:$COMMIT_SHA', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/mentor-ai:$COMMIT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'mentor-ai-api'
      - '--image=gcr.io/$PROJECT_ID/mentor-ai:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
```

### Scaling Strategy
- **Horizontal Scaling**: Cloud Run auto-scales based on requests
- **Database Scaling**: Firestore automatically scales with usage
- **Authentication**: Firebase Auth handles millions of users
- **Vector Search**: Managed scaling by Vertex AI
- **Cost Optimization**: 
  - Cloud Run scales to zero when idle
  - Firestore pay-per-use pricing
  - Firebase free tier for development

## Future Enhancements

1. **Mobile Apps**: Native iOS and Android applications
2. **Offline Mode**: Download content for offline study
3. **Live Doubt Solving**: Real-time chat with AI tutor
4. **Peer Learning**: Connect students preparing for same exam
5. **Advanced Analytics**: Predictive rank estimation
6. **Gamification**: Badges, leaderboards, challenges
7. **Parent Community**: Forum and discussion boards
8. **Video Explanations**: AI-generated video tutorials
9. **Handwriting Recognition**: Solve problems on paper and upload
10. **Voice Assistant**: Voice-based interaction for hands-free learning
