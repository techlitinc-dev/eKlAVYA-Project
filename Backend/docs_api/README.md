# Mentor AI API Testing Documentation

Welcome to the comprehensive API testing documentation for Mentor AI. This documentation provides detailed testing instructions for all API endpoints, organized by functional areas for easy navigation.

## Documentation Structure

The API documentation is organized into the following sections:

### [01 Authentication](./01_authentication/)
- [auth_router.md](./01_authentication/auth_router.md) - Parent registration endpoints
- [login_router.md](./01_authentication/login_router.md) - Login, token management, and user sessions
- [simple_register_router.md](./01_authentication/simple_register_router.md) - Simple registration flow
- [verification_router.md](./01_authentication/verification_router.md) - Email and phone verification

### [02 Onboarding](./02_onboarding/)
- [child_router.md](./02_onboarding/child_router.md) - Child profile management
- [preferences_router.md](./02_onboarding/preferences_router.md) - User preferences
- [exam_router.md](./02_onboarding/exam_router.md) - Exam selection and scheduling

### [03 Dashboards](./03_dashboards/)
- [parent_dashboard_router.md](./03_dashboards/parent_dashboard_router.md) - Parent dashboard and reports
- [student_dashboard_router.md](./03_dashboards/student_dashboard_router.md) - Student dashboard and features

### [04 Testing](./04_testing/)
- [diagnostic_test_router.md](./04_testing/diagnostic_test_router.md) - Diagnostic test management
- [test_management_router.md](./04_testing/test_management_router.md) - Test CRUD operations
- [schedule_router.md](./04_testing/schedule_router.md) - Study schedule management
- [question_router.md](./04_testing/question_router.md) - Question generation and management

### [05 Learning](./05_learning/)
- [study_center_router.md](./05_learning/study_center_router.md) - Learning materials and progress
- [syllabus_coverage_router.md](./05_learning/syllabus_coverage_router.md) - Syllabus tracking
- [analytics_router.md](./05_learning/analytics_router.md) - Performance analytics
- [gamification_router.md](./05_learning/gamification_router.md) - Badges and achievements

### [06 AI Features](./06_ai_features/)
- [rag_router.md](./06_ai_features/rag_router.md) - RAG-based content generation
- [embedding_router.md](./06_ai_features/embedding_router.md) - Text embedding generation
- [vector_search_router.md](./06_ai_features/vector_search_router.md) - Semantic search
- [ai_features_router.md](./06_ai_features/ai_features_router.md) - General AI features
- [hermes_router.md](./06_ai_features/hermes_router.md) - Hermes 1-to-1 AI mentor (Socratic tutor, micro-topic state machine, daily summaries)

### [07 Payments](./07_payments/)
- [payment_router.md](./07_payments/payment_router.md) - Payment processing (Razorpay)

## Additional Resources

- [TESTING_WORKFLOW.md](./TESTING_WORKFLOW.md) - Complete user journey testing guide
- [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) - Common errors and solutions
- [AI_PROMPTS.md](./AI_PROMPTS.md) - AI troubleshooting prompts for debugging
- [POSTMAN_COLLECTION.md](./POSTMAN_COLLECTION.md) - Postman collection usage guide

## Quick Start

### Prerequisites

1. **API Base URL**: Set your API base URL (e.g., `http://localhost:8000`)
2. **Authentication**: Most endpoints require JWT tokens in the Authorization header
3. **Tools**: Use curl, Postman, or any HTTP client for testing

### Environment Setup

1. Clone the repository and set up your environment variables
2. Ensure Firebase/Firestore is properly configured
3. Verify all API keys (Gemini, Razorpay) are set in your `.env` file

### Testing Tools

#### Using curl
```bash
# Example with authentication
curl -X GET "http://localhost:8000/api/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### Using Postman
1. Import the Postman collection from `docs/Mentor_AI_Postman_Collection.json`
2. Set up environment variables for base_url, auth_token, etc.
3. Use the pre-configured requests for each endpoint

## Common Troubleshooting Tips

### Authentication Issues
- Ensure JWT tokens are properly formatted: `Bearer <token>`
- Check token expiration and refresh when needed
- Verify user exists in Firestore

### 404 Not Found Errors
- Confirm the endpoint path is correct
- Check if required query parameters are provided
- Verify resource exists in the database

### 500 Internal Server Errors
- Check server logs for detailed error messages
- Verify all environment variables are set
- Ensure external services (Firebase, Gemini) are accessible

### Validation Errors (400)
- Review request payload structure
- Check required fields and data types
- Validate against the models in the documentation

## Using AI Troubleshooting Prompts

Each endpoint documentation includes an "AI Troubleshooting Prompt" section. These prompts can be copied and pasted into ChatGPT or Claude for debugging specific issues. To use them:

1. Copy the prompt from the relevant endpoint documentation
2. Fill in the specific error details, request/response examples
3. Paste into your AI assistant with relevant code context
4. Follow the debugging suggestions provided

For general issues, use the prompts in [AI_PROMPTS.md](./AI_PROMPTS.md).

## Testing Best Practices

1. **Follow the Testing Workflow**: Use [TESTING_WORKFLOW.md](./TESTING_WORKFLOW.md) for systematic testing
2. **Test in Order**: Start with authentication, then onboarding, then other features
3. **Use Test Data**: Create consistent test data for reproducible results
4. **Check Dependencies**: Some endpoints require data from other endpoints
5. **Verify Responses**: Always check both success and error scenarios
6. **Monitor Logs**: Use server logs to debug issues not visible in responses

## Getting Help

If you encounter issues not covered in this documentation:

1. Check the [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) for common solutions
2. Use the AI prompts for debugging specific errors
3. Review the existing test files in the `tests/` directory
4. Check the main project documentation in `docs/`

## Contributing

When adding new endpoints or updating existing ones:

1. Update the relevant router documentation
2. Include testing steps for all new endpoints
3. Add error scenarios and troubleshooting information
4. Update the TESTING_WORKFLOW.md if the user flow changes
5. Add new AI troubleshooting prompts as needed