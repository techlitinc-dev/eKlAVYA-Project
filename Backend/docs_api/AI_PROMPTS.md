# AI Prompts for API Debugging

## Overview

This collection of AI prompts is designed to help you quickly debug Mentor AI API issues by providing structured prompts for ChatGPT, Claude, or other AI assistants. Each prompt is tailored to specific categories of problems you might encounter.

## How to Use These Prompts

1. **Copy the relevant prompt** for your issue category
2. **Fill in the bracketed placeholders** `[...]` with specific details
3. **Paste into ChatGPT/Claude** along with any relevant logs
4. **Review the AI's suggestions** and implement the recommended fixes

---

## 1. Authentication Issues Prompt

```
I'm debugging a Mentor AI authentication issue and need help. Please analyze the problem and provide solutions.

**System Context:**
- Mentor AI uses JWT-based authentication with access and refresh tokens
- Supports parent and child login with different endpoints
- Firebase/Firestore for user data storage
- Token expiration: 24 hours for access tokens, 30 days for refresh tokens

**Issue Details:**
- Endpoint: [e.g., POST /login/email, POST /token/refresh]
- Request payload: [Copy the exact JSON request]
- Error response: [Copy the exact error message]
- Expected behavior: [Describe what should happen]
- User type: [Parent/Child]
- Authentication method: [Email/Phone/Google OAuth]

**Environment:**
- Testing mode: [Yes/No]
- JWT_SECRET configured: [Yes/No]
- Firebase connected: [Yes/No]
- Recent changes: [Any recent deployments or code changes]

**Questions:**
1. What's causing this authentication error based on the response?
2. How can I fix the JWT token validation/refresh logic?
3. Are there any issues with the Firebase user authentication flow?
4. What additional logs should I check to diagnose this issue?
5. Are there any security considerations I should be aware of?

Please provide specific steps to resolve this authentication issue, including code examples if applicable.
```

---

## 2. Database Issues Prompt

```
I'm experiencing a Mentor AI database issue and need help troubleshooting. Please assist with the diagnosis.

**System Context:**
- Mentor AI uses Google Cloud Firestore as primary database
- Collections: parents, children, subscriptions, tests, analytics, etc.
- Real-time listeners and offline sync
- Data validation at both model and database level
- Index-based queries for performance optimization

**Issue Details:**
- Endpoint: [e.g., GET /me, POST /api/onboarding/child]
- Database operation: [Read/Write/Update/Delete]
- Error response: [Copy the exact error message]
- Query details: [If applicable, copy the query being executed]
- Expected behavior: [Describe what should happen]
- Performance concerns: [Slow queries, timeouts, etc.]

**Environment:**
- Firebase project ID: [Your project ID]
- Database region: [e.g., us-central1]
- Emulator mode: [Yes/No]
- Recent schema changes: [Any recent model updates]
- Index status: [Up to date/Missing indexes]

**Questions:**
1. What's causing this database error based on Firestore error codes?
2. How can I optimize this Firestore query for better performance?
3. Are there missing or incorrect Firestore indexes?
4. What's the best way to handle concurrent database operations?
5. How should I structure my data model to avoid common pitfalls?
6. Are there any Firestore quota or pricing concerns?

Please provide specific debugging steps and code examples for resolving this database issue.
```

---

## 3. Payment Issues Prompt

```
I'm debugging a Mentor AI payment processing issue and need expert help. Please analyze the problem.

**System Context:**
- Mentor AI uses Razorpay for payment processing
- Subscription management with monthly/yearly plans
- Payment flow: Create Order → Razorpay Checkout → Webhook Verification → Activation
- Currency: INR (stored in paise, 100 paise = 1 rupee)
- Webhook-based payment verification with signature validation

**Issue Details:**
- Endpoint: [e.g., POST /api/payment/create-order, POST /api/payment/verify]
- Payment gateway: [Razorpay]
- Error response: [Copy the exact error message]
- Order ID: [If applicable]
- Payment ID: [If applicable]
- Expected behavior: [Describe what should happen]
- Webhook status: [Receiving/Not receiving webhooks]

**Environment:**
- Razorpay mode: [Test/Live]
- Key ID: [Your Razorpay key ID]
- Key secret: [Configured/Not configured]
- Webhook URL: [Your webhook endpoint]
- SSL certificate: [Valid/Invalid/Expired]

**Questions:**
1. What's causing this payment failure based on Razorpay error codes?
2. How do I properly verify Razorpay webhook signatures?
3. Are there issues with the order creation or payment flow?
4. How should I handle payment timeouts and retries?
5. What's the best way to test payment flows in development?
6. Are there any compliance or security issues with my payment setup?

Please provide step-by-step debugging instructions and code examples for payment integration issues.
```

---

## 4. AI Features Issues Prompt

```
I'm having trouble with Mentor AI's AI-powered features and need help debugging. Please assist me.

**System Context:**
- Mentor AI uses Google Gemini API for AI features
- Features: AI tutor chat, question generation, recommendations, exam readiness
- RAG (Retrieval-Augmented Generation) for contextual responses
- Vector embeddings for semantic search
- Rate limiting and quota management for AI services

**Issue Details:**
- Feature: [e.g., AI tutor, RAG question generation, recommendations]
- Endpoint: [e.g., POST /api/ai/tutor/ask, POST /api/rag/generate-questions]
- Error response: [Copy the exact error message]
- Request details: [Copy the relevant request payload]
- Expected behavior: [Describe what should happen]
- Performance: [Slow responses, timeouts, etc.]

**Environment:**
- Gemini API key: [Valid/Invalid/Expired]
- API quota status: [Current usage/limits]
- Model version: [e.g., gemini-pro, gemini-1.5-flash]
- Rate limits: [Current limits and throttling]
- Cache status: [Enabled/Disabled, hit rates]

**Questions:**
1. What's causing this AI feature to fail based on the Gemini API response?
2. How can I optimize the RAG pipeline for better performance?
3. Are there issues with the context retrieval or embedding generation?
4. What's the best way to handle Gemini API rate limits and quotas?
5. How should I structure prompts for better AI response quality?
6. Are there any caching strategies I should implement for AI features?

Please provide specific debugging steps for AI service issues, including prompt engineering tips.
```

---

## 5. API Performance Issues Prompt

```
I'm experiencing performance issues with the Mentor AI API and need help optimizing it. Please analyze and provide solutions.

**System Context:**
- Mentor AI is built on FastAPI with Python
- Uses Firestore for database operations
- Implements JWT authentication and rate limiting
- Caching layer for frequently accessed data
- Background tasks for AI processing and notifications

**Issue Details:**
- Endpoint: [The specific slow endpoint]
- Performance metrics: [Response times, memory usage, CPU usage]
- Concurrency: [Number of simultaneous users]
- Database performance: [Query times, connection pool]
- Cache effectiveness: [Hit/miss ratios]

**Environment:**
- Server specs: [CPU, RAM, disk space]
- Database location: [Firestore region]
- Network: [Bandwidth, latency to external services]
- Load balancer: [Single instance/multiple instances]
- Monitoring: [Enabled/Disabled tools]

**Questions:**
1. What are the primary bottlenecks in this API endpoint?
2. How can I optimize Firestore queries for better performance?
3. What caching strategies should I implement for this use case?
4. Are there any memory leaks or resource issues in the application?
5. How should I handle high concurrent load scenarios?
6. What monitoring and alerting should I set up for performance issues?

Please provide specific optimization strategies and code examples for improving API performance.
```

---

## 6. Validation Issues Prompt

```
I'm encountering validation errors in Mentor AI API requests and need help fixing them. Please assist with the debugging.

**System Context:**
- Mentor AI uses Pydantic models for request/response validation
- Custom validators for business logic
- Field-level and cross-field validation
- Error messages with detailed validation feedback
- Type hints and model serialization

**Issue Details:**
- Endpoint: [The endpoint returning validation errors]
- Model: [e.g., CreateOrderRequest, SubscriptionDetails]
- Validation errors: [Copy the specific validation error messages]
- Request payload: [Copy the failing request data]
- Expected validation rules: [Describe what should be validated]

**Environment:**
- Pydantic version: [Your version]
- Custom validators: [Any custom validation logic]
- Model updates: [Recent changes to request models]
- Testing framework: [Pytest/Manual testing]

**Questions:**
1. What's causing this validation error based on the model definition?
2. How can I fix the request payload to pass validation?
3. Are there any issues with custom validators or business logic?
4. What's the best way to handle partial validation failures?
5. How should I structure error responses for better developer experience?
6. Are there any issues with data type conversion or serialization?

Please provide specific fixes for validation errors, including corrected request examples.
```

---

## 7. External Service Integration Issues Prompt

```
I'm having trouble with external service integrations in Mentor AI and need help debugging the connections.

**System Context:**
- Mentor AI integrates with: Firebase, Gemini API, Razorpay, Email services, SMS services
- Uses webhooks for real-time notifications
- Implements retry logic and circuit breakers
- External authentication providers (Google OAuth)

**Issue Details:**
- Service: [Firebase/Gemini/Razorpay/Email/SMS]
- Integration type: [API/Webhook/SDK]
- Error details: [Copy error messages and logs]
- Configuration: [API keys, webhooks, credentials]
- Network connectivity: [Firewall/DNS/proxy issues]

**Environment:**
- API keys: [Valid/Expired/Incorrect permissions]
- Network access: [Direct internet/Proxy/VPN]
- Service status: [Check external service status pages]
- Configuration files: [Environment variables/settings]
- Recent changes: [Any updates to external services]

**Questions:**
1. What's causing the external service integration failure?
2. How can I verify the service configuration and credentials?
3. Are there any network connectivity or firewall issues?
4. What's the best way to handle external service outages?
5. How should I implement proper error handling for external API calls?
6. Are there any rate limiting or quota issues with the external service?

Please provide specific troubleshooting steps for external service integration issues.
```

---

## 8. Deployment Issues Prompt

```
I'm having deployment issues with Mentor AI and need help resolving them. Please assist with the deployment debugging.

**System Context:**
- Mentor AI deployment on [Docker/Kubernetes/VM/Serverless]
- Uses environment variables for configuration
- Implements health checks and monitoring
- Database migrations and schema updates
- SSL/TLS termination for HTTPS

**Issue Details:**
- Deployment type: [Your deployment method]
- Environment: [Development/Staging/Production]
- Error symptoms: [Startup failures, crashes, 503 errors]
- Configuration: [Environment variables, secrets, networking]
- Recent changes: [Code deployments, configuration updates]
- Logs: [Error messages, stack traces]

**Environment:**
- Platform: [AWS/GCP/Azure/On-premises]
- Container runtime: [Docker version, Python version]
- Resource limits: [CPU, memory, disk space]
- Networking: [Load balancer, DNS, SSL certificates]
- Monitoring: [Logs, metrics, alerts]

**Questions:**
1. What's causing the deployment to fail or perform poorly?
2. How can I verify the environment configuration is correct?
3. Are there any resource constraints or limitations I should be aware of?
4. What's the best way to handle database migrations in production?
5. How should I implement proper logging and monitoring for deployment issues?
6. Are there any networking or connectivity issues between services?

Please provide specific deployment troubleshooting steps and configuration best practices.
```

---

## 9. Testing Issues Prompt

```
I'm having issues testing Mentor AI APIs and need help creating effective test scenarios. Please assist with test strategy.

**System Context:**
- Mentor AI has comprehensive API endpoints for authentication, onboarding, testing, learning, AI features, payments
- Uses JWT authentication with different user roles (parent/child)
- Implements rate limiting and caching
- Has mock services for testing isolation
- Supports both manual and automated testing

**Issue Details:**
- Test type: [Unit/Integration/E2E/Performance]
- Endpoint(s): [Specific APIs being tested]
- Test framework: [Pytest/Manual/Postman/Custom]
- Environment: [Local/Staging/Production]
- Test data: [Setup/Teardown/Isolation issues]

**Environment:**
- Test database: [Separate/Shared with production]
- Test users: [Number and types of test accounts]
- Test data generation: [Dynamic/Static/Hardcoded]
- Mock services: [Enabled/Disabled, which services mocked]
- CI/CD pipeline: [GitHub Actions/GitLab CI/Jenkins]

**Questions:**
1. What's the best way to test authentication flows end-to-end?
2. How can I create realistic test data without affecting production?
3. What's the best strategy for testing payment flows safely?
4. How should I test rate limiting and caching behavior?
5. What's the best way to test AI features with deterministic outputs?
6. How can I set up comprehensive integration testing for multiple services?

Please provide specific testing strategies, test data setup, and debugging techniques for API testing.
```

---

## 10. General Error Debugging Prompt

```
I'm encountering an error with Mentor AI that doesn't fit into specific categories. Please help me debug this general issue.

**System Context:**
- Mentor AI is a FastAPI-based educational platform
- Uses JWT authentication and Firestore database
- Integrates multiple external services (Gemini, Razorpay, etc.)
- Implements comprehensive error handling and logging
- Runs on [Your deployment environment]

**Issue Details:**
- Error message: [Copy the complete error message]
- HTTP status code: [e.g., 400, 401, 403, 404, 500, 503]
- Endpoint: [The API endpoint being called]
- Request method: [GET, POST, PUT, DELETE]
- Request headers: [Relevant headers if applicable]
- Request body: [The request payload if applicable]
- Timestamp: [When the error occurred]
- User context: [Any relevant user information]

**Environment:**
- Your role: [Developer/Tester/Admin]
- Access level: [The permissions you have]
- Environment: [Development/Staging/Production]
- Recent changes: [Any recent code deployments]
- Browser/client: [If applicable]

**Questions:**
1. What's the most likely cause of this error based on the message and context?
2. How can I reproduce this error consistently?
3. What logs or additional information should I gather to diagnose this?
4. Are there any recent changes that might have introduced this issue?
5. What's the impact of this error on the user experience?
6. What temporary workarounds or mitigation strategies can I implement?

Please provide general debugging guidance and systematic troubleshooting steps for this Mentor AI issue.
```

## Tips for Effective AI Debugging

### 1. Provide Context
- Always include system context and environment details
- Mention recent changes that might be relevant
- Describe the expected vs. actual behavior

### 2. Be Specific
- Include exact error messages and status codes
- Provide complete request payloads (redact sensitive data)
- Share relevant logs and stack traces

### 3. Ask Focused Questions
- Request specific debugging steps or solutions
- Ask for code examples when relevant
- Inquire about best practices or alternatives

### 4. Follow Up on Solutions
- Implement suggested fixes and test them
- Share results with the AI for future reference
- Document the solution for team knowledge

These prompts should help you get targeted, effective assistance for debugging Mentor AI API issues across all categories.