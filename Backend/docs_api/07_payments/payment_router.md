# Payment Router API Testing Guide

## Overview

The Payment router provides endpoints for subscription management and payment processing using Razorpay. It handles subscription plans, order creation, payment verification, and transaction history for the Mentor AI platform.

**Base URL:** `http://localhost:8000/api/payment`

## Authentication

Most endpoints require JWT authentication:
```bash
Authorization: Bearer <access_token>
```

**Exception:** The `/plans` endpoint is public (no authentication required).

## Endpoints

### 1. Get Subscription Plans

**Endpoint:** `GET /api/payment/plans`

Retrieve all available subscription plans for the platform.

#### Request Example (curl):
```bash
curl -X GET http://localhost:8000/api/payment/plans
```

#### Expected Response (200 OK):
```json
[
  {
    "plan_id": "free",
    "name": "Free Plan",
    "price": 0,
    "duration_days": 365,
    "features": ["1 diagnostic test", "Basic analytics"],
    "currency": "INR",
    "is_active": true
  },
  {
    "plan_id": "premium_monthly",
    "name": "Premium Monthly",
    "price": 99900,
    "duration_days": 30,
    "features": [
      "Unlimited tests",
      "Advanced analytics",
      "AI-powered recommendations",
      "Personalized study schedules",
      "24/7 doubt support",
      "Video solutions"
    ],
    "currency": "INR",
    "is_active": true,
    "description": "Complete access to all premium features for 30 days",
    "discount_percentage": 10
  },
  {
    "plan_id": "premium_yearly",
    "name": "Premium Yearly",
    "price": 99000,
    "duration_days": 365,
    "features": [
      "Unlimited tests",
      "Advanced analytics",
      "AI-powered recommendations",
      "Personalized study schedules",
      "24/7 doubt support",
      "Video solutions"
    ],
    "currency": "INR",
    "is_active": true,
    "description": "Best value - Save 17% with yearly billing",
    "discount_percentage": 17
  }
]
```

#### Error Scenarios:

**500 Internal Server Error:**
```json
{
  "detail": "Unable to retrieve subscription plans. Please try again later."
}
```

---

### 2. Create Payment Order

**Endpoint:** `POST /api/payment/create-order`

Create a Razorpay payment order for subscription purchase.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/payment/create-order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "parent_id": "parent_abc123",
    "plan_id": "premium_monthly",
    "apply_discount": false
  }'
```

#### Request Example (Postman):
```json
{
  "parent_id": "parent_abc123",
  "plan_id": "premium_monthly",
  "apply_discount": false
}
```

#### Expected Response (201 Created):
```json
{
  "order_id": "order_MNxkZ1aB2cD3eF",
  "amount": 99900,
  "currency": "INR",
  "receipt": "rcpt_20240115_103000_A7K9M",
  "status": "created"
}
```

#### Error Scenarios:

**400 Bad Request - Invalid plan ID:**
```json
{
  "detail": "Invalid plan_id 'invalid_plan'. Must be one of: premium_monthly, premium_yearly, basic_monthly, basic_yearly"
}
```

**401 Unauthorized - Not logged in:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden - Creating order for different parent:**
```json
{
  "detail": "You can only create payment orders for your own account"
}
```

**404 Not Found - Plan not found:**
```json
{
  "detail": "Plan 'expired_plan' not found or is not active"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Unable to create payment order. Please try again later."
}
```

---

### 3. Verify Payment

**Endpoint:** `POST /api/payment/verify`

Verify Razorpay payment signature and activate subscription.

#### Request Example (curl):
```bash
curl -X POST http://localhost:8000/api/payment/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "order_id": "order_MNxkZ1aB2cD3eF",
    "payment_id": "pay_MNxkZ1aB2cD3eF",
    "razorpay_signature": "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
  }'
```

#### Expected Response (200 OK):
```json
{
  "subscription_id": "sub_parent_abc123_1705312200",
  "parent_id": "parent_abc123",
  "plan_id": "premium_monthly",
  "plan_name": "Premium Monthly",
  "status": "active",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-02-14T10:30:00Z",
  "auto_renew": false,
  "amount_paid": 99900,
  "currency": "INR",
  "payment_id": "pay_MNxkZ1aB2cD3eF",
  "order_id": "order_MNxkZ1aB2cD3eF"
}
```

#### Error Scenarios:

**400 Bad Request - Invalid signature:**
```json
{
  "detail": "Payment verification failed: Invalid signature"
}
```

**401 Unauthorized - Not logged in:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden - Verifying payment for different parent:**
```json
{
  "detail": "You can only verify payments for your own account"
}
```

**500 Internal Server Error - Verification failed:**
```json
{
  "detail": "Unable to verify payment. Please contact support."
}
```

---

### 4. Get Subscription Status

**Endpoint:** `GET /api/payment/subscription/{parent_id}`

Retrieve current subscription status for a parent.

#### Request Example (curl):
```bash
curl -X GET "http://localhost:8000/api/payment/subscription/parent_abc123" \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "is_active": true,
  "plan_name": "Premium Monthly",
  "plan_id": "premium_monthly",
  "status": "active",
  "days_remaining": 25,
  "end_date": "2024-02-14T10:30:00Z",
  "auto_renew": false,
  "features": [
    "Unlimited tests",
    "Advanced analytics",
    "AI-powered recommendations",
    "Personalized study schedules",
    "24/7 doubt support",
    "Video solutions"
  ],
  "amount_paid": 99900
}
```

#### Error Scenarios:

**401 Unauthorized - Not logged in:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden - Accessing another parent's subscription:**
```json
{
  "detail": "You can only access your own subscription information"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Unable to retrieve subscription status. Please try again later."
}
```

---

### 5. Get Transaction History

**Endpoint:** `GET /api/payment/transactions/{parent_id}`

Retrieve complete transaction history for a parent.

#### Request Example (curl):
```bash
curl -X GET "http://localhost:8000/api/payment/transactions/parent_abc123" \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
[
  {
    "transaction_id": "txn_abc123",
    "parent_id": "parent_abc123",
    "order_id": "order_MNxkZ1aB2cD3eF",
    "payment_id": "pay_MNxkZ1aB2cD3eF",
    "amount": 99900,
    "currency": "INR",
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:31:00Z",
    "plan_id": "premium_monthly"
  },
  {
    "transaction_id": "txn_def456",
    "parent_id": "parent_abc123",
    "order_id": "order_LkjHGFDS789",
    "payment_id": "pay_LkjHGFDS5678",
    "amount": 99000,
    "currency": "INR",
    "status": "completed",
    "created_at": "2023-12-15T10:30:00Z",
    "completed_at": "2023-12-15T10:35:00Z",
    "plan_id": "premium_yearly"
  },
  {
    "transaction_id": "txn_ghi789",
    "parent_id": "parent_abc123",
    "order_id": "order_XyZ123aB4cD5eF",
    "payment_id": null,
    "amount": 99900,
    "currency": "INR",
    "status": "failed",
    "created_at": "2024-01-10T10:30:00Z",
    "completed_at": "2024-01-10T10:45:00Z",
    "plan_id": "premium_monthly",
    "error_message": "Payment declined by bank"
  }
]
```

#### Error Scenarios:

**401 Unauthorized - Not logged in:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden - Accessing another parent's transactions:**
```json
{
  "detail": "You can only access your own transaction history"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Unable to retrieve transaction history. Please try again later."
}
```

---

### 6. Cancel Subscription

**Endpoint:** `POST /api/payment/cancel/{parent_id}`

Cancel active subscription for a parent.

#### Request Example (curl):
```bash
curl -X POST "http://localhost:8000/api/payment/cancel/parent_abc123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>"
```

#### Expected Response (200 OK):
```json
{
  "subscription_id": "sub_parent_abc123_1705312200",
  "parent_id": "parent_abc123",
  "plan_id": "premium_monthly",
  "plan_name": "Premium Monthly",
  "status": "cancelled",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-02-14T10:30:00Z",
  "auto_renew": false,
  "amount_paid": 99900,
  "currency": "INR"
}
```

#### Error Scenarios:

**401 Unauthorized - Not logged in:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden - Canceling another parent's subscription:**
```json
{
  "detail": "You can only cancel your own subscription"
}
```

**404 Not Found - No active subscription:**
```json
{
  "detail": "No active subscription found to cancel"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Unable to cancel subscription. Please contact support."
}
```

## Testing Workflow

### Complete Payment Testing

1. **Get Available Plans:**
   ```bash
   curl -X GET http://localhost:8000/api/payment/plans
   ```

2. **Create Payment Order:**
   ```bash
   curl -X POST http://localhost:8000/api/payment/create-order \
     -H "Authorization: Bearer <access_token>" \
     -d '{"parent_id":"parent_123","plan_id":"premium_monthly"}'
   ```

3. **Simulate Payment (Manual):**
   - Use Razorpay test environment
   - Complete payment flow with test card
   - Note the payment_id returned by Razorpay

4. **Verify Payment:**
   ```bash
   curl -X POST http://localhost:8000/api/payment/verify \
     -H "Authorization: Bearer <access_token>" \
     -d '{"order_id":"order_abc123","payment_id":"pay_xyz789","razorpay_signature":"signature"}'
   ```

5. **Check Subscription Status:**
   ```bash
   curl -X GET "http://localhost:8000/api/payment/subscription/parent_123" \
     -H "Authorization: Bearer <access_token>"
   ```

6. **Get Transaction History:**
   ```bash
   curl -X GET "http://localhost:8000/api/payment/transactions/parent_123" \
     -H "Authorization: Bearer <access_token>"
   ```

7. **Cancel Subscription:**
   ```bash
   curl -X POST "http://localhost:8000/api/payment/cancel/parent_123" \
     -H "Authorization: Bearer <access_token>"
   ```

## Troubleshooting

### Common Issues

1. **Order Creation Failed:**
   - Check if parent_id matches authenticated user
   - Verify plan_id is valid and active
   - Check Razorpay API key configuration
   - Ensure proper request headers

2. **Payment Verification Failed:**
   - Verify signature is correctly calculated
   - Check order_id and payment_id match
   - Ensure Razorpay webhook is configured
   - Check for signature tampering attempts

3. **Subscription Not Activating:**
   - Verify payment was completed successfully
   - Check for duplicate subscription attempts
   - Ensure parent_id consistency across requests
   - Check Firestore connectivity

4. **Transaction History Issues:**
   - Verify parent authentication
   - Check if transactions exist for parent
   - Ensure proper date formatting
   - Check pagination for large histories

5. **Cancellation Problems:**
   - Verify subscription is currently active
   - Check for pending payments
   - Ensure proper authorization
   - Verify cancellation takes effect immediately

### Security Considerations

1. **Signature Verification:**
   - Always verify Razorpay signatures
   - Log failed verification attempts
   - Use Razorpay's official verification library
   - Implement webhook security

2. **Authorization Checks:**
   - Parents can only access their own data
   - Validate JWT tokens on every request
   - Implement proper session management
   - Check for token expiration

3. **Payment Security:**
   - Never store raw card details
   - Use Razorpay's secure payment flow
   - Implement proper error handling
   - Log all payment events

### AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT/Claude when debugging payment issues:

```
I'm testing Mentor AI payment system and encountering an issue. Please help me debug:

**System Context:**
- Mentor AI uses Razorpay for payment processing
- Supports subscription plans: Free, Premium Monthly, Premium Yearly
- Prices in paise (100 paise = 1 rupee)
- Payment flow: Create Order → Complete Payment → Verify Signature → Activate Subscription

**Issue Details:**
- Endpoint: [POST/GET endpoint URL]
- Request payload: [Copy exact JSON request]
- Error response: [Copy exact error message]
- Expected behavior: [Describe what should happen]

**Environment:**
- Razorpay mode: [Test/Live]
- API key: [Configured/Not configured]
- Testing mode: [Yes/No]
- Webhook URL: [Configured/Not configured]

**Questions:**
1. What's causing this payment error based on response?
2. How can I fix Razorpay integration issues?
3. What additional logs should I check?
4. Are there any workarounds for this issue?

Please provide specific steps to resolve this payment processing issue.
```

## Reference Models

### Request Models

- **CreateOrderRequest** ([`models/payment_models.py`](models/payment_models.py:195))
  - `parent_id`: str - Firebase user ID of parent
  - `plan_id`: str - Subscription plan identifier
  - `apply_discount`: bool - Whether to apply available discounts

- **VerifyPaymentRequest** ([`models/payment_models.py`](models/payment_models.py:345))
  - `order_id`: str - Razorpay order ID
  - `payment_id`: str - Razorpay payment ID
  - `signature`: str - Razorpay signature for verification

### Response Models

- **SubscriptionPlan** ([`models/payment_models.py`](models/payment_models.py:56))
  - `plan_id`: str - Unique plan identifier
  - `name`: str - Display name of plan
  - `price`: int - Price in paise (100 paise = 1 rupee)
  - `duration_days`: int - Plan duration in days
  - `features`: List[str] - List of features
  - `currency`: str - Currency code (default: INR)
  - `is_active`: bool - Whether plan is available
  - `description`: Optional[str] - Plan description
  - `discount_percentage`: Optional[int] - Discount percentage

- **OrderResponse** ([`models/payment_models.py`](models/payment_models.py:257))
  - `order_id`: str - Razorpay order ID
  - `amount`: int - Order amount in paise
  - `currency`: str - Currency code
  - `receipt`: str - Unique receipt identifier
  - `created_at`: datetime - Order creation timestamp
  - `status`: str - Order status

- **SubscriptionDetails** ([`models/payment_models.py`](models/payment_models.py:402))
  - `subscription_id`: str - Unique subscription identifier
  - `parent_id`: str - Firebase user ID of parent
  - `plan_id`: str - Subscription plan identifier
  - `plan_name`: str - Display name of plan
  - `status`: SubscriptionStatus - Current status
  - `start_date`: datetime - Subscription start timestamp
  - `end_date`: datetime - Subscription expiry timestamp
  - `auto_renew`: bool - Whether subscription auto-renews
  - `amount_paid`: int - Amount paid in paise
  - `currency`: Currency - Currency code
  - `payment_id`: Optional[str] - Razorpay payment ID
  - `created_at`: datetime - When subscription was created
  - `updated_at`: datetime - Last update timestamp

- **TransactionRecord** ([`models/payment_models.py`](models/payment_models.py:551))
  - `transaction_id`: str - Unique transaction identifier
  - `parent_id`: str - Firebase user ID of parent
  - `order_id`: str - Razorpay order ID
  - `payment_id`: Optional[str] - Razorpay payment ID
  - `amount`: int - Transaction amount in paise
  - `currency`: Currency - Currency code
  - `status`: TransactionStatus - Transaction status
  - `plan_id`: str - Subscription plan identifier
  - `error_message`: Optional[str] - Error message if failed
  - `created_at`: datetime - When transaction was created
  - `completed_at`: Optional[datetime] - When transaction was completed

- **SubscriptionStatusResponse** ([`models/payment_models.py`](models/payment_models.py:674))
  - `is_active`: bool - Whether subscription is currently active
  - `plan_name`: str - Display name of plan
  - `plan_id`: str - Subscription plan identifier
  - `days_remaining`: int - Days until subscription expires
  - `expires_at`: datetime - Subscription expiry timestamp
  - `features`: List[str] - List of features
  - `auto_renew`: bool - Whether subscription will auto-renew
  - `amount_paid`: Optional[int] - Amount paid in paise

## Service Dependencies

- **Razorpay API**: Payment processing service
- **Subscription Service**: Subscription management
- **Payment Service**: Payment transaction handling
- **Authentication Service**: JWT token validation
- **Firestore Database**: Subscription and transaction storage

## Razorpay Integration

1. **Order Creation**: Create order with Razorpay API
2. **Payment Processing**: Redirect to Razorpay checkout
3. **Payment Completion**: Razorpay webhook notifies backend
4. **Signature Verification**: Verify payment authenticity
5. **Subscription Activation**: Update subscription in database

## Currency and Pricing

1. **Base Currency**: INR (Indian Rupee)
2. **Price Unit**: Paise (100 paise = 1 rupee)
3. **Display Conversion**: Divide by 100 for rupee display
4. **Supported Plans**: Free, Premium Monthly, Premium Yearly
5. **Discount System**: Percentage-based discounts

## Additional Resources

- [Razorpay Documentation](https://razorpay.com/docs)
- [Payment Service Implementation](services/payment_service.py)
- [Subscription Service Implementation](services/subscription_service.py)
- [Razorpay Python SDK](https://github.com/razorpay/razorpay-python)
- [Webhook Integration Guide](docs/razorpay_webhook_guide.md)