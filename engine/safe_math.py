#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.safe_math
================

Safe math operations with NaN/Infinity/Overflow protection.

This module provides safe wrappers for mathematical operations that
may fail with extreme or invalid inputs.

Usage:
    from engine.safe_math import safe_sqrt, safe_log, safe_divide

    # Instead of math.sqrt(-1) -> ValueError
    result = safe_sqrt(-1)  # Returns None or fallback

    # Instead of math.log(-1) -> ValueError
    result = safe_log(-1)   # Returns None or fallback

Author: Eco Nojin Architecture Team
Version: 2.0.0
"""

import math
import sys
from typing import Optional, Union, Any
from functools import wraps

# Recursion protection
MAX_RECURSION_DEPTH = 1000
if sys.getrecursionlimit() < MAX_RECURSION_DEPTH + 100:
    sys.setrecursionlimit(MAX_RECURSION_DEPTH + 100)


class SafeMathError(Exception):
    """Custom exception for safe math operations."""
    pass


def _is_valid_number(value: Any) -> bool:
    """Check if value is a valid, finite number."""
    if value is None:
        return False
    try:
        if isinstance(value, (int, float)):
            return not (math.isnan(value) or math.isinf(value))
        float(value)
        return True
    except (ValueError, TypeError, OverflowError):
        return False


def safe_sqrt(x: Any, fallback: Optional[float] = None) -> Optional[float]:
    """
    Safe square root with NaN/Infinity/negative protection.

    Args:
        x: Input value (can be None, NaN, negative, etc.)
        fallback: Value to return if operation fails (default: None)

    Returns:
        Square root of x, or fallback if invalid input

    Examples:
        >>> safe_sqrt(4)
        2.0
        >>> safe_sqrt(-1)
        None
        >>> safe_sqrt(-1, fallback=0.0)
        0.0
        >>> safe_sqrt(float('nan'))
        None
    """
    if not _is_valid_number(x):
        return fallback
    try:
        x_float = float(x)
        if x_float < 0:
            return fallback
        return math.sqrt(x_float)
    except (ValueError, OverflowError, TypeError):
        return fallback


def safe_log(x: Any, base: float = math.e, fallback: Optional[float] = None) -> Optional[float]:
    """
    Safe logarithm with NaN/Infinity/non-positive protection.

    Args:
        x: Input value (must be positive)
        base: Logarithm base (default: natural log)
        fallback: Value to return if operation fails (default: None)

    Returns:
        Logarithm of x, or fallback if invalid input

    Examples:
        >>> safe_log(10)
        2.302585092994046
        >>> safe_log(-1)
        None
        >>> safe_log(0)
        None
        >>> safe_log(100, base=10)
        2.0
    """
    if not _is_valid_number(x):
        return fallback
    try:
        x_float = float(x)
        if x_float <= 0:
            return fallback
        if base == math.e:
            return math.log(x_float)
        return math.log(x_float, base)
    except (ValueError, OverflowError, TypeError, ZeroDivisionError):
        return fallback


def safe_divide(a: Any, b: Any, fallback: Optional[float] = None) -> Optional[float]:
    """
    Safe division with zero/NaN/Infinity protection.

    Args:
        a: Numerator
        b: Denominator
        fallback: Value to return if operation fails (default: None)

    Returns:
        a / b, or fallback if invalid input

    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        None
        >>> safe_divide(10, 0, fallback=0.0)
        0.0
    """
    if not _is_valid_number(a) or not _is_valid_number(b):
        return fallback
    try:
        a_float = float(a)
        b_float = float(b)
        if b_float == 0:
            return fallback
        result = a_float / b_float
        if math.isinf(result) or math.isnan(result):
            return fallback
        return result
    except (ValueError, OverflowError, TypeError, ZeroDivisionError):
        return fallback


def safe_exp(x: Any, fallback: Optional[float] = None, max_value: float = 700.0) -> Optional[float]:
    """
    Safe exponential with overflow protection.

    Args:
        x: Input value
        fallback: Value to return if operation fails (default: None)
        max_value: Maximum allowed input to prevent overflow

    Returns:
        exp(x), or fallback if invalid or would overflow

    Examples:
        >>> safe_exp(1)
        2.718281828459045
        >>> safe_exp(1000)  # Would overflow
        None
    """
    if not _is_valid_number(x):
        return fallback
    try:
        x_float = float(x)
        if abs(x_float) > max_value:
            return fallback
        return math.exp(x_float)
    except (ValueError, OverflowError, TypeError):
        return fallback


def safe_power(base: Any, exponent: Any, fallback: Optional[float] = None) -> Optional[float]:
    """
    Safe power operation with overflow protection.

    Args:
        base: Base value
        exponent: Exponent value
        fallback: Value to return if operation fails

    Returns:
        base ** exponent, or fallback if invalid
    """
    if not _is_valid_number(base) or not _is_valid_number(exponent):
        return fallback
    try:
        base_float = float(base)
        exp_float = float(exponent)
        # Prevent overflow
        if abs(base_float) > 1 and exp_float > 100:
            return fallback
        if abs(base_float) < 1 and exp_float < -100:
            return fallback
        result = base_float ** exp_float
        if math.isinf(result) or math.isnan(result):
            return fallback
        return result
    except (ValueError, OverflowError, TypeError):
        return fallback


def nan_guard(value: Any, fallback: float = 0.0) -> float:
    """
    Guard against NaN/Infinity values, returning a fallback.

    Args:
        value: Input value to check
        fallback: Value to return if input is NaN/Infinity/None

    Returns:
        Original value if valid, otherwise fallback

    Examples:
        >>> nan_guard(5.0)
        5.0
        >>> nan_guard(float('nan'))
        0.0
        >>> nan_guard(None, fallback=-1.0)
        -1.0
    """
    if value is None:
        return fallback
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return fallback
        return f
    except (ValueError, TypeError):
        return fallback


def validate_numeric(value: Any, min_val: Optional[float] = None,
                     max_val: Optional[float] = None) -> Optional[float]:
    """
    Validate a numeric value within a range.

    Args:
        value: Input value
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Returns:
        Validated float, or None if invalid

    Examples:
        >>> validate_numeric(5, min_val=0, max_val=10)
        5.0
        >>> validate_numeric(-5, min_val=0)
        None
    """
    if not _is_valid_number(value):
        return None
    try:
        f = float(value)
        if min_val is not None and f < min_val:
            return None
        if max_val is not None and f > max_val:
            return None
        return f
    except (ValueError, TypeError):
        return None


def with_safe_math(fallback: Any = None):
    """
    Decorator to wrap a function with safe math error handling.

    Usage:
        @with_safe_math(fallback=0.0)
        def compute_metric(x, y):
            return math.log(x) / math.sqrt(y)

        # If any operation fails, returns 0.0
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if not _is_valid_number(result):
                    return fallback
                return result
            except (ValueError, OverflowError, TypeError, ZeroDivisionError,
                    RecursionError, ArithmeticError):
                return fallback
        return wrapper
    return decorator


__all__ = [
    "SafeMathError",
    "safe_sqrt",
    "safe_log",
    "safe_divide",
    "safe_exp",
    "safe_power",
    "nan_guard",
    "validate_numeric",
    "with_safe_math",
    "MAX_RECURSION_DEPTH",
]
