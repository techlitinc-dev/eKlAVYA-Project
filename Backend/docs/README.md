# Mentor AI Platform - API Documentation

Welcome to the Mentor AI Platform API documentation! This folder contains comprehensive guides for testing and using the API.

## 📚 Documentation Files

### 1. [API Testing Guide](./API_TESTING_GUIDE.md)
**Complete guide for manual API testing**

- Getting started with the API
- Authentication flows
- Complete onboarding process
- Study center features
- Diagnostic test management
- Schedule generation
- Payment integration
- AI-powered features
- Testing tools and tips

**Best for:** Understanding the complete API workflow and testing manually

### 2. [Endpoint Reference](./ENDPOINT_REFERENCE.md)
**Complete endpoint reference documentation**

- All available endpoints organized by category
- Request/response formats
- Authentication requirements
- Error responses
- Rate limits
- Pagination and filtering

**Best for:** Quick lookup of endpoint details and specifications

### 3. [Quick Test Scenarios](./QUICK_TEST_SCENARIOS.md)
**Ready-to-use test scenarios with curl commands**

- Complete parent onboarding flow
- Student learning journey
- Diagnostic test flow
- AI-powered search
- Schedule management
- Payment flow
- Testing tips and troubleshooting

**Best for:** Quick testing with copy-paste curl commands

### 4. [Postman Collection](./Mentor_AI_Postman_Collection.json)
**Importable Postman collection**

- Pre-configured requests for all endpoints
- Environment variables
- Automatic token management
- Request examples

**Best for:** Testing with Postman GUI

## 🚀 Quick Start

### 1. Start the Server
```bash
./start-dev.sh
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Verify Server is Running
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "mentor-ai-backend"
}
```

### 3. Run Automated Tests
```bash
python3 run_endpoint_tests.py
```

### 4. Access Interactive Documentation
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

## 📖 Common Workflows

### Complete Onboarding Flow
1. Register parent → [Quick Test Scenarios](./QUICK_TEST_SCENARIOS.md#scenario-1-complete-parent-onboarding-flow)
2. Login
3. Set preferences
4. Create child profile
5. Select exam
6. Verify onboarding complete

### Student Learning
1. Child login
2. Browse topics
3. Get learning materials
4. Start learning session
5. Complete session
6. Check progress

### Diagnostic Test
1. Schedule test (parent)
2. Start test (child)
3. Submit answers
4. Get results

## 🔑 Authentication

Most endpoints require authentication. After login, include the token in requests:

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🛠️ Testing Tools

### 1. Automated Test Runner
```bash
python3 run_endpoint_tests.py
```

### 2. Postman
Import `Mentor_AI_Postman_Collection.json` into Postman

### 3. Curl Commands
See [Quick Test Scenarios](./QUICK_TEST_SCENARIOS.md) for ready-to-use commands

### 4. Python Requests
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login/email",
    json={"email": "test@example.com", "password": "pass123"}
)
print(response.json())
```

## 📊 API Categories

### Authentication & Authorization
- Parent registration and login
- Child login
- Token management
- Session handling

### Onboarding
- Parent preferences
- Child profile management
- Exam selection
- Onboarding status tracking

### Study Center
- Topic browsing
- Learning materials (notes, mind maps, teaching content)
- Progress tracking
- Learning sessions

### Diagnostic Tests
- Test scheduling
- Test lifecycle (start, submit, results)
- Test management
- Performance analytics

### Schedule Management
- AI-powered schedule generation
- Progress tracking
- Daily task management
- Schedule adaptation

### Payment & Subscriptions
- Subscription plans
- Payment processing (Razorpay)
- Subscription management
- Transaction history

### AI Features
- Vector search (Gemini-based)
- RAG question generation
- Semantic search
- Content generation

## 🔍 Finding Information

### Need to know...
- **How to test a specific feature?** → [API Testing Guide](./API_TESTING_GUIDE.md)
- **Endpoint details and formats?** → [Endpoint Reference](./ENDPOINT_REFERENCE.md)
- **Quick curl commands?** → [Quick Test Scenarios](./QUICK_TEST_SCENARIOS.md)
- **Want to use Postman?** → Import [Postman Collection](./Mentor_AI_Postman_Collection.json)

## ⚠️ Common Issues

### 401 Unauthorized
**Problem:** Token expired or invalid  
**Solution:** Login again to get a new token

### 403 Forbidden
**Problem:** Accessing resources you don't own  
**Solution:** Use correct parent_id/student_id

### 422 Validation Error
**Problem:** Invalid request body format  
**Solution:** Check request format in [Endpoint Reference](./ENDPOINT_REFERENCE.md)

### 500 Internal Server Error
**Problem:** Server-side issue  
**Solution:** Check server logs: `tail -f server.log`

### Connection Refused
**Problem:** Server not running  
**Solution:** Start server with `./start-dev.sh`

## 🌐 Environment Variables

Required in `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
JWT_SECRET_KEY=your_secret_key
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

## 📝 API Endpoints Summary

### Health & System
- `GET /health` - Health check
- `GET /` - API information

### Authentication (8 endpoints)
- Registration (simple, email, phone, Google)
- Login (parent, child)
- Token management
- Logout

### Onboarding (8 endpoints)
- Preferences management
- Child profile CRUD
- Exam selection
- Status tracking

### Study Center (11 endpoints)
- Topic management
- Learning materials
- Progress tracking
- Learning sessions

### Diagnostic Tests (8 endpoints)
- Test scheduling
- Test lifecycle
- Results management
- Status tracking

### Schedule Management (10 endpoints)
- Schedule generation
- Progress tracking
- Task management
- Schedule adaptation

### Payment (6 endpoints)
- Plans management
- Order creation
- Payment verification
- Subscription management

### AI Features (10 endpoints)
- Vector search
- RAG generation
- Semantic search
- Content generation

**Total: 61+ endpoints**

## 🎯 Next Steps

1. **Start Testing:**
   - Follow [Quick Test Scenarios](./QUICK_TEST_SCENARIOS.md) for immediate testing
   - Use [API Testing Guide](./API_TESTING_GUIDE.md) for comprehensive understanding

2. **Integrate:**
   - Use [Endpoint Reference](./ENDPOINT_REFERENCE.md) for integration
   - Import [Postman Collection](./Mentor_AI_Postman_Collection.json) for API exploration

3. **Automate:**
   - Run `python3 run_endpoint_tests.py` for automated testing
   - Create custom test scripts based on examples

## 📞 Support

For issues or questions:
1. Check the documentation files in this folder
2. Review server logs: `tail -f server.log`
3. Check interactive docs: http://localhost:8000/api/docs
4. Run automated tests: `python3 run_endpoint_tests.py`

## 📄 License

Mentor AI Platform - Internal Documentation

---

**Last Updated:** January 2025  
**API Version:** 1.0.0  
**Documentation Version:** 1.0.0
