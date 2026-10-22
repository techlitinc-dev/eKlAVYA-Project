"""
Razorpay Client Wrapper for Payment Operations - Mentor AI Platform.

This module provides a wrapper around the Razorpay Python SDK for handling
payment operations including order creation, payment verification, and
payment/order fetching.

Features:
- Order creation with validation
- Payment signature verification
- Payment details fetching
- Order details fetching
- Receipt ID generation
- Comprehensive error handling
- Detailed logging

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.razorpay_client import RazorpayClient
    >>> 
    >>> # Initialize client
    >>> client = RazorpayClient()
    >>> 
    >>> # Create order
    >>> order = client.create_order(
    ...     amount=99900,  # ₹999 in paise
    ...     currency="INR",
    ...     receipt="rcpt_20240115_103000_ABC12"
    ... )
    >>> print(order['id'])  # order_LkjHGFDS1234567
    >>> 
    >>> # Verify payment
    >>> is_valid = client.verify_payment_signature(
    ...     order_id="order_LkjHGFDS1234567",
    ...     payment_id="pay_LkjHGFDS7654321",
    ...     signature="9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
    ... )
    >>> print(is_valid)  # True
"""

import os
import logging
import secrets
from datetime import datetime
from typing import Dict, Any, Optional

import razorpay
from razorpay.errors import BadRequestError, ServerError, SignatureVerificationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class RazorpayClientError(Exception):
    """Base exception for Razorpay client errors."""
    pass


class RazorpayConfigurationError(RazorpayClientError):
    """Exception raised for configuration errors."""
    pass


class RazorpayOrderError(RazorpayClientError):
    """Exception raised for order creation errors."""
    pass


class RazorpayPaymentError(RazorpayClientError):
    """Exception raised for payment-related errors."""
    pass


class RazorpayVerificationError(RazorpayClientError):
    """Exception raised for signature verification errors."""
    pass


class RazorpayClient:
    """
    Razorpay client wrapper for payment operations.
    
    This class provides a high-level interface to the Razorpay SDK with
    comprehensive error handling, validation, and logging.
    
    Attributes:
        client: Razorpay client instance
        key_id: Razorpay API key ID
        key_secret: Razorpay API key secret (not exposed)
    
    Environment Variables:
        RAZORPAY_KEY_ID: Razorpay API key ID
        RAZORPAY_KEY_SECRET: Razorpay API key secret
    
    Example:
        >>> client = RazorpayClient()
        >>> order = client.create_order(amount=99900, currency="INR")
    """
    
    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None
    ):
        """
        Initialize Razorpay client with API credentials.
        
        Args:
            key_id: Razorpay API key ID (optional, defaults to env var)
            key_secret: Razorpay API key secret (optional, defaults to env var)
        
        Raises:
            RazorpayConfigurationError: If credentials are missing
        
        Example:
            >>> # Using environment variables
            >>> client = RazorpayClient()
            >>> 
            >>> # Using explicit credentials
            >>> client = RazorpayClient(
            ...     key_id="rzp_test_1234567890",
            ...     key_secret="secret_key_1234567890"
            ... )
        """
        # Get credentials from parameters or environment variables
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self._key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        
        # Validate credentials
        if not self.key_id:
            error_msg = (
                "RAZORPAY_KEY_ID is not set. "
                "Please set the RAZORPAY_KEY_ID environment variable or pass it as a parameter."
            )
            logger.error(error_msg)
            raise RazorpayConfigurationError(error_msg)
        
        if not self._key_secret:
            error_msg = (
                "RAZORPAY_KEY_SECRET is not set. "
                "Please set the RAZORPAY_KEY_SECRET environment variable or pass it as a parameter."
            )
            logger.error(error_msg)
            raise RazorpayConfigurationError(error_msg)
        
        # Initialize Razorpay client
        try:
            self.client = razorpay.Client(auth=(self.key_id, self._key_secret))
            logger.info("Razorpay client initialized successfully")
            logger.debug(f"Using key ID: {self.key_id[:10]}...")
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {e}")
            raise RazorpayConfigurationError(f"Failed to initialize Razorpay client: {e}")
    
    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order.
        
        This method creates a new order in Razorpay's system. The order must be
        created before initiating payment. All amounts must be in paise (smallest
        currency unit).
        
        Args:
            amount: Order amount in paise (e.g., 99900 for ₹999)
            currency: Currency code (default: INR)
            receipt: Unique receipt identifier (auto-generated if not provided)
            notes: Optional metadata dictionary for the order
        
        Returns:
            Order dictionary containing:
            - id: Razorpay order ID
            - entity: "order"
            - amount: Amount in paise
            - currency: Currency code
            - receipt: Receipt identifier
            - status: Order status
            - created_at: Unix timestamp
        
        Raises:
            RazorpayOrderError: If order creation fails
            ValueError: If validation fails
        
        Example:
            >>> order = client.create_order(
            ...     amount=99900,
            ...     currency="INR",
            ...     receipt="rcpt_20240115_103000_ABC12",
            ...     notes={"plan_id": "premium_monthly", "parent_id": "parent_123"}
            ... )
            >>> print(order['id'])
            'order_LkjHGFDS1234567'
        """
        logger.info(f"Creating Razorpay order: amount={amount}, currency={currency}")
        
        # Validate amount
        if not isinstance(amount, int):
            raise ValueError(f"Amount must be an integer (in paise), got {type(amount)}")
        
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        
        # Validate currency
        valid_currencies = ["INR", "USD", "EUR", "GBP"]
        if currency not in valid_currencies:
            raise ValueError(
                f"Invalid currency '{currency}'. Must be one of: {', '.join(valid_currencies)}"
            )
        
        # Generate receipt if not provided
        if not receipt:
            receipt = self.generate_receipt_id()
            logger.debug(f"Generated receipt ID: {receipt}")
        
        # Prepare order data
        order_data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt
        }
        
        # Add notes if provided
        if notes:
            order_data["notes"] = notes
        
        try:
            # Create order via Razorpay API
            logger.debug(f"Calling Razorpay API to create order with receipt: {receipt}")
            order = self.client.order.create(data=order_data)
            
            logger.info(
                f"Order created successfully: order_id={order['id']}, "
                f"amount={order['amount']}, receipt={order['receipt']}"
            )
            
            return order
            
        except BadRequestError as e:
            error_msg = f"Bad request while creating order: {str(e)}"
            logger.error(error_msg)
            raise RazorpayOrderError(error_msg)
        
        except ServerError as e:
            error_msg = f"Razorpay server error while creating order: {str(e)}"
            logger.error(error_msg)
            raise RazorpayOrderError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error while creating order: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            raise RazorpayOrderError(error_msg)
    
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature.
        
        This method verifies the authenticity of a payment using Razorpay's
        signature verification mechanism. This is crucial for ensuring payment
        integrity and preventing tampering.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID (received after payment)
            signature: Razorpay signature (received after payment)
        
        Returns:
            True if signature is valid, False otherwise
        
        Example:
            >>> is_valid = client.verify_payment_signature(
            ...     order_id="order_LkjHGFDS1234567",
            ...     payment_id="pay_LkjHGFDS7654321",
            ...     signature="9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
            ... )
            >>> if is_valid:
            ...     print("Payment verified successfully")
            ... else:
            ...     print("Payment verification failed")
        """
        logger.info(
            f"Verifying payment signature: order_id={order_id}, payment_id={payment_id}"
        )
        
        # Validate inputs
        if not order_id or not order_id.strip():
            raise ValueError("order_id cannot be empty")
        
        if not payment_id or not payment_id.strip():
            raise ValueError("payment_id cannot be empty")
        
        if not signature or not signature.strip():
            raise ValueError("signature cannot be empty")
        
        # Prepare verification parameters
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        try:
            # Verify signature using Razorpay utility
            self.client.utility.verify_payment_signature(params_dict)
            
            logger.info(
                f"Payment signature verified successfully: "
                f"order_id={order_id}, payment_id={payment_id}"
            )
            
            return True
            
        except SignatureVerificationError as e:
            logger.warning(
                f"Payment signature verification failed: "
                f"order_id={order_id}, payment_id={payment_id}, error={str(e)}"
            )
            return False
        
        except Exception as e:
            error_msg = f"Unexpected error during signature verification: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            # For unexpected errors, return False instead of raising
            # This is safer as it prevents valid payments from being rejected
            # due to transient errors
            return False
    
    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetch payment details from Razorpay.
        
        This method retrieves complete payment information including status,
        amount, payment method, and other metadata.
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            Payment dictionary containing:
            - id: Payment ID
            - entity: "payment"
            - amount: Amount in paise
            - currency: Currency code
            - status: Payment status (captured, authorized, failed, etc.)
            - order_id: Associated order ID
            - method: Payment method (card, netbanking, upi, etc.)
            - captured: Whether payment is captured
            - created_at: Unix timestamp
        
        Raises:
            RazorpayPaymentError: If payment fetch fails
        
        Example:
            >>> payment = client.fetch_payment("pay_LkjHGFDS7654321")
            >>> print(f"Status: {payment['status']}")
            >>> print(f"Amount: ₹{payment['amount']/100}")
            >>> print(f"Method: {payment['method']}")
        """
        logger.info(f"Fetching payment details: payment_id={payment_id}")
        
        # Validate input
        if not payment_id or not payment_id.strip():
            raise ValueError("payment_id cannot be empty")
        
        try:
            # Fetch payment via Razorpay API
            payment = self.client.payment.fetch(payment_id)
            
            logger.info(
                f"Payment fetched successfully: payment_id={payment_id}, "
                f"status={payment.get('status')}, amount={payment.get('amount')}"
            )
            
            return payment
            
        except BadRequestError as e:
            # Payment not found or invalid payment ID
            error_msg = f"Payment not found or invalid: {payment_id}, error={str(e)}"
            logger.error(error_msg)
            raise RazorpayPaymentError(error_msg)
        
        except ServerError as e:
            error_msg = f"Razorpay server error while fetching payment: {str(e)}"
            logger.error(error_msg)
            raise RazorpayPaymentError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error while fetching payment: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            raise RazorpayPaymentError(error_msg)
    
    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch order details from Razorpay.
        
        This method retrieves complete order information including status,
        amount, receipt, and payment status.
        
        Args:
            order_id: Razorpay order ID
        
        Returns:
            Order dictionary containing:
            - id: Order ID
            - entity: "order"
            - amount: Amount in paise
            - currency: Currency code
            - receipt: Receipt identifier
            - status: Order status (created, attempted, paid)
            - attempts: Number of payment attempts
            - created_at: Unix timestamp
        
        Raises:
            RazorpayOrderError: If order fetch fails
        
        Example:
            >>> order = client.fetch_order("order_LkjHGFDS1234567")
            >>> print(f"Status: {order['status']}")
            >>> print(f"Amount: ₹{order['amount']/100}")
            >>> print(f"Attempts: {order['attempts']}")
        """
        logger.info(f"Fetching order details: order_id={order_id}")
        
        # Validate input
        if not order_id or not order_id.strip():
            raise ValueError("order_id cannot be empty")
        
        try:
            # Fetch order via Razorpay API
            order = self.client.order.fetch(order_id)
            
            logger.info(
                f"Order fetched successfully: order_id={order_id}, "
                f"status={order.get('status')}, amount={order.get('amount')}"
            )
            
            return order
            
        except BadRequestError as e:
            # Order not found or invalid order ID
            error_msg = f"Order not found or invalid: {order_id}, error={str(e)}"
            logger.error(error_msg)
            raise RazorpayOrderError(error_msg)
        
        except ServerError as e:
            error_msg = f"Razorpay server error while fetching order: {str(e)}"
            logger.error(error_msg)
            raise RazorpayOrderError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error while fetching order: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            raise RazorpayOrderError(error_msg)
    
    @staticmethod
    def generate_receipt_id() -> str:
        """
        Generate a unique receipt ID.
        
        The receipt ID format is: rcpt_YYYYMMDD_HHMMSS_XXXXX
        where XXXXX is a random 5-character alphanumeric string.
        
        Returns:
            Unique receipt identifier string
        
        Example:
            >>> receipt = RazorpayClient.generate_receipt_id()
            >>> print(receipt)
            'rcpt_20240115_103000_A7K9M'
        """
        # Get current timestamp
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        
        # Generate random alphanumeric string (5 characters)
        random_str = secrets.token_urlsafe(4)[:5].upper()
        
        # Combine into receipt ID
        receipt_id = f"rcpt_{date_str}_{time_str}_{random_str}"
        
        logger.debug(f"Generated receipt ID: {receipt_id}")
        
        return receipt_id
