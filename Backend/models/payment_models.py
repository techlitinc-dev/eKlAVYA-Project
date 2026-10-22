"""
Payment Models for Mentor AI Platform.

This module defines Pydantic models for payment processing and subscription
management using Razorpay for the JEE/NEET exam preparation platform.

Models:
- SubscriptionPlan: Subscription plan details and pricing
- CreateOrderRequest: Request to create a Razorpay order
- OrderResponse: Razorpay order creation response
- VerifyPaymentRequest: Payment signature verification request
- SubscriptionDetails: Active subscription information
- TransactionRecord: Payment transaction details
- SubscriptionStatusResponse: Subscription status for user

Author: Mentor AI Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


# ==================== Enums ====================


class SubscriptionStatus(str, Enum):
    """Subscription status values."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class TransactionStatus(str, Enum):
    """Transaction status values."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Currency(str, Enum):
    """Supported currency codes."""
    INR = "INR"
    USD = "USD"


# ==================== Subscription Plan Model ====================


class SubscriptionPlan(BaseModel):
    """
    Subscription plan details and pricing.
    
    This model defines a subscription plan with pricing, duration, and features
    included. All amounts are stored in paise (1 rupee = 100 paise) for precision.
    
    Attributes:
        plan_id: Unique plan identifier (e.g., "premium_monthly")
        name: Display name of the plan (e.g., "Premium Monthly")
        price: Price in paise (e.g., 99900 for ₹999)
        duration_days: Plan duration in days (30 for monthly, 365 for yearly)
        features: List of features included in this plan
        currency: Currency code (default: INR)
        is_active: Whether this plan is available for purchase
        description: Optional detailed description of the plan
        discount_percentage: Optional discount percentage (0-100)
    
    Example:
        >>> plan = SubscriptionPlan(
        ...     plan_id="premium_monthly",
        ...     name="Premium Monthly",
        ...     price=99900,
        ...     duration_days=30,
        ...     features=[
        ...         "Unlimited practice tests",
        ...         "AI-powered analytics",
        ...         "Personalized study schedules",
        ...         "24/7 doubt support"
        ...     ],
        ...     currency="INR",
        ...     is_active=True,
        ...     description="Complete access to all features for 30 days"
        ... )
    """
    plan_id: str = Field(
        ...,
        min_length=1,
        description="Unique plan identifier"
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Display name of the plan"
    )
    price: int = Field(
        ...,
        ge=0,
        description="Price in paise (100 paise = 1 rupee)"
    )
    duration_days: int = Field(
        ...,
        gt=0,
        description="Plan duration in days"
    )
    features: List[str] = Field(
        ...,
        min_length=1,
        description="List of features included in this plan"
    )
    currency: Currency = Field(
        default=Currency.INR,
        description="Currency code (default: INR)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether this plan is available for purchase"
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of the plan"
    )
    discount_percentage: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Discount percentage (0-100)"
    )
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: int) -> int:
        """Validate that price is a non-negative integer."""
        if v < 0:
            raise ValueError(f"Price must be non-negative, got {v}")
        return v
    
    @field_validator('duration_days')
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validate that duration is a positive integer."""
        if v <= 0:
            raise ValueError(f"Duration must be positive, got {v}")
        return v
    
    @field_validator('features')
    @classmethod
    def validate_features(cls, v: List[str]) -> List[str]:
        """Validate that features list is not empty."""
        if not v or len(v) == 0:
            raise ValueError("Features list cannot be empty")
        return v
    
    def get_price_in_rupees(self) -> float:
        """Get price in rupees (convenience method)."""
        return self.price / 100.0
    
    def get_discounted_price(self) -> int:
        """Get price after discount in paise."""
        if self.discount_percentage:
            discount_amount = (self.price * self.discount_percentage) // 100
            return self.price - discount_amount
        return self.price
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "plan_id": "premium_monthly",
                "name": "Premium Monthly",
                "price": 99900,
                "duration_days": 30,
                "features": [
                    "Unlimited practice tests",
                    "AI-powered analytics",
                    "Personalized study schedules",
                    "24/7 doubt support",
                    "Video solutions"
                ],
                "currency": "INR",
                "is_active": True,
                "description": "Complete access to all premium features for 30 days",
                "discount_percentage": 10
            }
        }


# ==================== Order Request/Response Models ====================


class CreateOrderRequest(BaseModel):
    """
    Request to create a Razorpay order for subscription payment.
    
    This model is used when a parent wants to purchase a subscription plan.
    The order is created with Razorpay before redirecting to payment.
    
    Attributes:
        parent_id: Firebase user ID of the parent
        plan_id: Subscription plan identifier
        apply_discount: Whether to apply any available discounts
    
    Example:
        >>> request = CreateOrderRequest(
        ...     parent_id="parent_abc123",
        ...     plan_id="premium_monthly",
        ...     apply_discount=True
        ... )
    """
    parent_id: str = Field(
        ...,
        min_length=1,
        description="Firebase user ID of the parent"
    )
    plan_id: str = Field(
        ...,
        min_length=1,
        description="Subscription plan identifier"
    )
    apply_discount: bool = Field(
        default=False,
        description="Whether to apply any available discounts"
    )
    
    @field_validator('plan_id')
    @classmethod
    def validate_plan_id(cls, v: str) -> str:
        """Validate that plan_id follows naming convention."""
        # Valid plan IDs: premium_monthly, premium_yearly, basic_monthly, etc.
        valid_plans = [
            "premium_monthly",
            "premium_yearly",
            "basic_monthly",
            "basic_yearly"
        ]
        
        if v not in valid_plans:
            raise ValueError(
                f"Invalid plan_id '{v}'. Must be one of: {', '.join(valid_plans)}"
            )
        return v
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "parent_id": "parent_abc123def456",
                "plan_id": "premium_monthly",
                "apply_discount": False
            }
        }


class OrderResponse(BaseModel):
    """
    Razorpay order creation response.
    
    This model contains the order details returned by Razorpay after
    successfully creating an order. The order_id is used in the payment flow.
    
    Attributes:
        order_id: Razorpay order ID (e.g., "order_abc123xyz")
        amount: Order amount in paise
        currency: Currency code (default: INR)
        receipt: Unique receipt identifier
        created_at: Timestamp when order was created
        status: Order status (default: "created")
    
    Example:
        >>> response = OrderResponse(
        ...     order_id="order_LkjHGFDS1234",
        ...     amount=99900,
        ...     currency="INR",
        ...     receipt="receipt_parent_abc123_1234567890",
        ...     created_at=datetime.now(),
        ...     status="created"
        ... )
    """
    order_id: str = Field(
        ...,
        min_length=1,
        description="Razorpay order ID"
    )
    amount: int = Field(
        ...,
        gt=0,
        description="Order amount in paise"
    )
    currency: str = Field(
        default="INR",
        description="Currency code"
    )
    receipt: str = Field(
        ...,
        min_length=1,
        description="Unique receipt identifier"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when order was created"
    )
    status: str = Field(
        default="created",
        description="Order status"
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Validate that amount is positive."""
        if v <= 0:
            raise ValueError(f"Amount must be positive, got {v}")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency is a valid ISO code."""
        valid_currencies = ["INR", "USD", "EUR", "GBP"]
        if v not in valid_currencies:
            raise ValueError(
                f"Invalid currency '{v}'. Must be one of: {', '.join(valid_currencies)}"
            )
        return v
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "order_id": "order_LkjHGFDS1234567",
                "amount": 99900,
                "currency": "INR",
                "receipt": "receipt_parent_abc123_1705123456",
                "created_at": "2024-01-13T10:30:00Z",
                "status": "created"
            }
        }


# ==================== Payment Verification Model ====================


class VerifyPaymentRequest(BaseModel):
    """
    Payment signature verification request.
    
    This model is used to verify the authenticity of a payment using
    Razorpay's signature verification mechanism. All three fields are
    required for successful verification.
    
    Attributes:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID (received after payment)
        signature: Razorpay signature for verification
    
    Example:
        >>> request = VerifyPaymentRequest(
        ...     order_id="order_LkjHGFDS1234",
        ...     payment_id="pay_LkjHGFDS5678",
        ...     signature="9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
        ... )
    """
    order_id: str = Field(
        ...,
        min_length=1,
        description="Razorpay order ID"
    )
    payment_id: str = Field(
        ...,
        min_length=1,
        description="Razorpay payment ID"
    )
    signature: str = Field(
        ...,
        min_length=1,
        description="Razorpay signature for verification"
    )
    
    @field_validator('order_id', 'payment_id', 'signature')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that fields are not empty strings."""
        if not v or v.strip() == "":
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "order_id": "order_LkjHGFDS1234567",
                "payment_id": "pay_LkjHGFDS7654321",
                "signature": "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f"
            }
        }


# ==================== Subscription Details Model ====================


class SubscriptionDetails(BaseModel):
    """
    Active subscription information for a parent.
    
    This model stores complete subscription details including plan information,
    status, dates, and renewal settings.
    
    Attributes:
        subscription_id: Unique subscription identifier
        parent_id: Firebase user ID of the parent
        plan_id: Subscription plan identifier
        plan_name: Display name of the plan
        status: Subscription status (active, expired, cancelled, pending)
        start_date: Subscription start timestamp
        end_date: Subscription expiry timestamp
        auto_renew: Whether subscription auto-renews
        amount_paid: Amount paid in paise
        currency: Currency code
        payment_id: Razorpay payment ID (if payment completed)
        created_at: When subscription was created
        updated_at: Last update timestamp
    
    Example:
        >>> subscription = SubscriptionDetails(
        ...     subscription_id="sub_abc123",
        ...     parent_id="parent_123",
        ...     plan_id="premium_monthly",
        ...     plan_name="Premium Monthly",
        ...     status="active",
        ...     start_date=datetime.now(),
        ...     end_date=datetime.now() + timedelta(days=30),
        ...     auto_renew=True,
        ...     amount_paid=99900,
        ...     currency="INR",
        ...     payment_id="pay_xyz789"
        ... )
    """
    subscription_id: str = Field(
        ...,
        min_length=1,
        description="Unique subscription identifier"
    )
    parent_id: str = Field(
        ...,
        min_length=1,
        description="Firebase user ID of the parent"
    )
    plan_id: str = Field(
        ...,
        min_length=1,
        description="Subscription plan identifier"
    )
    plan_name: str = Field(
        ...,
        min_length=1,
        description="Display name of the plan"
    )
    status: SubscriptionStatus = Field(
        ...,
        description="Subscription status"
    )
    start_date: datetime = Field(
        ...,
        description="Subscription start timestamp"
    )
    end_date: datetime = Field(
        ...,
        description="Subscription expiry timestamp"
    )
    auto_renew: bool = Field(
        default=False,
        description="Whether subscription auto-renews"
    )
    amount_paid: int = Field(
        ...,
        gt=0,
        description="Amount paid in paise"
    )
    currency: Currency = Field(
        default=Currency.INR,
        description="Currency code"
    )
    payment_id: Optional[str] = Field(
        default=None,
        description="Razorpay payment ID (if payment completed)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When subscription was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )
    
    @field_validator('amount_paid')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Validate that amount is positive."""
        if v <= 0:
            raise ValueError(f"Amount must be positive, got {v}")
        return v
    
    @model_validator(mode='after')
    def validate_dates(self) -> SubscriptionDetails:
        """Validate that end_date is after start_date."""
        if self.end_date <= self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) must be after start_date ({self.start_date})"
            )
        return self
    
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.start_date <= datetime.utcnow() <= self.end_date
        )
    
    def days_remaining(self) -> int:
        """Calculate days remaining in subscription."""
        if self.status != SubscriptionStatus.ACTIVE:
            return 0
        remaining = (self.end_date - datetime.utcnow()).days
        return max(0, remaining)
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "subscription_id": "sub_abc123def456",
                "parent_id": "parent_abc123def456",
                "plan_id": "premium_monthly",
                "plan_name": "Premium Monthly",
                "status": "active",
                "start_date": "2024-01-15T10:30:00Z",
                "end_date": "2024-02-14T10:30:00Z",
                "auto_renew": True,
                "amount_paid": 99900,
                "currency": "INR",
                "payment_id": "pay_LkjHGFDS7654321",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


# ==================== Transaction Record Model ====================


class TransactionRecord(BaseModel):
    """
    Payment transaction details and history.
    
    This model stores complete transaction information for audit and
    reconciliation purposes.
    
    Attributes:
        transaction_id: Unique transaction identifier
        parent_id: Firebase user ID of the parent
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID (if payment completed)
        amount: Transaction amount in paise
        currency: Currency code
        status: Transaction status (pending, completed, failed, refunded)
        plan_id: Subscription plan identifier
        error_message: Error message if transaction failed
        created_at: When transaction was created
        completed_at: When transaction was completed/failed
    
    Example:
        >>> transaction = TransactionRecord(
        ...     transaction_id="txn_abc123",
        ...     parent_id="parent_123",
        ...     order_id="order_xyz789",
        ...     payment_id="pay_xyz789",
        ...     amount=99900,
        ...     currency="INR",
        ...     status="completed",
        ...     plan_id="premium_monthly",
        ...     created_at=datetime.now(),
        ...     completed_at=datetime.now()
        ... )
    """
    transaction_id: str = Field(
        ...,
        min_length=1,
        description="Unique transaction identifier"
    )
    parent_id: str = Field(
        ...,
        min_length=1,
        description="Firebase user ID of the parent"
    )
    order_id: str = Field(
        ...,
        min_length=1,
        description="Razorpay order ID"
    )
    payment_id: Optional[str] = Field(
        default=None,
        description="Razorpay payment ID (if payment completed)"
    )
    amount: int = Field(
        ...,
        gt=0,
        description="Transaction amount in paise"
    )
    currency: Currency = Field(
        default=Currency.INR,
        description="Currency code"
    )
    status: TransactionStatus = Field(
        ...,
        description="Transaction status"
    )
    plan_id: str = Field(
        ...,
        min_length=1,
        description="Subscription plan identifier"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if transaction failed"
    )
    created_at: datetime = Field(
        ...,
        description="When transaction was created"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When transaction was completed/failed"
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Validate that amount is positive."""
        if v <= 0:
            raise ValueError(f"Amount must be positive, got {v}")
        return v
    
    @model_validator(mode='after')
    def validate_completed_at(self) -> TransactionRecord:
        """Validate completed_at is set for completed/failed transactions."""
        if self.status in [TransactionStatus.COMPLETED, TransactionStatus.FAILED, TransactionStatus.REFUNDED]:
            if not self.completed_at:
                raise ValueError(
                    f"completed_at must be set for {self.status.value} transactions"
                )
        return self
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_abc123def456ghi789",
                "parent_id": "parent_abc123def456",
                "order_id": "order_LkjHGFDS1234567",
                "payment_id": "pay_LkjHGFDS7654321",
                "amount": 99900,
                "currency": "INR",
                "status": "completed",
                "plan_id": "premium_monthly",
                "error_message": None,
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:35:00Z"
            }
        }


# ==================== Subscription Status Response Model ====================


class SubscriptionStatusResponse(BaseModel):
    """
    Subscription status response for user queries.
    
    This model provides a simplified view of subscription status
    for display in the frontend/mobile app.
    
    Attributes:
        is_active: Whether subscription is currently active
        plan_name: Display name of the plan
        plan_id: Subscription plan identifier
        days_remaining: Days until subscription expires
        expires_at: Subscription expiry timestamp
        features: List of features included in the plan
        auto_renew: Whether subscription will auto-renew
        amount_paid: Amount paid in paise
    
    Example:
        >>> status = SubscriptionStatusResponse(
        ...     is_active=True,
        ...     plan_name="Premium Monthly",
        ...     plan_id="premium_monthly",
        ...     days_remaining=25,
        ...     expires_at=datetime.now() + timedelta(days=25),
        ...     features=["Unlimited tests", "AI analytics"],
        ...     auto_renew=True,
        ...     amount_paid=99900
        ... )
    """
    is_active: bool = Field(
        ...,
        description="Whether subscription is currently active"
    )
    plan_name: str = Field(
        ...,
        min_length=1,
        description="Display name of the plan"
    )
    plan_id: str = Field(
        ...,
        min_length=1,
        description="Subscription plan identifier"
    )
    days_remaining: int = Field(
        ...,
        ge=0,
        description="Days until subscription expires"
    )
    expires_at: datetime = Field(
        ...,
        description="Subscription expiry timestamp"
    )
    features: List[str] = Field(
        ...,
        min_length=1,
        description="List of features included in the plan"
    )
    auto_renew: bool = Field(
        default=False,
        description="Whether subscription will auto-renew"
    )
    amount_paid: Optional[int] = Field(
        default=None,
        gt=0,
        description="Amount paid in paise"
    )
    
    @field_validator('days_remaining')
    @classmethod
    def validate_days_remaining(cls, v: int) -> int:
        """Validate that days_remaining is non-negative."""
        if v < 0:
            raise ValueError(f"days_remaining must be non-negative, got {v}")
        return v
    
    @field_validator('features')
    @classmethod
    def validate_features(cls, v: List[str]) -> List[str]:
        """Validate that features list is not empty."""
        if not v or len(v) == 0:
            raise ValueError("Features list cannot be empty")
        return v
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "is_active": True,
                "plan_name": "Premium Monthly",
                "plan_id": "premium_monthly",
                "days_remaining": 25,
                "expires_at": "2024-02-14T10:30:00Z",
                "features": [
                    "Unlimited practice tests",
                    "AI-powered analytics",
                    "Personalized study schedules",
                    "24/7 doubt support",
                    "Video solutions"
                ],
                "auto_renew": True,
                "amount_paid": 99900
            }
        }
