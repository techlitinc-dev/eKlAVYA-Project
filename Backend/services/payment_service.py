"""
Payment Orchestration Service for Mentor AI Platform.

This module coordinates the complete payment flow including order creation,
payment verification, subscription activation, and transaction management.

Features:
- Create Razorpay payment orders
- Verify payment signatures
- Activate subscriptions after successful payment
- Record and track transactions
- Handle payment failures
- Comprehensive error handling and logging

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.payment_service import PaymentService
    >>> 
    >>> # Initialize service
    >>> service = PaymentService()
    >>> 
    >>> # Create payment order
    >>> order = service.create_payment_order(
    ...     parent_id="parent_abc123",
    ...     plan_id="premium_monthly"
    ... )
    >>> print(f"Order ID: {order.order_id}, Amount: ₹{order.amount/100}")
    >>> 
    >>> # After payment, verify and activate
    >>> subscription = service.verify_and_activate(
    ...     order_id="order_xyz789",
    ...     payment_id="pay_xyz789",
    ...     signature="signature_hash"
    ... )
    >>> print(f"Subscription activated: {subscription.plan_name}")
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from google.cloud import firestore

from services.razorpay_client import (
    RazorpayClient,
    RazorpayOrderError,
    RazorpayPaymentError
)
from services.subscription_service import (
    SubscriptionService,
    PlanNotFoundError,
    SubscriptionServiceError
)
from models.payment_models import (
    OrderResponse,
    SubscriptionDetails,
    TransactionRecord,
    TransactionStatus,
    Currency
)
from utils.firebase_config import get_firestore_client

# Configure logging
logger = logging.getLogger(__name__)

# Firestore collections
TRANSACTIONS_COLLECTION = "transactions"
PARENTS_COLLECTION = "parents"


class PaymentServiceError(Exception):
    """Base exception for payment service errors."""
    pass


class ParentNotFoundError(PaymentServiceError):
    """Exception raised when parent is not found."""
    pass


class PaymentVerificationError(PaymentServiceError):
    """Exception raised when payment verification fails."""
    pass


class PaymentService:
    """
    Payment orchestration service for managing the complete payment flow.
    
    This service coordinates Razorpay operations, subscription activation,
    and transaction management.
    
    Attributes:
        razorpay_client: Razorpay client for payment operations
        subscription_service: Subscription service for activation
    
    Example:
        >>> service = PaymentService()
        >>> order = service.create_payment_order("parent_123", "premium_monthly")
    """
    
    def __init__(
        self,
        razorpay_client: Optional[RazorpayClient] = None,
        subscription_service: Optional[SubscriptionService] = None
    ):
        """
        Initialize payment service with dependencies.
        
        Args:
            razorpay_client: RazorpayClient instance (optional, created if not provided)
            subscription_service: SubscriptionService instance (optional, created if not provided)
        
        Example:
            >>> # Using default clients
            >>> service = PaymentService()
            >>> 
            >>> # Using custom clients
            >>> razorpay = RazorpayClient(key_id="...", key_secret="...")
            >>> subscriptions = SubscriptionService()
            >>> service = PaymentService(razorpay, subscriptions)
        """
        logger.info("Initializing PaymentService")
        
        # Initialize Razorpay client
        if razorpay_client:
            self.razorpay_client = razorpay_client
            logger.info("Using provided RazorpayClient")
        else:
            # For testing, create client with test credentials
            try:
                self.razorpay_client = RazorpayClient(
                    key_id="rzp_test_1234567890123456",
                    key_secret="rzp_test_1234567890123456"
                )
                logger.info("Created test RazorpayClient")
            except Exception as e:
                logger.warning(f"Failed to create RazorpayClient: {e}")
                self.razorpay_client = RazorpayClient()
                logger.info("Created default RazorpayClient")
        
        # Initialize subscription service
        if subscription_service:
            self.subscription_service = subscription_service
            logger.info("Using provided SubscriptionService")
        else:
            self.subscription_service = SubscriptionService()
            logger.info("Created new SubscriptionService")
        
        logger.info("PaymentService initialized successfully")
    
    def create_payment_order(
        self,
        parent_id: str,
        plan_id: str
    ) -> OrderResponse:
        """
        Create a Razorpay payment order for a subscription plan.
        
        This method validates the parent and plan, creates a Razorpay order,
        and records the transaction in Firestore.
        
        Args:
            parent_id: Firebase user ID of the parent
            plan_id: Subscription plan identifier
        
        Returns:
            OrderResponse with order details
        
        Raises:
            ParentNotFoundError: If parent doesn't exist
            PlanNotFoundError: If plan doesn't exist
            PaymentServiceError: If order creation fails
        
        Example:
            >>> order = service.create_payment_order(
            ...     parent_id="parent_abc123",
            ...     plan_id="premium_monthly"
            ... )
            >>> print(f"Pay ₹{order.amount/100} for order {order.order_id}")
        """
        logger.info(
            f"Creating payment order: parent_id={parent_id}, plan_id={plan_id}"
        )
        
        try:
            # Step 1: Validate parent exists
            if not self._validate_parent_exists(parent_id):
                error_msg = f"Parent not found: {parent_id}"
                logger.error(error_msg)
                raise ParentNotFoundError(error_msg)
            
            # Step 2: Get plan details
            plan = self.subscription_service.get_plan_by_id(plan_id)
            
            # Step 3: Validate plan is active
            if not plan.is_active:
                error_msg = f"Plan is not active: {plan_id}"
                logger.error(error_msg)
                raise PaymentServiceError(error_msg)
            
            # Step 4: Get final price (with discount if applicable)
            amount = plan.get_discounted_price() if plan.discount_percentage else plan.price
            
            # Step 5: Generate unique receipt ID
            receipt_id = self.razorpay_client.generate_receipt_id()
            
            # Step 6: Create Razorpay order with metadata
            order_notes = {
                "parent_id": parent_id,
                "plan_id": plan_id,
                "plan_name": plan.name
            }
            
            razorpay_order = self.razorpay_client.create_order(
                amount=amount,
                currency=plan.currency.value,
                receipt=receipt_id,
                notes=order_notes
            )
            
            logger.info(
                f"Razorpay order created: {razorpay_order['id']}, "
                f"amount={razorpay_order['amount']}"
            )
            
            # Step 7: Record transaction in Firestore
            transaction_id = self.record_transaction(
                parent_id=parent_id,
                order_id=razorpay_order['id'],
                amount=razorpay_order['amount'],
                currency=razorpay_order['currency'],
                status=TransactionStatus.PENDING,
                plan_id=plan_id
            )
            
            logger.info(f"Transaction recorded: {transaction_id}")
            
            # Step 8: Create and return OrderResponse
            order_response = OrderResponse(
                order_id=razorpay_order['id'],
                amount=razorpay_order['amount'],
                currency=razorpay_order['currency'],
                receipt=razorpay_order['receipt'],
                created_at=datetime.fromtimestamp(razorpay_order['created_at']),
                status=razorpay_order['status']
            )
            
            logger.info(
                f"Payment order created successfully: {order_response.order_id}"
            )
            
            return order_response
            
        except ParentNotFoundError:
            raise
        except PlanNotFoundError:
            raise
        except RazorpayOrderError as e:
            error_msg = f"Razorpay order creation failed: {e}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg)
        except Exception as e:
            error_msg = f"Failed to create payment order: {e}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            raise PaymentServiceError(error_msg)
    
    def verify_and_activate(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> SubscriptionDetails:
        """
        Verify payment signature and activate subscription.
        
        This method verifies the Razorpay payment signature, fetches order details,
        activates the subscription, and updates the transaction status.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Razorpay payment signature
        
        Returns:
            SubscriptionDetails for the activated subscription
        
        Raises:
            PaymentVerificationError: If signature verification fails
            PaymentServiceError: If activation fails
        
        Example:
            >>> subscription = service.verify_and_activate(
            ...     order_id="order_LkjHGFDS1234567",
            ...     payment_id="pay_LkjHGFDS7654321",
            ...     signature="9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
            ... )
            >>> print(f"Activated: {subscription.plan_name}")
        """
        logger.info(
            f"Verifying payment and activating subscription: "
            f"order_id={order_id}, payment_id={payment_id}"
        )
        
        try:
            # Step 1: Verify payment signature
            is_valid = self.razorpay_client.verify_payment_signature(
                order_id=order_id,
                payment_id=payment_id,
                signature=signature
            )
            
            if not is_valid:
                # Log security incident
                error_msg = (
                    f"Payment signature verification failed! "
                    f"order_id={order_id}, payment_id={payment_id}"
                )
                logger.error(f"SECURITY INCIDENT: {error_msg}")
                
                # Update transaction as failed
                self.handle_payment_failure(
                    order_id=order_id,
                    reason="Invalid payment signature"
                )
                
                raise PaymentVerificationError(error_msg)
            
            logger.info("Payment signature verified successfully")
            
            # Step 2: Fetch order details from Razorpay
            order = self.razorpay_client.fetch_order(order_id)
            
            # Step 3: Extract parent_id and plan_id from order notes
            notes = order.get('notes', {})
            parent_id = notes.get('parent_id')
            plan_id = notes.get('plan_id')
            
            if not parent_id or not plan_id:
                error_msg = (
                    f"Missing parent_id or plan_id in order notes: "
                    f"order_id={order_id}"
                )
                logger.error(error_msg)
                raise PaymentServiceError(error_msg)
            
            logger.info(
                f"Order details retrieved: parent_id={parent_id}, plan_id={plan_id}"
            )
            
            # Step 4: Activate subscription
            subscription = self.subscription_service.activate_subscription(
                parent_id=parent_id,
                plan_id=plan_id,
                payment_id=payment_id,
                order_id=order_id
            )
            
            logger.info(
                f"Subscription activated: {subscription.subscription_id}, "
                f"expires: {subscription.end_date.isoformat()}"
            )
            
            # Step 5: Update transaction status to completed
            self._update_transaction_status(
                order_id=order_id,
                payment_id=payment_id,
                status=TransactionStatus.COMPLETED
            )
            
            logger.info(
                f"Payment verified and subscription activated successfully: "
                f"{subscription.subscription_id}"
            )
            
            return subscription
            
        except PaymentVerificationError:
            raise
        except RazorpayPaymentError as e:
            error_msg = f"Failed to fetch order details: {e}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg)
        except SubscriptionServiceError as e:
            error_msg = f"Failed to activate subscription: {e}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg)
        except Exception as e:
            error_msg = f"Failed to verify and activate: {e}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            raise PaymentServiceError(error_msg)
    
    def record_transaction(
        self,
        parent_id: str,
        order_id: str,
        amount: int,
        currency: str,
        status: TransactionStatus,
        plan_id: str,
        payment_id: Optional[str] = None
    ) -> str:
        """
        Record a transaction in Firestore.
        
        Args:
            parent_id: Firebase user ID of the parent
            order_id: Razorpay order ID
            amount: Transaction amount in paise
            currency: Currency code
            status: Transaction status
            plan_id: Subscription plan identifier
            payment_id: Razorpay payment ID (optional)
        
        Returns:
            Transaction ID (Firestore document ID)
        
        Raises:
            PaymentServiceError: If recording fails
        
        Example:
            >>> txn_id = service.record_transaction(
            ...     parent_id="parent_abc123",
            ...     order_id="order_xyz789",
            ...     amount=99900,
            ...     currency="INR",
            ...     status=TransactionStatus.PENDING,
            ...     plan_id="premium_monthly"
            ... )
        """
        logger.info(
            f"Recording transaction: order_id={order_id}, "
            f"amount={amount}, status={status.value}"
        )
        
        try:
            # Generate transaction ID
            transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
            
            # Get current timestamp
            created_at = datetime.utcnow()
            
            # Determine completed_at
            completed_at = created_at if status in [
                TransactionStatus.COMPLETED,
                TransactionStatus.FAILED,
                TransactionStatus.REFUNDED
            ] else None
            
            # Create transaction record
            transaction = TransactionRecord(
                transaction_id=transaction_id,
                parent_id=parent_id,
                order_id=order_id,
                payment_id=payment_id,
                amount=amount,
                currency=Currency(currency),
                status=status,
                plan_id=plan_id,
                error_message=None,
                created_at=created_at,
                completed_at=completed_at
            )
            
            # Save to Firestore
            db = get_firestore_client()
            doc_ref = db.collection(TRANSACTIONS_COLLECTION).document(transaction_id)
            transaction_dict = transaction.model_dump(mode='json')
            doc_ref.set(transaction_dict)
            
            logger.info(f"Transaction recorded successfully: {transaction_id}")
            
            return transaction_id
            
        except Exception as e:
            error_msg = f"Failed to record transaction: {e}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            raise PaymentServiceError(error_msg)
    
    def get_transaction_history(
        self,
        parent_id: str,
        limit: Optional[int] = None
    ) -> List[TransactionRecord]:
        """
        Get transaction history for a parent.
        
        Args:
            parent_id: Firebase user ID of the parent
            limit: Maximum number of transactions to return (None for all)
        
        Returns:
            List of TransactionRecord objects ordered by created_at descending
        
        Example:
            >>> history = service.get_transaction_history("parent_abc123", limit=10)
            >>> for txn in history:
            ...     print(f"{txn.order_id}: {txn.status.value}")
        """
        logger.info(f"Getting transaction history: parent_id={parent_id}, limit={limit}")
        
        try:
            db = get_firestore_client()
            
            # Query transactions collection
            query = (
                db.collection(TRANSACTIONS_COLLECTION)
                .where(filter=firestore.FieldFilter("parent_id", "==", parent_id))
                .order_by('created_at', direction=firestore.Query.DESCENDING)
            )
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            
            # Convert to TransactionRecord objects
            transactions = []
            for doc in docs:
                try:
                    txn_data = doc.to_dict()
                    transaction = TransactionRecord(**txn_data)
                    transactions.append(transaction)
                except Exception as e:
                    logger.warning(
                        f"Skipping invalid transaction record: {doc.id}, error: {e}"
                    )
            
            logger.info(f"Found {len(transactions)} transactions")
            
            return transactions
            
        except Exception as e:
            error_msg = f"Failed to get transaction history: {e}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            raise PaymentServiceError(error_msg)
    
    def handle_payment_failure(
        self,
        order_id: str,
        reason: str
    ) -> None:
        """
        Handle payment failure.
        
        Updates transaction status to failed and logs the failure reason.
        
        Args:
            order_id: Razorpay order ID
            reason: Failure reason
        
        Example:
            >>> service.handle_payment_failure(
            ...     order_id="order_xyz789",
            ...     reason="Payment declined by bank"
            ... )
        """
        logger.warning(f"Handling payment failure: order_id={order_id}, reason={reason}")
        
        try:
            # Update transaction status
            self._update_transaction_status(
                order_id=order_id,
                payment_id=None,
                status=TransactionStatus.FAILED,
                error_message=reason
            )
            
            logger.info(f"Payment failure recorded for order: {order_id}")
            
            # TODO: Send notification to parent (email/SMS)
            # This would be implemented in a notification service
            
        except Exception as e:
            logger.error(f"Failed to handle payment failure: {e}")
            # Don't raise - this is a background operation
    
    def _validate_parent_exists(self, parent_id: str) -> bool:
        """
        Validate that parent exists in Firestore.
        
        Args:
            parent_id: Firebase user ID of the parent
        
        Returns:
            True if parent exists, False otherwise
        """
        logger.debug(f"Validating parent exists: {parent_id}")
        
        try:
            db = get_firestore_client()
            doc_ref = db.collection(PARENTS_COLLECTION).document(parent_id)
            doc = doc_ref.get()
            
            exists = doc.exists
            logger.debug(f"Parent exists: {exists}")
            
            return exists
            
        except Exception as e:
            logger.error(f"Error validating parent existence: {e}")
            # Return False on error (safer to deny)
            return False
    
    def _update_transaction_status(
        self,
        order_id: str,
        payment_id: Optional[str],
        status: TransactionStatus,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update transaction status in Firestore.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID (optional)
            status: New transaction status
            error_message: Error message for failed transactions (optional)
        """
        logger.debug(f"Updating transaction status: order_id={order_id}, status={status.value}")
        
        try:
            db = get_firestore_client()
            
            # Query for transaction by order_id
            query = (
                db.collection(TRANSACTIONS_COLLECTION)
                .where(filter=firestore.FieldFilter("order_id", "==", order_id))
                .limit(1)
            )
            
            docs = list(query.stream())
            
            if not docs:
                logger.warning(f"Transaction not found for order: {order_id}")
                return
            
            # Update transaction
            doc_ref = docs[0].reference
            update_data = {
                'status': status.value,
                'updated_at': datetime.utcnow()
            }
            
            if payment_id:
                update_data['payment_id'] = payment_id
            
            if error_message:
                update_data['error_message'] = error_message
            
            # Set completed_at for terminal statuses
            if status in [TransactionStatus.COMPLETED, TransactionStatus.FAILED, TransactionStatus.REFUNDED]:
                update_data['completed_at'] = datetime.utcnow()
            
            doc_ref.update(update_data)
            
            logger.debug(f"Transaction status updated to: {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update transaction status: {e}")
            # Don't raise - this is a background update
