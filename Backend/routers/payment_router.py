"""
Payment Router Module for Mentor AI Platform.

This module defines FastAPI endpoints for payment processing and subscription
management using Razorpay for the JEE/NEET exam preparation platform.

Endpoints:
- GET /api/payment/plans: Get all available subscription plans
- POST /api/payment/create-order: Create Razorpay payment order
- POST /api/payment/verify: Verify payment and activate subscription
- GET /api/payment/subscription/{parent_id}: Get current subscription status
- GET /api/payment/transactions/{parent_id}: Get transaction history
- POST /api/payment/cancel/{parent_id}: Cancel subscription

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status

from models.payment_models import (
    SubscriptionPlan,
    CreateOrderRequest,
    OrderResponse,
    VerifyPaymentRequest,
    SubscriptionDetails,
    TransactionRecord,
    SubscriptionStatusResponse
)
from services.payment_service import PaymentService, PaymentServiceError, PaymentVerificationError
from services.subscription_service import SubscriptionService
from middleware.testing_auth import get_current_user_testing as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/payment",
    tags=["Payment"]
)

# Service instances (singleton pattern)
_payment_service = None
_subscription_service = None


def get_payment_service() -> PaymentService:
    """
    Dependency to get PaymentService instance.
    
    Returns:
        PaymentService: Singleton instance of payment service
    """
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service


def get_subscription_service() -> SubscriptionService:
    """
    Dependency to get SubscriptionService instance.
    
    Returns:
        SubscriptionService: Singleton instance of subscription service
    """
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service


# ==================== Endpoints ====================


@router.get(
    "/plans",
    response_model=List[SubscriptionPlan],
    status_code=status.HTTP_200_OK,
    summary="Get all available subscription plans",
    description="""
    Retrieve all available subscription plans for the platform.
    
    This is a **public endpoint** (no authentication required). It returns
    all active subscription plans including Free, Premium Monthly, and
    Premium Yearly plans with their features and pricing.
    
    **Returns:**
    - 200: List of available subscription plans
    - 500: Internal server error
    
    **Response includes:**
    - Plan ID and name
    - Price in paise (100 paise = 1 rupee)
    - Duration in days
    - List of features
    - Currency (INR by default)
    """
)
async def get_subscription_plans(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> List[SubscriptionPlan]:
    """
    Get all available subscription plans.
    
    Args:
        subscription_service: Injected SubscriptionService dependency
    
    Returns:
        List[SubscriptionPlan]: List of all active subscription plans
    
    Raises:
        HTTPException: 500 if unable to retrieve plans
    
    Example:
        Request:
        ```
        GET /api/payment/plans
        ```
        
        Response:
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
                "features": ["Unlimited tests", "Advanced analytics"],
                "currency": "INR",
                "is_active": true
            }
        ]
        ```
    """
    try:
        logger.info("Request to retrieve all subscription plans")
        plans = subscription_service.get_all_plans()
        logger.info(f"Successfully retrieved {len(plans)} subscription plans")
        return plans
    
    except Exception as e:
        logger.error(f"Error retrieving subscription plans: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve subscription plans. Please try again later."
        )


@router.post(
    "/create-order",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay payment order",
    description="""
    Create a Razorpay payment order for subscription purchase.
    
    This endpoint creates a Razorpay order that must be used to initiate
    the payment flow on the frontend. After creating the order, redirect
    the user to Razorpay checkout with the order_id.
    
    **Authentication:** Required (parent must be logged in)
    
    **Requirements:**
    - Valid parent_id (authenticated user)
    - Valid plan_id (must exist and be active)
    
    **Returns:**
    - 201: Order created successfully
    - 400: Invalid plan or validation error
    - 401: Unauthorized (not logged in)
    - 404: Plan not found
    - 500: Internal server error
    
    **Process:**
    1. Validate parent exists
    2. Validate plan exists and is active
    3. Create Razorpay order with amount
    4. Record pending transaction
    5. Return order details for payment
    """
)
async def create_payment_order(
    request: CreateOrderRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: str = Depends(get_current_user)
) -> OrderResponse:
    """
    Create Razorpay payment order for subscription purchase.
    
    Args:
        request: CreateOrderRequest with parent_id and plan_id
        payment_service: Injected PaymentService dependency
        current_user: Authenticated parent ID from JWT token
    
    Returns:
        OrderResponse: Order details including order_id and amount
    
    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 401 if not authenticated
        HTTPException: 403 if trying to create order for different parent
        HTTPException: 404 if plan not found
        HTTPException: 500 if order creation fails
    
    Example:
        Request:
        ```json
        POST /api/payment/create-order
        Headers:
            Authorization: Bearer <token>
        Body:
        {
            "parent_id": "parent_abc123",
            "plan_id": "premium_monthly"
        }
        ```
        
        Response:
        ```json
        {
            "order_id": "order_MNxkZ1aB2cD3eF",
            "amount": 99900,
            "currency": "INR",
            "receipt": "rcpt_20240115_103000_A7K9M",
            "status": "created"
        }
        ```
    """
    try:
        # Verify parent can only create order for themselves
        if request.parent_id != current_user:
            logger.warning(
                f"Parent {current_user} attempted to create order for {request.parent_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create payment orders for your own account"
            )
        
        logger.info(
            f"Creating payment order for parent {request.parent_id}, "
            f"plan {request.plan_id}"
        )
        
        # Create payment order
        order = payment_service.create_payment_order(
            parent_id=request.parent_id,
            plan_id=request.plan_id
        )
        
        logger.info(
            f"Payment order created successfully: {order.order_id} "
            f"for parent {request.parent_id}"
        )
        
        return order
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Handle validation errors (plan not found, etc.)
        logger.warning(f"Validation error creating payment order: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except PaymentServiceError as e:
        # Handle payment service errors
        logger.error(f"Payment service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error creating payment order: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create payment order. Please try again later."
        )


@router.post(
    "/verify",
    response_model=SubscriptionDetails,
    status_code=status.HTTP_200_OK,
    summary="Verify payment and activate subscription",
    description="""
    Verify Razorpay payment signature and activate subscription.
    
    This endpoint is called after the user completes payment on Razorpay.
    It verifies the payment signature to ensure authenticity, then activates
    the subscription for the parent.
    
    **Authentication:** Required (parent must be logged in)
    
    **Security:**
    - Signature verification prevents payment tampering
    - Invalid signatures are logged as security incidents
    - Failed verifications do not activate subscriptions
    
    **Returns:**
    - 200: Payment verified and subscription activated
    - 400: Invalid signature or verification failed
    - 401: Unauthorized (not logged in)
    - 500: Internal server error or activation failed
    
    **Process:**
    1. Verify payment signature using Razorpay utility
    2. Fetch order details to get parent_id and plan_id
    3. Activate subscription in Firestore
    4. Update transaction status to "completed"
    5. Return subscription details
    """
)
async def verify_payment(
    request: VerifyPaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: str = Depends(get_current_user)
) -> SubscriptionDetails:
    """
    Verify payment signature and activate subscription.
    
    Args:
        request: VerifyPaymentRequest with order_id, payment_id, signature
        payment_service: Injected PaymentService dependency
        current_user: Authenticated parent ID from JWT token
    
    Returns:
        SubscriptionDetails: Activated subscription details
    
    Raises:
        HTTPException: 400 if signature verification fails
        HTTPException: 401 if not authenticated
        HTTPException: 500 if subscription activation fails
    
    Example:
        Request:
        ```json
        POST /api/payment/verify
        Headers:
            Authorization: Bearer <token>
        Body:
        {
            "order_id": "order_MNxkZ1aB2cD3eF",
            "payment_id": "pay_MNxkZ1aB2cD3eF",
            "razorpay_signature": "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
        }
        ```
        
        Response:
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
    """
    try:
        logger.info(
            f"Verifying payment for order {request.order_id}, "
            f"payment {request.payment_id}"
        )
        
        # Verify and activate subscription
        subscription = payment_service.verify_and_activate(
            order_id=request.order_id,
            payment_id=request.payment_id,
            signature=request.razorpay_signature
        )
        
        # Verify current user owns this subscription
        if subscription.parent_id != current_user:
            logger.error(
                f"Parent {current_user} attempted to verify payment "
                f"for parent {subscription.parent_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only verify payments for your own account"
            )
        
        logger.info(
            f"Payment verified and subscription activated: "
            f"{subscription.subscription_id} for parent {subscription.parent_id}"
        )
        
        return subscription
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except PaymentVerificationError as e:
        # Handle signature verification errors
        logger.error(f"Payment verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except PaymentServiceError as e:
        # Handle payment service errors
        logger.error(f"Payment service error during verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error verifying payment: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to verify payment. Please contact support."
        )


@router.get(
    "/subscription/{parent_id}",
    response_model=SubscriptionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current subscription status",
    description="""
    Retrieve current subscription status for a parent.
    
    This endpoint returns detailed subscription status including plan name,
    active status, days remaining, and auto-renewal information.
    
    **Authentication:** Required (parent must be logged in)
    
    **Security:**
    - Parents can only view their own subscription
    - Attempting to view others' subscriptions returns 403 Forbidden
    
    **Returns:**
    - 200: Subscription status retrieved successfully
    - 401: Unauthorized (not logged in)
    - 403: Forbidden (trying to access another parent's subscription)
    - 500: Internal server error
    
    **Note:**
    - If no subscription exists, returns Free Plan status
    - Expired subscriptions are automatically updated to "expired" status
    """
)
async def get_subscription_status(
    parent_id: str,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    current_user: str = Depends(get_current_user)
) -> SubscriptionStatusResponse:
    """
    Get current subscription status for a parent.
    
    Args:
        parent_id: Parent ID to get subscription for
        subscription_service: Injected SubscriptionService dependency
        current_user: Authenticated parent ID from JWT token
    
    Returns:
        SubscriptionStatusResponse: Current subscription status
    
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if trying to access another parent's subscription
        HTTPException: 500 if unable to retrieve subscription
    
    Example:
        Request:
        ```
        GET /api/payment/subscription/parent_abc123
        Headers:
            Authorization: Bearer <token>
        ```
        
        Response:
        ```json
        {
            "is_active": true,
            "plan_name": "Premium Monthly",
            "plan_id": "premium_monthly",
            "status": "active",
            "days_remaining": 25,
            "end_date": "2024-02-14T10:30:00Z",
            "auto_renew": false
        }
        ```
    """
    try:
        # Verify parent can only access own subscription
        if parent_id != current_user:
            logger.warning(
                f"Parent {current_user} attempted to access subscription "
                f"of parent {parent_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own subscription information"
            )
        
        logger.info(f"Retrieving subscription status for parent {parent_id}")
        
        # Get subscription status
        status_response = subscription_service.check_subscription_status(parent_id)
        
        logger.info(
            f"Subscription status retrieved for parent {parent_id}: "
            f"Plan {status_response.plan_name}, Active {status_response.is_active}"
        )
        
        return status_response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error retrieving subscription status: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve subscription status. Please try again later."
        )


@router.get(
    "/transactions/{parent_id}",
    response_model=List[TransactionRecord],
    status_code=status.HTTP_200_OK,
    summary="Get transaction history",
    description="""
    Retrieve complete transaction history for a parent.
    
    This endpoint returns all payment transactions associated with the parent,
    ordered by creation date (most recent first).
    
    **Authentication:** Required (parent must be logged in)
    
    **Security:**
    - Parents can only view their own transactions
    - Attempting to view others' transactions returns 403 Forbidden
    
    **Returns:**
    - 200: Transaction history retrieved successfully (can be empty list)
    - 401: Unauthorized (not logged in)
    - 403: Forbidden (trying to access another parent's transactions)
    - 500: Internal server error
    
    **Transaction statuses:**
    - pending: Order created, payment not completed
    - completed: Payment successful
    - failed: Payment failed
    - refunded: Payment refunded
    """
)
async def get_transaction_history(
    parent_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: str = Depends(get_current_user)
) -> List[TransactionRecord]:
    """
    Get transaction history for a parent.
    
    Args:
        parent_id: Parent ID to get transactions for
        payment_service: Injected PaymentService dependency
        current_user: Authenticated parent ID from JWT token
    
    Returns:
        List[TransactionRecord]: List of all transactions (can be empty)
    
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if trying to access another parent's transactions
        HTTPException: 500 if unable to retrieve transactions
    
    Example:
        Request:
        ```
        GET /api/payment/transactions/parent_abc123
        Headers:
            Authorization: Bearer <token>
        ```
        
        Response:
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
                "completed_at": "2024-01-15T10:31:00Z"
            }
        ]
        ```
    """
    try:
        # Verify parent can only access own transactions
        if parent_id != current_user:
            logger.warning(
                f"Parent {current_user} attempted to access transactions "
                f"of parent {parent_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own transaction history"
            )
        
        logger.info(f"Retrieving transaction history for parent {parent_id}")
        
        # Get transaction history
        transactions = payment_service.get_transaction_history(parent_id)
        
        logger.info(
            f"Transaction history retrieved for parent {parent_id}: "
            f"{len(transactions)} transactions found"
        )
        
        return transactions
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error retrieving transaction history: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve transaction history. Please try again later."
        )


@router.post(
    "/cancel/{parent_id}",
    response_model=SubscriptionDetails,
    status_code=status.HTTP_200_OK,
    summary="Cancel subscription",
    description="""
    Cancel active subscription for a parent.
    
    This endpoint cancels the current active subscription. The subscription
    status will be set to "cancelled" and will not auto-renew.
    
    **Authentication:** Required (parent must be logged in)
    
    **Security:**
    - Parents can only cancel their own subscriptions
    - Attempting to cancel others' subscriptions returns 403 Forbidden
    
    **Returns:**
    - 200: Subscription cancelled successfully
    - 401: Unauthorized (not logged in)
    - 403: Forbidden (trying to cancel another parent's subscription)
    - 404: No active subscription found to cancel
    - 500: Internal server error
    
    **Important:**
    - Cancelled subscriptions remain in history for record-keeping
    - Parents can purchase a new subscription after cancellation
    - Cancellation is immediate and cannot be undone
    """
)
async def cancel_subscription(
    parent_id: str,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    current_user: str = Depends(get_current_user)
) -> SubscriptionDetails:
    """
    Cancel active subscription for a parent.
    
    Args:
        parent_id: Parent ID to cancel subscription for
        subscription_service: Injected SubscriptionService dependency
        current_user: Authenticated parent ID from JWT token
    
    Returns:
        SubscriptionDetails: Cancelled subscription details
    
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if trying to cancel another parent's subscription
        HTTPException: 404 if no subscription found
        HTTPException: 500 if cancellation fails
    
    Example:
        Request:
        ```
        POST /api/payment/cancel/parent_abc123
        Headers:
            Authorization: Bearer <token>
        ```
        
        Response:
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
    """
    try:
        # Verify parent can only cancel own subscription
        if parent_id != current_user:
            logger.warning(
                f"Parent {current_user} attempted to cancel subscription "
                f"of parent {parent_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own subscription"
            )
        
        logger.info(f"Cancelling subscription for parent {parent_id}")
        
        # Cancel subscription
        subscription = subscription_service.cancel_subscription(parent_id)
        
        logger.info(
            f"Subscription cancelled successfully: "
            f"{subscription.subscription_id} for parent {parent_id}"
        )
        
        return subscription
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Handle no subscription found
        logger.warning(f"Cannot cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error cancelling subscription: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to cancel subscription. Please contact support."
        )
