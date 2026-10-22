# Mentor AI API Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide covers common issues across all Mentor AI API endpoints, with systematic debugging approaches and solutions. It's organized by error type, service dependencies, and feature categories for quick reference.

## Quick Reference

### Common HTTP Status Codes

| Status Code | Meaning | Common Causes | Quick Fix |
|-------------|---------|--------------|-----------|
| 400 | Bad Request | Invalid JSON, missing fields, validation errors | Check request format and required fields |
| 401 | Unauthorized | Invalid/expired JWT token | Refresh token or re-authenticate |
| 403 | Forbidden | Accessing another user's data | Verify user ownership |
| 404 | Not Found | Resource doesn't exist | Check resource ID and permissions |
| 429 | Too Many Requests | Rate limit exceeded | Implement backoff strategy |
| 500 | Internal Server Error | Service failure | Check logs and service status |
| 503 | Service Unavailable | External service down | Check service dependencies |

## Authentication Issues

### JWT Token Problems

#### Problem: Token Validation Fails

**Symptoms:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Debugging Steps:**
1. **Check Token Format:**
   ```bash
   # Verify token has proper Bearer prefix
   echo "Bearer $TOKEN" | cut -d' ' ' -f2
   ```

2. **Verify Token Expiration:**
   ```bash
   # Decode JWT to check expiration
   echo $TOKEN | cut -d'.' -f2 | base64 -d | jq -r '.exp'
   ```

3. **Check Environment Variables:**
   ```bash
   # Verify JWT_SECRET is set
   echo $JWT_SECRET
   ```

4. **Validate Token Structure:**
   ```bash
   # Check if token has required claims
   echo $TOKEN | jq -r '.parent_id, .child_id, .exp'
   ```

**Common Solutions:**
- Token missing Bearer prefix: Add `Bearer ` to Authorization header
- Token expired: Implement token refresh flow
- Invalid token: Re-authenticate user
- Secret mismatch: Check JWT_SECRET environment variable

#### Problem: Token Refresh Fails

**Symptoms:**
```json
{
  "detail": "Failed to refresh token"
}
```

**Debugging Steps:**
1. **Check Refresh Token Validity:**
   ```bash
   # Verify refresh token hasn't expired
   echo $REFRESH_TOKEN | cut -d'.' -f2 | base64 -d | jq -r '.exp'
   ```

2. **Check Token Storage:**
   ```bash
   # Verify refresh token exists in database
   # Check Firestore for refresh token document
   ```

3. **Validate Request Format:**
   ```bash
   # Check if refresh_token is in request body
   curl -X POST "$API_BASE_URL/token/refresh" \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"test_token"}' -v
   ```

**Common Solutions:**
- Refresh token expired: Require re-login
- Refresh token not found: Generate new refresh token
- Invalid grant type: Use `refresh_token` grant type
- Database error: Check Firestore connectivity

### User Registration Issues

#### Problem: Email Registration Fails

**Symptoms:**
```json
{
  "detail": "Email already exists"
}
```

**Debugging Steps:**
1. **Check Email Format:**
   ```bash
   # Test email validation
   curl -X POST "$API_BASE_URL/register/parent/email" \
     -H "Content-Type: application/json" \
     -d '{"email":"invalid-email","password":"Test@123"}' -v
   ```

2. **Check Firebase Connection:**
   ```bash
   # Test Firebase connectivity
   firebase projects:list
   ```

3. **Verify Email Service:**
   ```bash
   # Check if email service is configured
   echo $EMAIL_SERVICE
   ```

**Common Solutions:**
- Email exists: Use different email or login
- Invalid email format: Validate email before sending
- Firebase error: Check service account credentials
- Password validation: Ensure password meets requirements

#### Problem: Phone Registration Fails

**Symptoms:**
```json
{
  "detail": "Mobile number already registered"
}
```

**Debugging Steps:**
1. **Check Phone Format:**
   ```bash
   # Test with different phone formats
   curl -X POST "$API_BASE_URL/register/parent/phone" \
     -H "Content-Type: application/json" \
     -d '{"mobile":"+919876543210","password":"Test@123"}' -v
   ```

2. **Check OTP Service:**
   ```bash
   # Verify OTP service is working
   echo $OTP_SERVICE_PROVIDER
   ```

3. **Verify SMS Configuration:**
   ```bash
   # Check SMS service credentials
   echo $SMS_API_KEY
   ```

**Common Solutions:**
- Phone exists: Use different number or login
- Invalid format: Include country code and proper formatting
- OTP not sent: Check SMS service configuration
- SMS quota exceeded: Use email verification alternative

### Verification Issues

#### Problem: Email Verification Not Working

**Symptoms:**
- Verification email not received
- OTP code not accepted
- Verification link expired

**Debugging Steps:**
1. **Check Email Logs:**
   ```bash
   # Check email service logs
   # Look for delivery status
   ```

2. **Verify OTP Generation:**
   ```bash
   # Check if OTP was generated
   # Look in verification service logs
   ```

3. **Test OTP Validation:**
   ```bash
   # Test with known OTP
   curl -X POST "$API_BASE_URL/verify/email/confirm" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","verification_code":"123456"}' -v
   ```

**Common Solutions:**
- Email not received: Check spam folder, verify email address
- Invalid OTP: Verify code format and expiration time
- Expired code: Generate new verification code
- Rate limit: Implement cooldown period

#### Problem: Phone Verification Not Working

**Symptoms:**
- SMS not delivered
- Invalid OTP code
- Verification timeout

**Debugging Steps:**
1. **Check SMS Provider Status:**
   ```bash
   # Check SMS service dashboard
   # Verify API quotas and status
   ```

2. **Test SMS Delivery:**
   ```bash
   # Send test SMS to verify delivery
   # Check delivery reports
   ```

3. **Verify Phone Format:**
   ```bash
   # Test with different phone formats
   # Check country code handling
   ```

**Common Solutions:**
- SMS not delivered: Check phone number, try email verification
- Invalid OTP: Verify code digits and format
- Network issues: Check SMS provider status
- Rate limit: Wait before retrying

## Data Validation Issues

### Problem: Child Profile Validation Fails

**Symptoms:**
```json
{
  "detail": "Invalid age or grade"
}
```

**Debugging Steps:**
1. **Check Request Format:**
   ```bash
   # Verify JSON structure
   curl -X POST "$API_BASE_URL/api/onboarding/child" \
     -H "Content-Type: application/json" \
     -d '{"parent_id":"test","name":"Student","age":16,"grade":"11"}' -v
   ```

2. **Check Validation Rules:**
   ```bash
   # Test boundary values
   curl -X POST "$API_BASE_URL/api/onboarding/child" \
     -H "Content-Type: application/json" \
     -d '{"parent_id":"test","name":"Student","age":0,"grade":"11"}' -v
   ```

3. **Check Database Constraints:**
   ```bash
   # Verify database schema constraints
   # Check Firestore rules and indexes
   ```

**Common Solutions:**
- Invalid age: Ensure age is between 5-25
- Invalid grade: Use valid grade levels (1-12)
- Missing fields: Include all required fields
- Type errors: Ensure correct data types

### Problem: Exam Selection Validation Fails

**Symptoms:**
```json
{
  "detail": "Subject preferences must sum to 100"
}
```

**Debugging Steps:**
1. **Check Subject Preferences:**
   ```bash
   # Verify subject percentages
   curl -X POST "$API_BASE_URL/api/onboarding/exam/select" \
     -H "Content-Type: application/json" \
     -d '{"parent_id":"test","exam_type":"JEE_MAIN","subject_preferences":{"Physics":40,"Chemistry":35,"Mathematics":25}}' -v
   ```

2. **Check Exam Date:**
   ```bash
   # Test with future dates only
   curl -X POST "$API_BASE_URL/api/onboarding/exam/select" \
     -H "Content-Type: application/json" \
     -d '{"parent_id":"test","exam_type":"JEE_MAIN","exam_date":"2024-06-01"}' -v
   ```

3. **Validate Exam Type:**
   ```bash
   # Test with invalid exam types
   curl -X POST "$API_BASE_URL/api/onboarding/exam/select" \
     -H "Content-Type: application/json" \
     -d '{"parent_id":"test","exam_type":"INVALID"}' -v
   ```

**Common Solutions:**
- Invalid percentages: Ensure subjects sum to exactly 100
- Past exam date: Use future dates only
- Invalid exam type: Use JEE_MAIN, JEE_ADVANCED, or NEET
- Missing preferences: Include all required subjects

## Service Dependency Issues

### Firebase/Firestore Problems

#### Problem: Database Connection Fails

**Symptoms:**
```json
{
  "detail": "Internal Server Error"
}
```

**Debugging Steps:**
1. **Check Firebase Configuration:**
   ```bash
   # Verify Firebase credentials
   echo $FIREBASE_PROJECT_ID
   echo $FIREBASE_PRIVATE_KEY
   ```

2. **Test Database Access:**
   ```bash
   # Test basic Firestore operation
   firebase projects:getProject $FIREBASE_PROJECT_ID
   ```

3. **Check Network Connectivity:**
   ```bash
   # Test Firebase connectivity
   ping firestore.googleapis.com
   ```

4. **Verify Service Account:**
   ```bash
   # Check service account permissions
   gcloud auth list
   ```

**Common Solutions:**
- Invalid credentials: Check Firebase project settings
- Permission denied: Update service account permissions
- Network issues: Check firewall and DNS
- Quota exceeded: Monitor usage and upgrade plan
- Index missing: Create required Firestore indexes

### Gemini API Issues

#### Problem: AI Service Unavailable

**Symptoms:**
```json
{
  "detail": "Service Unavailable - Gemini API is down"
}
```

**Debugging Steps:**
1. **Check API Key:**
   ```bash
   # Verify Gemini API key
   echo $GEMINI_API_KEY
   ```

2. **Test API Access:**
   ```bash
   # Test direct Gemini API call
   curl -H "Content-Type: application/json" \
     -H "x-goog-api-key: $GEMINI_API_KEY" \
     -d '{"contents":[{"parts":[{"text":"test"}]}' \
     https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
   ```

3. **Check Quota:**
   ```bash
   # Monitor API usage
   # Check Google Cloud Console for quotas
   ```

4. **Verify Model Access:**
   ```bash
   # Check if gemini-pro model is enabled
   gcloud ai models list
   ```

**Common Solutions:**
- Invalid API key: Regenerate from Google Cloud Console
- Quota exceeded: Monitor usage and implement caching
- Model unavailable: Check model availability and permissions
- Network issues: Check connectivity to Google APIs
- Rate limiting: Implement exponential backoff

### Razorpay Issues

#### Problem: Payment Processing Fails

**Symptoms:**
```json
{
  "detail": "Payment verification failed"
}
```

**Debugging Steps:**
1. **Check Razorpay Configuration:**
   ```bash
   # Verify Razorpay credentials
   echo $RAZORPAY_KEY_ID
   echo $RAZORPAY_KEY_SECRET
   ```

2. **Test Webhook URL:**
   ```bash
   # Test webhook accessibility
   curl -X POST "$WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"event":"payment.authorized"}' -v
   ```

3. **Verify Signature:**
   ```bash
   # Test signature verification
   # Use Razorpay test credentials
   ```

4. **Check Order Status:**
   ```bash
   # Check Razorpay order status
   # Use Razorpay dashboard or API
   ```

**Common Solutions:**
- Invalid credentials: Check Razorpay dashboard settings
- Signature mismatch: Verify webhook secret and calculation
- Webhook not working: Check URL accessibility and SSL
- Order not found: Verify order ID and status
- Payment declined: Check card details and bank response

## Performance Issues

### Problem: Slow API Response Times

**Symptoms:**
- Requests taking >5 seconds
- Timeout errors
- Poor user experience

**Debugging Steps:**
1. **Measure Response Times:**
   ```bash
   # Time API calls
   time curl -X GET "$API_BASE_URL/me" \
     -H "Authorization: Bearer $TOKEN" \
     -w "Time: %{time_total}s\n"
   ```

2. **Check Database Performance:**
   ```bash
   # Monitor Firestore performance
   # Check query execution times
   ```

3. **Analyze Request Size:**
   ```bash
   # Check large request payloads
   # Monitor memory usage
   ```

4. **Test Concurrent Load:**
   ```bash
   # Test with multiple concurrent requests
   # Monitor performance degradation
   ```

**Common Solutions:**
- Database queries: Optimize Firestore queries and indexes
- Large responses: Implement pagination
- Memory issues: Add response caching
- Network latency: Use CDN for static content
- CPU bound: Implement request queuing

### Problem: Memory Leaks

**Symptoms:**
- Memory usage increasing over time
- Server crashes under load
- Performance degradation

**Debugging Steps:**
1. **Monitor Memory Usage:**
   ```bash
   # Monitor process memory
   ps aux --sort=-%mem | head -10
   ```

2. **Check Connection Pooling:**
   ```bash
   # Monitor database connections
   # Check for unclosed connections
   ```

3. **Profile Application:**
   ```bash
   # Use Python profiler
   python -m cProfile -o profile_stats app.py
   ```

4. **Test Resource Cleanup:**
   ```bash
   # Test with resource cleanup
   # Force garbage collection
   ```

**Common Solutions:**
- Unclosed connections: Ensure proper connection cleanup
- Large objects: Implement object pooling
- Caching issues: Clear cache periodically
- Memory leaks: Profile and fix memory leaks

## Security Issues

### Problem: CORS Errors

**Symptoms:**
```javascript
// Browser console error
Access to fetch at 'http://localhost:8000/api/me' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Debugging Steps:**
1. **Check CORS Configuration:**
   ```bash
   # Verify CORS middleware
   # Check allowed origins
   ```

2. **Test Preflight Requests:**
   ```bash
   # Test OPTIONS requests
   curl -X OPTIONS "$API_BASE_URL/me" \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -v
   ```

3. **Verify Headers:**
   ```bash
   # Check response headers
   curl -I "$API_BASE_URL/me" \
     -H "Origin: http://localhost:3000" \
     -v
   ```

**Common Solutions:**
- Missing headers: Add proper CORS headers
- Wrong origins: Update allowed origins list
- Preflight failed: Handle OPTIONS requests
- Credentials not allowed: Add allow-credentials header

### Problem: Rate Limiting Bypass

**Symptoms:**
```json
{
  "detail": "Rate limit exceeded"
}
```

**Debugging Steps:**
1. **Test Rate Limits:**
   ```bash
   # Send rapid requests to trigger limit
   for i in {1..101}; do
     curl -X GET "$API_BASE_URL/me" \
       -H "Authorization: Bearer $TOKEN" \
       -o /dev/null -s -w "%{http_code}\n"
   done
   ```

2. **Check Rate Limit Headers:**
   ```bash
   # Verify rate limit headers
   curl -X GET "$API_BASE_URL/me" \
     -H "Authorization: Bearer $TOKEN" \
     -I -v
   ```

3. **Test Different Users:**
   ```bash
   # Test with different user IDs
   # Verify rate limiting is per-user
   ```

**Common Solutions:**
- Rate limit too low: Increase limits for legitimate use
- Not per-user: Implement per-user rate limiting
- Headers missing: Add proper rate limit headers
- Bypass attempts: Implement IP-based limiting

## Environment-Specific Issues

### Development Environment

#### Problem: Local Testing Fails

**Symptoms:**
- Connection refused errors
- Environment variable issues
- Service unavailable errors

**Debugging Steps:**
1. **Check Server Status:**
   ```bash
   # Verify server is running
   ps aux | grep uvicorn
   ```

2. **Check Environment Variables:**
   ```bash
   # List all environment variables
   env | grep -E "^(API_|FIREBASE_|GEMINI_|RAZORPAY_)"
   ```

3. **Test Database Connection:**
   ```bash
   # Test database connectivity
   # Check if services are accessible
   ```

4. **Verify Port Availability:**
   ```bash
   # Check if port is available
   netstat -tlnp | grep :8000
   ```

**Common Solutions:**
- Server not running: Start the development server
- Wrong port: Update API_BASE_URL or server config
- Missing variables: Set up .env file properly
- Database issues: Check service credentials and connectivity

### Production Environment

#### Problem: Production Deployment Issues

**Symptoms:**
- 503 Service Unavailable errors
- Database connection timeouts
- SSL/TLS certificate errors

**Debugging Steps:**
1. **Check Service Health:**
   ```bash
   # Monitor service health endpoints
   curl -X GET "$API_BASE_URL/api/rag/pipeline/status"
   ```

2. **Verify SSL Configuration:**
   ```bash
   # Check SSL certificate
   openssl s_client -connect $PROD_HOST:443
   ```

3. **Check Load Balancer:**
   ```bash
   # Verify load balancer configuration
   # Check health of all instances
   ```

4. **Monitor Logs:**
   ```bash
   # Check application logs
   # Look for error patterns
   ```

**Common Solutions:**
- SSL errors: Update certificates and configuration
- Database timeouts: Increase connection pool size
- Load issues: Add more instances or optimize code
- Memory errors: Increase server resources

## Debugging Tools and Techniques

### 1. Logging Strategy

**Structured Logging:**
```python
import logging
import json

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add request ID for tracking
logger.info("Request started", extra={
    "request_id": "req_123",
    "user_id": "user_456",
    "endpoint": "/api/me"
})
```

**Error Logging:**
```python
# Log errors with context
try:
    # API operation
except Exception as e:
    logger.error("Operation failed", extra={
        "error": str(e),
        "request_id": request_id,
        "user_id": user_id,
        "traceback": traceback.format_exc()
    })
    raise
```

### 2. Request/Response Debugging

**Request Logging:**
```python
import json

# Log incoming requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request details
    logger.info("Incoming request", extra={
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "body": await request.body() if request.method != "GET" else None
    })
    
    response = await call_next(request)
    
    # Log response details
    logger.info("Request completed", extra={
        "status_code": response.status_code,
        "duration": time.time() - start_time,
        "response_size": len(response.body) if hasattr(response, 'body') else 0
    })
    
    return response
```

### 3. Database Debugging

**Firestore Debugging:**
```python
from google.cloud import firestore
import logging

# Add query debugging
db = firestore.Client()

def debug_query(collection: str, query: dict):
    start_time = time.time()
    
    # Log query details
    logging.info("Firestore query", extra={
        "collection": collection,
        "query": query,
        "operation": "query"
    })
    
    try:
        result = db.collection(collection).where(**query).get()
        duration = time.time() - start_time
        
        logging.info("Query completed", extra={
            "duration": duration,
            "result_count": len(result) if result else 0,
            "success": True
        })
        
        return result
    except Exception as e:
        logging.error("Query failed", extra={
            "error": str(e),
            "duration": time.time() - start_time,
            "success": False
        })
        raise
```

### 4. Performance Monitoring

**Response Time Tracking:**
```python
import time
from functools import wraps

def track_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log performance metrics
            logging.info("Performance", extra={
                "function": func.__name__,
                "duration": duration,
                "success": True
            })
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logging.error("Performance error", extra={
                "function": func.__name__,
                "duration": duration,
                "error": str(e),
                "success": False
            })
            raise
    
    return wrapper
```

## Automated Testing Strategies

### 1. Health Check Automation

**Automated Health Monitoring:**
```bash
#!/bin/bash
# Health check script
API_BASE_URL="http://localhost:8000"

# Check critical endpoints
endpoints=(
    "/api/rag/pipeline/status"
    "/api/payment/plans"
    "/me"
)

for endpoint in "${endpoints[@]}"; do
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL$endpoint")
    
    if [ "$status_code" -eq "200" ]; then
        echo "✅ $endpoint: HEALTHY"
    else
        echo "❌ $endpoint: UNHEALTHY ($status_code)"
    fi
done
```

### 2. Load Testing Automation

**Load Testing Script:**
```bash
#!/bin/bash
# Load testing with concurrent requests
API_BASE_URL="http://localhost:8000"
TOKEN="your_test_token"
CONCURRENT_USERS=10
REQUESTS_PER_USER=5

echo "Starting load test: $CONCURRENT_USERS users x $REQUESTS_PER_USER requests"

# Run concurrent requests
for ((i=1; i<=CONCURRENT_USERS; i++)); do
    for ((j=1; j<=REQUESTS_PER_USER; j++)); do
        curl -X GET "$API_BASE_URL/me" \
            -H "Authorization: Bearer $TOKEN" \
            -o /dev/null -s -w "%{http_code}\n" &
    done
    
    # Wait for all requests to complete
    wait
done

echo "Load test completed"
```

### 3. Integration Testing

**End-to-End Testing:**
```python
import asyncio
import aiohttp
import json

async def test_user_journey():
    """Test complete user journey from registration to usage"""
    API_BASE_URL = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # 1. Register parent
        async with session.post(f"{API_BASE_URL}/register/parent/email") as resp:
            parent_data = {
                "name": "Test Parent",
                "email": f"test_{asyncio.current_task()}@example.com",
                "password": "Test@123"
            }
            await resp.json()
        
        # 2. Login parent
        async with session.post(f"{API_BASE_URL}/login/email") as resp:
            login_data = {
                "email": parent_data["email"],
                "password": parent_data["password"]
            }
            login_response = await resp.json()
            parent_token = login_response["access_token"]
        
        # 3. Create child
        async with session.post(f"{API_BASE_URL}/api/onboarding/child") as resp:
            child_data = {
                "parent_id": login_response["parent_id"],
                "name": "Test Student",
                "age": 16,
                "grade": "11"
            }
            await resp.json()
        
        # 4. Login child
        async with session.post(f"{API_BASE_URL}/login/child") as resp:
            child_login_data = {
                "username": "student123",
                "password": "Test@123"
            }
            child_login_response = await resp.json()
            child_token = child_login_response["access_token"]
        
        # 5. Generate practice questions
        async with session.post(f"{API_BASE_URL/api/testing/test/generate") as resp:
            practice_data = {
                "child_id": child_login_response["child_id"],
                "subject": "Physics",
                "topics": ["Mechanics"],
                "difficulty": "medium",
                "num_questions": 5
            }
            await resp.json()
        
        print("User journey test completed successfully")

# Run the test
asyncio.run(test_user_journey())
```

## Quick Fix Checklist

### Before Debugging
- [ ] Check recent changes that might have caused the issue
- [ ] Verify environment variables are set correctly
- [ ] Check if all required services are running
- [ ] Review recent error logs
- [ ] Test with minimal reproduction case
- [ ] Check if issue affects all users or specific conditions

### During Debugging
- [ ] Isolate the problem to a single endpoint
- [ ] Test with different input values
- [ ] Check both success and failure scenarios
- [ ] Verify data flow through the entire request lifecycle
- [ ] Monitor system resources during testing

### After Debugging
- [ ] Document the root cause and solution
- [ ] Add regression test to prevent recurrence
- [ ] Update monitoring/alerting for early detection
- [ ] Review and improve error messages for clarity

## Emergency Procedures

### Production Outage Response

1. **Immediate Assessment (5 minutes):**
   - Identify affected services
   - Check error rates and patterns
   - Assess user impact
   - Determine if rollback is needed

2. **Communication (10 minutes):**
   - Update status page
   - Notify stakeholders
   - Provide ETA for resolution
   - Share workarounds if available

3. **Resolution (Target: 1 hour):**
   - Implement fix
   - Verify resolution works
   - Monitor for recurrence
   - Document incident and learnings

4. **Post-Incident (24 hours):**
   - Conduct post-mortem
   - Update monitoring/alerting
   - Improve prevention measures
   - Share findings with team

This comprehensive troubleshooting guide should help identify, diagnose, and resolve common issues across the Mentor AI API platform efficiently.

## Router-Specific Troubleshooting

### 01 Authentication Routers

#### auth_router.py Issues

**Problem: Parent Registration Fails**
```json
{
  "detail": "Registration failed"
}
```

**Debugging Steps:**
1. Check request format for required fields (name, email, password)
2. Verify Firebase Auth service is accessible
3. Test with different email formats
4. Check password validation requirements

**Common Solutions:**
- Missing required fields: Include name, email, password in request
- Invalid email format: Use standard email format
- Weak password: Ensure password meets complexity requirements
- Firebase Auth down: Check Firebase service status

#### login_router.py Issues

**Problem: Token Refresh Returns Invalid Token**
```json
{
  "detail": "Invalid refresh token"
}
```

**Debugging Steps:**
1. Verify refresh token format and expiration
2. Check if refresh token exists in Firestore
3. Test with valid refresh token
4. Verify JWT_SECRET environment variable

**Common Solutions:**
- Expired refresh token: Require user to re-login
- Invalid token format: Check token structure
- Database connection: Verify Firestore connectivity
- Secret mismatch: Check JWT_SECRET configuration

#### verification_router.py Issues

**Problem: OTP Verification Fails**
```json
{
  "detail": "Invalid or expired verification code"
}
```

**Debugging Steps:**
1. Check if OTP was generated and stored
2. Verify OTP expiration time (typically 10 minutes)
3. Test with correct OTP format (6 digits)
4. Check email/SMS delivery status

**Common Solutions:**
- Expired OTP: Generate new verification code
- Invalid format: Use 6-digit numeric code
- Not delivered: Check email/SMS service configuration
- Rate limit: Implement cooldown between requests

### 02 Onboarding Routers

#### child_router.py Issues

**Problem: Child Profile Creation Fails**
```json
{
  "detail": "Parent already has a child profile"
}
```

**Debugging Steps:**
1. Check if parent already has child in Firestore
2. Verify parent_id in request matches authenticated parent
3. Test with different parent accounts
4. Check one-child-per-parent restriction logic

**Common Solutions:**
- Child exists: Use existing child profile or delete first
- Ownership error: Verify parent_id matches authenticated user
- Invalid data: Check age (5-25) and grade (1-12) validation
- Permission denied: Ensure parent is authenticated

#### preferences_router.py Issues

**Problem: Preferences Update Fails**
```json
{
  "detail": "Preferences not found"
}
```

**Debugging Steps:**
1. Check if preferences exist for parent
2. Verify parent_id in request
3. Test creating preferences before updating
4. Check Firestore document structure

**Common Solutions:**
- Not found: Create preferences before updating
- Invalid parent_id: Use authenticated parent ID
- Missing fields: Include all required preference fields
- Validation error: Check preference value constraints

#### exam_router.py Issues

**Problem: Exam Selection Validation Fails**
```json
{
  "detail": "Subject preferences must sum to 100"
}
```

**Debugging Steps:**
1. Calculate total percentage of subject preferences
2. Verify all required subjects are included
3. Test with different percentage combinations
4. Check exam type validation

**Common Solutions:**
- Invalid total: Ensure subjects sum to exactly 100%
- Missing subjects: Include all required subjects for exam type
- Invalid exam type: Use JEE_MAIN, JEE_ADVANCED, or NEET
- Past date: Use future exam dates only

### 03 Dashboard Routers

#### parent_dashboard_router.py Issues

**Problem: Dashboard Data Not Loading**
```json
{
  "detail": "Child not found"
}
```

**Debugging Steps:**
1. Verify child_id exists and belongs to parent
2. Check child-parent relationship in Firestore
3. Test with valid child_id
4. Verify parent authentication

**Common Solutions:**
- Child not found: Use correct child_id
- Ownership error: Ensure child belongs to authenticated parent
- Permission denied: Verify parent authentication
- Data missing: Check if child has required data

#### student_dashboard_router.py Issues

**Problem: Practice Generation Fails**
```json
{
  "detail": "Failed to generate practice questions"
}
```

**Debugging Steps:**
1. Check Gemini API service status
2. Verify request parameters (subject, topics, difficulty)
3. Test with different topic combinations
4. Check student profile data

**Common Solutions:**
- Gemini API down: Check service status and API key
- Invalid topics: Use valid topic names from syllabus
- No data available: Check if student has progress data
- Rate limit: Implement backoff strategy

### 04 Testing Routers

#### diagnostic_test_router.py Issues

**Problem: Test Creation Fails**
```json
{
  "detail": "Failed to create diagnostic test"
}
```

**Debugging Steps:**
1. Check if exam selection is completed
2. Verify diagnostic test template exists
3. Test with different exam types
4. Check question generation service

**Common Solutions:**
- Exam not selected: Complete exam selection first
- Template missing: Create diagnostic test template
- Generation failed: Check RAG service and Gemini API
- Invalid parameters: Verify request structure

#### test_management_router.py Issues

**Problem: Test Submission Fails**
```json
{
  "detail": "Invalid test submission"
}
```

**Debugging Steps:**
1. Verify test is in correct state (in_progress)
2. Check answer format and question IDs
3. Test with complete answer set
4. Verify student ownership

**Common Solutions:**
- Wrong state: Ensure test is in_progress
- Invalid answers: Check answer format and question IDs
- Missing answers: Include answers for all questions
- Permission denied: Verify student authentication

#### schedule_router.py Issues

**Problem: Schedule Generation Fails**
```json
{
  "detail": "Failed to generate study schedule"
}
```

**Debugging Steps:**
1. Check exam date and preferences
2. Verify AI service availability
3. Test with different constraint combinations
4. Check student performance data

**Common Solutions:**
- Invalid date: Use future exam dates
- Missing data: Ensure student has diagnostic test results
- AI service down: Check Gemini API status
- Constraints conflict: Adjust study preferences

#### question_router.py Issues

**Problem: Question Generation Fails**
```json
{
  "detail": "Failed to generate questions"
}
```

**Debugging Steps:**
1. Check RAG pipeline status
2. Verify topic and difficulty parameters
3. Test with different subjects
4. Check embedding service

**Common Solutions:**
- RAG service down: Check vector database and Gemini API
- Invalid topic: Use valid topic names
- No content: Check if syllabus content exists
- Rate limit: Implement backoff strategy

### 05 Learning Routers

#### study_center_router.py Issues

**Problem: Learning Content Not Available**
```json
{
  "detail": "No learning materials found"
}
```

**Debugging Steps:**
1. Check if topic has associated content
2. Verify content generation service
3. Test with different topics
4. Check student progress

**Common Solutions:**
- No content: Generate content for topic
- Service down: Check AI content generation
- Invalid topic: Use valid topic from syllabus
- Access denied: Verify student authentication

#### syllabus_coverage_router.py Issues

**Problem: Coverage Calculation Incorrect**
```json
{
  "detail": "Failed to calculate syllabus coverage"
}
```

**Debugging Steps:**
1. Check student progress data
2. Verify syllabus structure
3. Test with different subjects
4. Check calculation logic

**Common Solutions:**
- Missing data: Ensure student has progress data
- Invalid syllabus: Check syllabus JSON structure
- Calculation error: Verify coverage algorithm
- Database error: Check Firestore connectivity

#### analytics_router.py Issues

**Problem: Analytics Generation Fails**
```json
{
  "detail": "Failed to generate analytics"
}
```

**Debugging Steps:**
1. Check if student has sufficient data
2. Verify analytics service
3. Test with different time ranges
4. Check AI insights generation

**Common Solutions:**
- Insufficient data: Ensure student has practice/test data
- Service down: Check analytics service status
- Invalid range: Use valid date ranges
- AI error: Check Gemini API for insights

#### gamification_router.py Issues

**Problem: Achievement Not Awarded**
```json
{
  "detail": "Achievement criteria not met"
}
```

**Debugging Steps:**
1. Check achievement criteria
2. Verify student progress
3. Test with different achievement types
4. Check award logic

**Common Solutions:**
- Criteria not met: Verify student meets requirements
- Already awarded: Check if achievement already granted
- Invalid achievement: Use valid achievement IDs
- Logic error: Check achievement calculation

### 06 AI Features Routers

#### rag_router.py Issues

**Problem: RAG Pipeline Fails**
```json
{
  "detail": "RAG pipeline error"
}
```

**Debugging Steps:**
1. Check vector database connection
2. Verify embedding generation
3. Test with different queries
4. Check Gemini API integration

**Common Solutions:**
- Vector DB down: Check vector search service
- Embedding failed: Check embedding generation service
- API error: Verify Gemini API key and quota
- No results: Check if content is indexed

#### embedding_router.py Issues

**Problem: Embedding Generation Fails**
```json
{
  "detail": "Failed to generate embeddings"
}
```

**Debugging Steps:**
1. Check embedding service status
2. Verify text input format
3. Test with different text lengths
4. Check API quotas

**Common Solutions:**
- Service down: Check embedding service
- Invalid input: Verify text format and length
- Quota exceeded: Monitor API usage
- API error: Check service configuration

#### vector_search_router.py Issues

**Problem: Vector Search Returns No Results**
```json
{
  "detail": "No similar content found"
}
```

**Debugging Steps:**
1. Check if embeddings exist for content
2. Verify search query format
3. Test with different similarity thresholds
4. Check vector database

**Common Solutions:**
- No embeddings: Generate embeddings for content
- Threshold too high: Lower similarity threshold
- Invalid query: Check query format
- Database empty: Index content with embeddings

#### ai_features_router.py Issues

**Problem: AI Tutor Response Fails**
```json
{
  "detail": "Failed to generate AI response"
}
```

**Debugging Steps:**
1. Check conversation context
2. Verify Gemini API service
3. Test with different questions
4. Check response filtering

**Common Solutions:**
- API down: Check Gemini API status
- Invalid context: Verify conversation history
- Filtered response: Check content filtering
- Rate limit: Implement backoff strategy

### 07 Payment Router

#### payment_router.py Issues

**Problem: Payment Verification Fails**
```json
{
  "detail": "Payment verification failed"
}
```

**Debugging Steps:**
1. Check Razorpay webhook signature
2. Verify payment status in Razorpay
3. Test with test payment IDs
4. Check webhook configuration

**Common Solutions:**
- Signature mismatch: Verify webhook secret
- Invalid payment: Check payment status in Razorpay
- Webhook not received: Check webhook URL and SSL
- Configuration error: Verify Razorpay credentials

## Router-Specific Testing Commands

### Authentication Testing
```bash
# Test auth router
curl -X POST "$API_BASE_URL/register/parent/email" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Parent","email":"test@example.com","password":"Test@123"}'

# Test login router
curl -X POST "$API_BASE_URL/login/email" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123"}'

# Test verification router
curl -X POST "$API_BASE_URL/verify/email/send" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

### Onboarding Testing
```bash
# Test child router
curl -X POST "$API_BASE_URL/api/onboarding/child" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parent_id":"parent123","name":"Student","age":16,"grade":"11"}'

# Test preferences router
curl -X POST "$API_BASE_URL/api/onboarding/preferences" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parent_id":"parent123","language":"English","notifications":true}'

# Test exam router
curl -X POST "$API_BASE_URL/api/onboarding/exam/select" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parent_id":"parent123","exam_type":"JEE_MAIN","subject_preferences":{"Physics":40,"Chemistry":35,"Mathematics":25}}'
```

### Dashboard Testing
```bash
# Test parent dashboard
curl -X GET "$API_BASE_URL/api/parent/dashboard/child123" \
  -H "Authorization: Bearer $TOKEN"

# Test student dashboard
curl -X GET "$API_BASE_URL/api/student/today/student123" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

### Testing Module Testing
```bash
# Test question generation
curl -X POST "$API_BASE_URL/api/questions/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic":"Mechanics","exam_type":"JEE_MAIN","difficulty":"medium","num_questions":5}'

# Test diagnostic test
curl -X POST "$API_BASE_URL/api/diagnostic/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"child_id":"child123","exam_type":"JEE_MAIN"}'
```

### Learning Module Testing
```bash
# Test study center
curl -X GET "$API_BASE_URL/api/study/progress/student123" \
  -H "Authorization: Bearer $STUDENT_TOKEN"

# Test analytics
curl -X GET "$API_BASE_URL/api/analytics/performance/student123" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

### AI Features Testing
```bash
# Test RAG pipeline
curl -X POST "$API_BASE_URL/api/rag/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Newton laws explanation","context":"Physics"}'

# Test vector search
curl -X POST "$API_BASE_URL/api/vector/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"kinematics","similarity_threshold":0.7}'
```

### Payment Testing
```bash
# Test payment order creation
curl -X POST "$API_BASE_URL/api/payment/order/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id":"premium_monthly","amount":99900}'

# Test payment verification
curl -X POST "$API_BASE_URL/api/payment/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payment_id":"pay_test123","order_id":"order_test123","signature":"test_signature"}'
```

This comprehensive router-specific troubleshooting guide should help identify, diagnose, and resolve issues across all Mentor AI API endpoints efficiently.