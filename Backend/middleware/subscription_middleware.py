"""
Subscription Middleware for Mentor AI Platform.

This module provides FastAPI dependencies for premium subscription access control
and feature gating based on subscription plans.

Dependencies:
- require_premium_subscription: Require active premium subscription
- check_feature_access: Check if user's plan includes specific feature
- get_subscription_or_free: Get subscription status (always succeeds)

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from fastapi import APIRouter, Depends
    >>> from middleware.subscription_middleware import require_premium_subscription
    >>> 
    >>> router = APIRouter()
    >>> 
    >>> @router.get("/premium-feature")
    >>> async def premium_feature(
    ...     current_user: str = Depends(require_premium_subscription)
    ... ):
    ...     # Only premium users can access this
    ...     return {"message": "Welcome premium user"}
    >>> 
    >>> @router.get("/flexible-feature")
    >>> async def flexible_feature(
    ...     subscription: SubscriptionStatusResponse = Depends(get_subscription_or_free)
    ... ):
    ...     # Works for all users but behaves differently
    ...     if subscription.is_active and subscription.plan_id != "free":
    ...         return {"message": "Premium content"}
    ...     return {"message": "Free content"}
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status

from middleware.auth_middleware import get_current_user
from models.payment_models import SubscriptionStatusResponse
from services.subscription_service import SubscriptionService

# Configure logging
logger = logging.getLogger(__name__)

# Service instance (singleton pattern)
_subscription_service: Optional[SubscriptionService] = None


def get_subscription_service() -> SubscriptionService:
    """
    Get or create singleton SubscriptionService instance.
    
    Returns:
        SubscriptionService: Singleton instance of subscription service
    """
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service


async def require_premium_subscription(
    current_user: str = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> str:
    """
    Dependency to require active premium subscription.
    
    This dependency checks if the authenticated user has an active premium
    subscription. If not, it raises a 403 Forbidden error with upgrade information.
    
    Args:
        current_user: Authenticated parent ID from JWT token
        subscription_service: Injected SubscriptionService instance
    
    Returns:
        str: Parent ID if premium subscription is active
    
    Raises:
        HTTPException: 401 if not authenticated (from get_current_user)
        HTTPException: 403 if premium subscription is not active
    
    Example:
        >>> @router.get("/premium-analytics")
        >>> async def get_premium_analytics(
        ...     current_user: str = Depends(require_premium_subscription)
        ... ):
        ...     # Only premium users can access this endpoint
        ...     return {"analytics": "advanced"}
    """
    try:
        logger.debug(f"Checking premium subscription for parent: {current_user}")
        
        # Check if user has active premium subscription
        is_premium = subscription_service.is_premium_active(current_user)
        
        if not is_premium:
            logger.warning(
                f"Premium subscription required but not active for parent: {current_user}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Premium subscription required",
                    "message": "Premium subscription required. Please upgrade to access this feature.",
                    "upgrade_url": "/api/payment/plans",
                    "user_id": current_user
                }
            )
        
        logger.debug(f"Premium subscription verified for parent: {current_user}")
        return current_user
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle unexpected errors - safe default: deny access
        logger.error(f"Error checking premium subscription for {current_user}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Subscription verification failed",
                "message": "Unable to verify subscription status. Please try again later.",
                "user_id": current_user
            }
        )


async def check_feature_access(
    feature_name: str,
    current_user: str = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> bool:
    """
    Check if user's subscription plan includes a specific feature.
    
    This dependency performs granular feature-level access control by checking
    if the user's current subscription plan includes the specified feature.
    
    Args:
        feature_name: Name of the feature to check (e.g., "Unlimited practice questions")
        current_user: Authenticated parent ID from JWT token
        subscription_service: Injected SubscriptionService instance
    
    Returns:
        bool: True if user's plan includes the feature, False otherwise
    
    Raises:
        HTTPException: 401 if not authenticated (from get_current_user)
    
    Example:
        >>> @router.get("/advanced-analytics")
        >>> async def get_advanced_analytics(
        ...     current_user: str = Depends(get_current_user),
        ...     subscription_service: SubscriptionService = Depends(get_subscription_service)
        ... ):
        ...     has_access = await check_feature_access(
        ...         "Advanced AI analytics",
        ...         current_user,
        ...         subscription_service
        ...     )
        ...     if not has_access:
        ...         raise HTTPException(403, detail="This feature requires premium subscription")
        ...     return {"analytics": "advanced"}
    """
    try:
        logger.debug(
            f"Checking feature access '{feature_name}' for parent: {current_user}"
        )
        
        # Get subscription status
        subscription_status = subscription_service.check_subscription_status(current_user)
        
        # If no active subscription, no features available (except free plan features)
        if not subscription_status.is_active:
            logger.debug(f"No active subscription for parent: {current_user}")
            return False
        
        # Get current plan
        try:
            plan = subscription_service.get_plan_by_id(subscription_status.plan_id)
        except Exception as e:
            logger.error(f"Error getting plan {subscription_status.plan_id}: {e}")
            return False
        
        # Check if feature is in plan's features list
        has_feature = feature_name in plan.features
        
        logger.debug(
            f"Feature access '{feature_name}' for parent {current_user}: {has_feature}"
        )
        
        return has_feature
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle unexpected errors - safe default: deny access
        logger.error(f"Error checking feature access for {current_user}: {e}")
        logger.exception("Full traceback:")
        return False


async def get_subscription_or_free(
    current_user: str = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> SubscriptionStatusResponse:
    """
    Get subscription status (always succeeds, defaults to free plan).
    
    This dependency is used for endpoints that work for all users but behave
    differently based on subscription status. It never raises an exception,
    always returning at least the free plan status.
    
    Args:
        current_user: Authenticated parent ID from JWT token
        subscription_service: Injected SubscriptionService instance
    
    Returns:
        SubscriptionStatusResponse: Current subscription status or free plan
    
    Raises:
        HTTPException: 401 if not authenticated (from get_current_user)
    
    Example:
        >>> @router.get("/practice-questions")
        >>> async def get_practice_questions(
        ...     subscription: SubscriptionStatusResponse = Depends(get_subscription_or_free)
        ... ):
        ...     # Free users get 50 questions, premium users get unlimited
        ...     if subscription.plan_id == "free":
        ...         return {"questions": limited_questions[:50]}
        ...     return {"questions": all_questions}
    """
    try:
        logger.debug(f"Getting subscription status for parent: {current_user}")
        
        # Get subscription status (returns free plan if no subscription exists)
        subscription_status = subscription_service.check_subscription_status(current_user)
        
        logger.debug(
            f"Subscription status for parent {current_user}: "
            f"Plan {subscription_status.plan_id}, Active {subscription_status.is_active}"
        )
        
        return subscription_status
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle unexpected errors - return free plan status as safe default
        logger.error(f"Error getting subscription status for {current_user}: {e}")
        logger.exception("Full traceback:")
        
        # Return free plan status as fallback
        try:
            free_plan = subscription_service.get_plan_by_id("free")
            logger.info(f"Returning free plan as fallback for parent: {current_user}")
            return SubscriptionStatusResponse(
                is_active=True,
                plan_name=free_plan.name,
                plan_id=free_plan.plan_id,
                status="active",
                days_remaining=365,  # Free plan duration
                end_date=None,
                auto_renew=False
            )
        except Exception as fallback_error:
            logger.error(f"Error creating fallback free plan: {fallback_error}")
            # Last resort: return minimal free plan response
            return SubscriptionStatusResponse(
                is_active=True,
                plan_name="Free Plan",
                plan_id="free",
                status="active",
                days_remaining=365,
                end_date=None,
                auto_renew=False
            )


async def require_feature_access(
    feature_name: str,
    current_user: str = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> str:
    """
    Dependency to require access to a specific feature.
    
    This dependency checks if the user's subscription plan includes a specific
    feature. If not, it raises a 403 Forbidden error with upgrade information.
    
    Args:
        feature_name: Name of the feature to require
        current_user: Authenticated parent ID from JWT token
        subscription_service: Injected SubscriptionService instance
    
    Returns:
        str: Parent ID if feature access is granted
    
    Raises:
        HTTPException: 401 if not authenticated (from get_current_user)
        HTTPException: 403 if feature access is denied
    
    Example:
        >>> from functools import partial
        >>> 
        >>> # Create a dependency for specific feature
        >>> require_unlimited_tests = partial(
        ...     require_feature_access,
        ...     feature_name="Unlimited diagnostic tests"
        ... )
        >>> 
        >>> @router.post("/generate-test")
        >>> async def generate_test(
        ...     current_user: str = Depends(require_unlimited_tests)
        ... ):
        ...     return {"test": "generated"}
    """
    try:
        logger.debug(
            f"Checking required feature access '{feature_name}' for parent: {current_user}"
        )
        
        # Check if user has access to the feature
        has_access = await check_feature_access(
            feature_name=feature_name,
            current_user=current_user,
            subscription_service=subscription_service
        )
        
        if not has_access:
            logger.warning(
                f"Feature access denied for '{feature_name}' to parent: {current_user}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Feature access denied",
                    "message": f"Your subscription plan does not include '{feature_name}'. Please upgrade to access this feature.",
                    "feature": feature_name,
                    "upgrade_url": "/api/payment/plans",
                    "user_id": current_user
                }
            )
        
        logger.debug(
            f"Feature access granted for '{feature_name}' to parent: {current_user}"
        )
        return current_user
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle unexpected errors - safe default: deny access
        logger.error(
            f"Error checking required feature access '{feature_name}' "
            f"for {current_user}: {e}"
        )
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Feature access verification failed",
                "message": "Unable to verify feature access. Please try again later.",
                "feature": feature_name,
                "user_id": current_user
            }
        )


# Helper function to create feature-specific dependencies
def create_feature_dependency(feature_name: str):
    """
    Create a dependency function for a specific feature.
    
    This is a helper function to create reusable feature-specific dependencies
    that can be used across multiple endpoints.
    
    Args:
        feature_name: Name of the feature to protect
    
    Returns:
        Callable: Dependency function that requires the specified feature
    
    Example:
        >>> # Create feature-specific dependencies
        >>> require_unlimited_tests = create_feature_dependency("Unlimited diagnostic tests")
        >>> require_advanced_analytics = create_feature_dependency("Advanced AI analytics")
        >>> 
        >>> @router.get("/analytics")
        >>> async def get_analytics(
        ...     current_user: str = Depends(require_advanced_analytics)
        ... ):
        ...     return {"analytics": "advanced"}
    """
    async def feature_dependency(
        current_user: str = Depends(get_current_user),
        subscription_service: SubscriptionService = Depends(get_subscription_service)
    ) -> str:
        return await require_feature_access(
            feature_name=feature_name,
            current_user=current_user,
            subscription_service=subscription_service
        )
    
    # Set a descriptive name for better debugging
    feature_dependency.__name__ = f"require_{feature_name.lower().replace(' ', '_')}"
    
    return feature_dependency


# Pre-defined feature dependencies for common features
require_unlimited_tests = create_feature_dependency("Unlimited diagnostic tests")
require_advanced_analytics = create_feature_dependency("Advanced AI analytics")
require_unlimited_questions = create_feature_dependency("Unlimited practice questions")
require_personalized_schedules = create_feature_dependency("Personalized study schedules")
require_priority_support = create_feature_dependency("Priority support")
