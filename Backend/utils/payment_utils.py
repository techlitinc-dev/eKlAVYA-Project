"""
Payment Utility Functions for Mentor AI Platform.

This module provides utility functions for payment processing, currency conversion,
formatting, and validation.

Functions:
- rupees_to_paise: Convert rupees to paise
- paise_to_rupees: Convert paise to rupees
- generate_receipt_id: Generate unique receipt ID
- validate_amount: Validate payment amount
- format_currency: Format amount for display
- calculate_discount: Calculate discount percentage
- validate_signature_format: Validate payment signature format

Author: Mentor AI Team
Version: 1.0.0
"""

import secrets
from datetime import datetime
from typing import Optional


def rupees_to_paise(rupees: float) -> int:
    """
    Convert rupees to paise.
    
    Razorpay requires amounts in the smallest currency unit (paise for INR).
    This function converts rupees (which may have decimal places) to paise
    (integer value).
    
    Args:
        rupees: Amount in rupees (can have decimal places)
    
    Returns:
        Amount in paise (integer)
    
    Example:
        >>> rupees_to_paise(999.50)
        99950
        >>> rupees_to_paise(999.0)
        99900
        >>> rupees_to_paise(0.50)
        50
    """
    # Multiply by 100 and round to handle floating point precision
    paise = round(rupees * 100)
    return int(paise)


def paise_to_rupees(paise: int) -> float:
    """
    Convert paise to rupees.
    
    This function converts paise (integer) to rupees (float) with proper
    decimal formatting.
    
    Args:
        paise: Amount in paise (integer)
    
    Returns:
        Amount in rupees (float, 2 decimal places)
    
    Example:
        >>> paise_to_rupees(99900)
        999.0
        >>> paise_to_rupees(99950)
        999.5
        >>> paise_to_rupees(50)
        0.5
    """
    # Divide by 100 and round to 2 decimal places
    rupees = paise / 100.0
    return round(rupees, 2)


def generate_receipt_id() -> str:
    """
    Generate a unique receipt ID.
    
    The receipt ID format is: rcpt_YYYYMMDD_HHMMSS_XXXXX
    where XXXXX is a random 5-character alphanumeric string.
    
    Returns:
        Unique receipt identifier string
    
    Example:
        >>> receipt = generate_receipt_id()
        >>> print(receipt)
        'rcpt_20240115_103000_A7K9M'
        >>> len(receipt.split('_'))
        4
    """
    # Get current timestamp
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    
    # Generate random alphanumeric string (5 characters)
    random_str = secrets.token_urlsafe(4)[:5].upper()
    
    # Combine into receipt ID
    receipt_id = f"rcpt_{date_str}_{time_str}_{random_str}"
    
    return receipt_id


def validate_amount(amount: int) -> bool:
    """
    Validate that amount is a positive integer.
    
    Payment amounts must be positive integers (in paise) for Razorpay.
    
    Args:
        amount: Amount to validate (in paise)
    
    Returns:
        True if valid, False otherwise
    
    Example:
        >>> validate_amount(99900)
        True
        >>> validate_amount(0)
        False
        >>> validate_amount(-100)
        False
    """
    # Check if it's an integer
    if not isinstance(amount, int):
        return False
    
    # Check if it's positive
    if amount <= 0:
        return False
    
    return True


def format_currency(amount: int, currency: str = "INR") -> str:
    """
    Format amount for display with currency symbol.
    
    This function converts paise to rupees and formats it with the
    appropriate currency symbol.
    
    Args:
        amount: Amount in paise (integer)
        currency: Currency code (default: INR)
    
    Returns:
        Formatted currency string
    
    Example:
        >>> format_currency(99900, "INR")
        '₹999.00'
        >>> format_currency(99950, "INR")
        '₹999.50'
        >>> format_currency(99900, "USD")
        '$999.00'
        >>> format_currency(0, "INR")
        '₹0.00'
    """
    # Convert paise to rupees
    rupees = paise_to_rupees(amount)
    
    # Get currency symbol
    currency_symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    # Format with 2 decimal places
    formatted = f"{symbol}{rupees:.2f}"
    
    return formatted


def calculate_discount(original_price: int, discounted_price: int) -> float:
    """
    Calculate discount percentage.
    
    This function calculates the discount percentage when comparing
    an original price with a discounted price.
    
    Args:
        original_price: Original price in paise
        discounted_price: Discounted price in paise
    
    Returns:
        Discount percentage (rounded to 1 decimal place)
    
    Example:
        >>> calculate_discount(11988, 9999)
        16.6
        >>> calculate_discount(999, 799)
        20.0
        >>> calculate_discount(100, 100)
        0.0
        >>> calculate_discount(100, 120)
        -20.0
    """
    # Handle edge case where original price is 0
    if original_price == 0:
        return 0.0
    
    # Calculate discount amount
    discount_amount = original_price - discounted_price
    
    # Calculate percentage
    discount_percentage = (discount_amount / original_price) * 100
    
    # Round to 1 decimal place
    return round(discount_percentage, 1)


def validate_signature_format(signature: str) -> bool:
    """
    Validate if signature is a valid hexadecimal string.
    
    Razorpay payment signatures are hexadecimal strings. This function
    validates the format without verifying the actual signature.
    
    Args:
        signature: Payment signature to validate
    
    Returns:
        True if valid hex string, False otherwise
    
    Example:
        >>> validate_signature_format("9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d")
        True
        >>> validate_signature_format("invalid_signature")
        False
        >>> validate_signature_format("")
        False
        >>> validate_signature_format("ABCDEF123456")
        True
    """
    # Check if signature is not empty
    if not signature or not signature.strip():
        return False
    
    # Remove whitespace
    signature = signature.strip()
    
    # Check if it's a valid hexadecimal string
    try:
        # Try to convert to bytes from hex
        bytes.fromhex(signature)
        return True
    except ValueError:
        return False


def calculate_savings(
    monthly_price: int,
    yearly_price: int,
    months: int = 12
) -> int:
    """
    Calculate savings when choosing yearly plan over monthly.
    
    Args:
        monthly_price: Monthly plan price in paise
        yearly_price: Yearly plan price in paise
        months: Number of months (default: 12)
    
    Returns:
        Savings amount in paise
    
    Example:
        >>> calculate_savings(99900, 999900)
        198900
        >>> calculate_savings(99900, 999900, 12)
        198900
    """
    monthly_total = monthly_price * months
    savings = monthly_total - yearly_price
    return savings


def is_free_plan(plan_id: str) -> bool:
    """
    Check if plan is a free plan.
    
    Args:
        plan_id: Subscription plan identifier
    
    Returns:
        True if free plan, False otherwise
    
    Example:
        >>> is_free_plan("free")
        True
        >>> is_free_plan("premium_monthly")
        False
        >>> is_free_plan("Free")
        True
    """
    return plan_id.lower() == "free"


def format_plan_duration(duration_days: int) -> str:
    """
    Format plan duration for display.
    
    Args:
        duration_days: Duration in days
    
    Returns:
        Formatted duration string
    
    Example:
        >>> format_plan_duration(30)
        '1 month'
        >>> format_plan_duration(365)
        '1 year'
        >>> format_plan_duration(60)
        '2 months'
        >>> format_plan_duration(1)
        '1 day'
        >>> format_plan_duration(7)
        '7 days'
    """
    if duration_days == 1:
        return "1 day"
    elif duration_days == 30:
        return "1 month"
    elif duration_days == 365:
        return "1 year"
    elif duration_days % 30 == 0:
        months = duration_days // 30
        return f"{months} month{'s' if months > 1 else ''}"
    elif duration_days % 365 == 0:
        years = duration_days // 365
        return f"{years} year{'s' if years > 1 else ''}"
    else:
        return f"{duration_days} days"


def validate_currency_code(currency: str) -> bool:
    """
    Validate if currency code is supported.
    
    Args:
        currency: Currency code (e.g., INR, USD)
    
    Returns:
        True if supported, False otherwise
    
    Example:
        >>> validate_currency_code("INR")
        True
        >>> validate_currency_code("USD")
        True
        >>> validate_currency_code("XYZ")
        False
        >>> validate_currency_code("inr")
        True
    """
    valid_currencies = {"INR", "USD", "EUR", "GBP"}
    return currency.upper() in valid_currencies


def format_receipt_number(receipt_id: str) -> str:
    """
    Format receipt ID for display.
    
    Args:
        receipt_id: Receipt identifier (e.g., "rcpt_20240115_103000_A7K9M")
    
    Returns:
        Formatted receipt number for display
    
    Example:
        >>> format_receipt_number("rcpt_20240115_103000_A7K9M")
        'RCPT-20240115-103000-A7K9M'
        >>> format_receipt_number("rcpt_test")
        'RCPT-TEST'
    """
    # Replace underscores with hyphens and convert to uppercase
    formatted = receipt_id.replace("_", "-").upper()
    return formatted
