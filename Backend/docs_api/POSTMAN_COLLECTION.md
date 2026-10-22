# Mentor AI Postman Collection Guide

## Overview

This guide explains how to use the Mentor AI Postman collection for comprehensive API testing. The collection includes pre-configured requests for all endpoints with proper authentication, environment variables, and test scripts.

## Getting Started

### 1. Import the Collection

**File Location:** `docs/Mentor_AI_Postman_Collection.json`

**Import Steps:**
1. Open Postman
2. Click "Import" in the top left
3. Select "File" tab
4. Choose "Upload Files"
5. Select the `Mentor_AI_Postman_Collection.json` file
6. Click "Import"

### 2. Configure Environment

**Create Environment Variables:**
1. In Postman, click the "Environment" dropdown (top right)
2. Click "Add" to create a new environment
3. Name the environment: `Mentor AI - Development`
4. Add the following variables:

| Variable | Initial Value | Description |
|----------|---------------|-------------|
| `api_base_url` | `http://localhost:8000` | Base API URL |
| `parent_token` | `{{parent_token}}` | Parent JWT access token |
| `child_token` | `{{child_token}}` | Child JWT access token |
| `parent_id` | `{{parent_id}}` | Test parent ID |
| `child_id` | `{{child_id}}` | Test child ID |
| `test_email` | `parent@test.com` | Test parent email |
| `test_password` | `Test@123` | Test password |
| `test_mobile` | `9876543210` | Test mobile number |
| `test_child_name` | `Test Student` | Test child name |
| `test_child_age` | `16` | Test child age |
| `test_child_grade` | `11` | Test child grade |
| `test_child_username` | `student123` | Test child username |
| `test_child_password` | `Test@123` | Test child password |

5. Set the environment as active by clicking the checkbox next to its name

## Collection Structure

### Folder Organization

The Postman collection is organized by functional areas:

```
Mentor AI API/
├── 01_Authentication/
│   ├── Parent Registration
│   ├── Login & Token Management
│   ├── Simple Registration
│   └── Email/Phone Verification
├── 02_Onboarding/
│   ├── Child Profile Management
│   ├── Parent Preferences
│   └── Exam Selection
├── 03_Dashboards/
│   ├── Parent Dashboard
│   └── Student Dashboard
├── 04_Testing/
│   ├── Diagnostic Tests
│   ├── Test Management
│   ├── Question Generation
│   └── Study Schedules
├── 05_Learning/
│   ├── Study Center
│   ├── Syllabus Coverage
│   ├── Analytics
│   └── Gamification
├── 06_AI_Features/
│   ├── AI Tutor Chat
│   ├── RAG Question Generation
│   ├── Vector Search & Embeddings
│   └── Recommendations & Analysis
├── 07_Payments/
│   ├── Subscription Management
│   └── Payment Processing
└── Utilities/
    ├── Health Checks
    └── System Status
```

## Authentication Setup

### Parent Registration Flow

**1. Email Registration:**
- **Request:** `POST /register/parent/email`
- **Pre-request Script:** 
  ```javascript
  // Set parent registration data
  pm.environment.set("test_email", "parent@test.com");
  pm.environment.set("test_password", "Test@123");
  pm.environment.set("test_mobile", "9876543210");
  ```

**2. Login and Token Storage:**
- **Request:** `POST /login/email`
- **Tests Script:**
  ```javascript
  // Login and store tokens
  const loginResponse = pm.response.json();
  pm.environment.set("parent_token", loginResponse.access_token);
  pm.environment.set("parent_id", loginResponse.parent_id);
  ```

### Child Authentication Flow

**1. Child Login:**
- **Request:** `POST /login/child`
- **Tests Script:**
  ```javascript
  // Child login and store tokens
  const childLoginResponse = pm.response.json();
  pm.environment.set("child_token", childLoginResponse.access_token);
  pm.environment.set("child_id", childLoginResponse.child_id);
  ```

## Testing Workflows

### Complete User Journey Test

**Test Sequence:**
1. **Parent Registration** → 2. **Email Verification** → 3. **Parent Login** → 4. **Child Profile Creation** → 5. **Child Login** → 6. **Exam Selection** → 7. **Diagnostic Test** → 8. **Study Center Usage**

**Automated Test Script:**
```javascript
// Complete user journey test
async function runCompleteJourney() {
    try {
        // 1. Parent Registration
        const registerResponse = await pm.sendRequest({
            url: "{{api_base_url}}/register/parent/email",
            method: "POST",
            header: {
                "Content-Type": "application/json"
            },
            body: {
                name: pm.environment.get("test_child_name"),
                email: pm.environment.get("test_email"),
                password: pm.environment.get("test_password"),
                mobile: pm.environment.get("test_mobile")
            }
        });
        
        // 2. Email Verification
        const verifyResponse = await pm.sendRequest({
            url: "{{api_base_url}}/verify/email/confirm",
            method: "POST",
            header: {
                "Content-Type": "application/json"
            },
            body: {
                email: pm.environment.get("test_email"),
                verification_code: "123456" // Use actual code from response
            }
        });
        
        // 3. Parent Login
        const loginResponse = await pm.sendRequest({
            url: "{{api_base_url}}/login/email",
            method: "POST",
            header: {
                "Content-Type": "application/json"
            },
            body: {
                email: pm.environment.get("test_email"),
                password: pm.environment.get("test_password")
            }
        });
        
        // Store tokens for subsequent requests
        pm.environment.set("parent_token", loginResponse.access_token);
        pm.environment.set("parent_id", loginResponse.parent_id);
        
        // 4. Child Profile Creation
        const childResponse = await pm.sendRequest({
            url: "{{api_base_url}}/api/onboarding/child",
            method: "POST",
            header: {
                "Content-Type": "application/json",
                "Authorization": "Bearer {{parent_token}}"
            },
            body: {
                parent_id: pm.environment.get("parent_id"),
                name: pm.environment.get("test_child_name"),
                age: parseInt(pm.environment.get("test_child_age")),
                grade: parseInt(pm.environment.get("test_child_grade")),
                current_level: "beginner"
            }
        });
        
        // 5. Child Login
        const childLoginResponse = await pm.sendRequest({
            url: "{{api_base_url}}/login/child",
            method: "POST",
            header: {
                "Content-Type": "application/json"
            },
            body: {
                username: pm.environment.get("test_child_username"),
                password: pm.environment.get("test_child_password")
            }
        });
        
        // Store child token
        pm.environment.set("child_token", childLoginResponse.access_token);
        pm.environment.set("child_id", childLoginResponse.child_id);
        
        // 6. Exam Selection
        const examResponse = await pm.sendRequest({
            url: "{{api_base_url}}/api/onboarding/exam/select",
            method: "POST",
            header: {
                "Content-Type": "application/json",
                "Authorization": "Bearer {{parent_token}}"
            },
            body: {
                parent_id: pm.environment.get("parent_id"),
                exam_type: "JEE_MAIN",
                exam_date: "2024-05-01",
                subject_preferences: {
                    "Physics": 40,
                    "Chemistry": 35,
                    "Mathematics": 25
                }
            }
        });
        
        console.log("Complete user journey test completed successfully!");
        
    } catch (error) {
        console.error("Journey test failed:", error);
    }
}

// Run the complete journey
runCompleteJourney();
```

### Individual Endpoint Testing

**Example: Diagnostic Test Flow**
```javascript
// Test diagnostic test lifecycle
async function testDiagnosticFlow() {
    try {
        // 1. Get available diagnostic tests
        const testsResponse = await pm.sendRequest({
            url: "{{api_base_url}}/api/testing/diagnostic/list",
            method: "GET",
            header: {
                "Authorization": "Bearer {{parent_token}}"
            }
        });
        
        if (testsResponse.data && testsResponse.data.length > 0) {
            const testId = testsResponse.data[0].diagnostic_test_id;
            
            // 2. Start diagnostic test
            const startResponse = await pm.sendRequest({
                url: "{{api_base_url}}/api/testing/diagnostic/start",
                method: "POST",
                header: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {{child_token}}"
                },
                body: {
                    child_id: pm.environment.get("child_id"),
                    diagnostic_test_id: testId
                }
            });
            
            // 3. Submit test answers
            const answers = [
                {"question_id": "q1", "selected_option": "A"},
                {"question_id": "q2", "selected_option": "B"},
                {"question_id": "q3", "selected_option": "C"}
            ];
            
            const submitResponse = await pm.sendRequest({
                url: "{{api_base_url}}/api/testing/diagnostic/submit",
                method: "POST",
                header: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {{child_token}}"
                },
                body: {
                    child_id: pm.environment.get("child_id"),
                    diagnostic_test_id: testId,
                    answers: answers
                }
            });
            
            // 4. Get results
            const resultsResponse = await pm.sendRequest({
                url: "{{api_base_url}}/api/testing/diagnostic/results/" + testId,
                method: "GET",
                header: {
                    "Authorization": "Bearer {{child_token}}"
                }
            });
            
            console.log("Diagnostic test flow completed!");
        }
        
    } catch (error) {
        console.error("Diagnostic test failed:", error);
    }
}

testDiagnosticFlow();
```

## Advanced Features

### Batch Operations

**Example: Batch Question Generation**
```javascript
// Test RAG batch question generation
async function testBatchGeneration() {
    try {
        const batchResponse = await pm.sendRequest({
            url: "{{api_base_url}}/api/rag/generate-batch",
            method: "POST",
            header: {
                "Content-Type": "application/json",
                "Authorization": "Bearer {{child_token}}"
            },
            body: {
                topics: ["Calculus", "Algebra", "Trigonometry"],
                exam_type: "JEE_MAIN",
                difficulty: "medium",
                questions_per_topic: 5,
                include_explanations: true
            }
        });
        
        console.log("Batch generation response:", batchResponse);
        
    } catch (error) {
        console.error("Batch generation failed:", error);
    }
}

testBatchGeneration();
```

### Error Handling Tests

**Example: Validation Error Testing**
```javascript
// Test various validation scenarios
async function testValidationErrors() {
    const testCases = [
        {
            name: "Empty email",
            request: {
                email: "",
                password: "Test@123"
            }
        },
        {
            name: "Invalid email format",
            request: {
                email: "invalid-email",
                password: "Test@123"
            }
        },
        {
            name: "Short password",
            request: {
                email: "test@example.com",
                password: "123"
            }
        }
    ];
    
    for (const testCase of testCases) {
        try {
            const response = await pm.sendRequest({
                url: "{{api_base_url}}/register/parent/email",
                method: "POST",
                header: {
                    "Content-Type": "application/json"
                },
                body: testCase.request
            });
            
            console.log(`${testCase.name}:`, response.status, response.json());
            
        } catch (error) {
            console.error(`${testCase.name} failed:`, error);
        }
    }
}

testValidationErrors();
```

## Performance Testing

### Load Testing with Postman Runner

**1. Create Collection Runner:**
- Open Postman
- Click "Runner" in the bottom left
- Create new run
- Select "Mentor AI API" collection
- Choose "Mentor AI - Development" environment
- Set iterations to 10
- Set delay to 1000ms between requests

**2. Configure Test Data:**
- Use pre-request scripts to generate dynamic test data
- Implement randomization for realistic testing
- Set up data cleanup in post-request scripts

**3. Monitor Results:**
- Check response times in results
- Monitor success/failure rates
- Export results to CSV for analysis

## Environment-Specific Configurations

### Development Environment
```json
{
  "name": "Mentor AI - Development",
  "values": {
    "api_base_url": "http://localhost:8000",
    "test_email": "dev-parent@test.com",
    "test_password": "Dev@123",
    "test_mobile": "9876543210"
  }
}
```

### Staging Environment
```json
{
  "name": "Mentor AI - Staging",
  "values": {
    "api_base_url": "https://staging-api.mentorai.com",
    "test_email": "staging-parent@test.com",
    "test_password": "Staging@123",
    "test_mobile": "9876543211"
  }
}
```

### Production Environment
```json
{
  "name": "Mentor AI - Production",
  "values": {
    "api_base_url": "https://api.mentorai.com",
    "test_email": "prod-parent@test.com",
    "test_password": "Prod@123",
    "test_mobile": "9876543212"
  }
}
```

## Best Practices

### 1. Request Organization

- **Use Descriptive Names:** Name your requests clearly
- **Add Documentation:** Include request descriptions in each request
- **Organize in Folders:** Group related tests in folders
- **Use Scripts:** Automate repetitive tasks with pre-request scripts

### 2. Response Validation

- **Status Code Checks:** Always verify expected status codes
- **Response Schema:** Validate response structure against documentation
- **Error Handling:** Test both success and failure scenarios
- **Data Types:** Check data types and formats

### 3. Authentication Management

- **Token Refresh:** Implement automatic token refresh in scripts
- **Token Storage:** Use environment variables for sensitive tokens
- **Multi-User Testing:** Use separate environments for different user roles
- **Logout Testing:** Test token invalidation and cleanup

### 4. Test Data Management

- **Isolation:** Use unique test data for each test run
- **Cleanup:** Implement test data cleanup scripts
- **Reset:** Use scripts to reset database state between tests
- **Versioning:** Track test data schema versions

## Debugging in Postman

### 1. Console Output

- **Enable Console:** Use `console.log()` in pre-request scripts
- **View Network:** Check Network tab for request/response details
- **Error Details:** Examine error responses in Console tab
- **Performance:** Monitor timing in the response details

### 2. Test Results

- **Save Responses:** Save successful responses for reference
- **Export Results:** Use Runner results export functionality
- **Compare Results:** Use diff tools to compare expected vs actual
- **Share Collections:** Export test collections for team collaboration

### 3. Advanced Debugging

- **Breakpoints:** Set breakpoints in pre-request scripts
- **Conditional Logic:** Use `if/else` for complex test scenarios
- **Loop Testing:** Use `for` loops for repetitive testing
- **Error Simulation:** Test error conditions intentionally

## Integration with CI/CD

### 1. Newman Command Line

**Installation:**
```bash
# Install Newman (Postman CLI)
npm install -g newman

# Run collection
newman run "Mentor AI API.postman_collection.json" \
  --environment "Mentor AI - Development" \
  --reporters cli,html,json \
  --reporter-html-export "test-report.html" \
  --reporter-json-export "test-results.json"
```

### 2. GitHub Actions Integration

**Workflow Example:**
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '16'
      - name: Install Newman
        run: npm install -g newman
      - name: Run API Tests
        run: |
          newman run "docs/Mentor_AI_Postman_Collection.json" \
            --environment "production" \
            --reporters json \
            --bail \
            --suppress-exit-code
      - name: Upload Test Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-results.json
```

## Troubleshooting Common Issues

### 1. Import/Export Problems

**Issue:** Collection import fails
**Solutions:**
- Check JSON syntax validation
- Ensure Postman version compatibility
- Try importing smaller sections first
- Validate environment variables format

### 2. Authentication Failures

**Issue:** 401 Unauthorized errors
**Solutions:**
- Verify environment variables are set correctly
- Check token expiration and refresh logic
- Ensure Bearer prefix in Authorization header
- Validate token format and encoding

### 3. Request/Response Mismatches

**Issue:** Expected response doesn't match actual
**Solutions:**
- Check API documentation for correct format
- Verify request payload is properly formatted
- Check for missing required fields
- Validate data types and constraints

### 4. Performance Issues

**Issue:** Slow response times in Postman
**Solutions:**
- Disable "Automatically follow redirects"
- Check "Send request immediately" setting
- Use smaller test data payloads
- Monitor network connectivity to API server
- Check Postman desktop app version

## Additional Resources

### 1. Documentation Links

- [Mentor API Documentation](docs_api/README.md)
- [Authentication Guide](docs_api/01_authentication/README.md)
- [Testing Workflow](docs_api/TESTING_WORKFLOW.md)
- [Troubleshooting Guide](docs_api/TROUBLESHOOTING_GUIDE.md)

### 2. External Tools

- [Postman Learning Center](https://learning.postman.com/)
- [Newman Documentation](https://learning.postman.com/docs/newman)
- [Postman API Documentation](https://learning.postman.com/docs/postman)

### 3. Community Resources

- [Mentor AI GitHub Repository](https://github.com/mentor-ai/api)
- [API Issues Tracker](https://github.com/mentor-ai/issues)
- [Developer Community Forum](https://community.mentorai.com)

This comprehensive guide should help you effectively test the Mentor AI API using Postman, from basic authentication to advanced AI features and payment processing.