"""
Decorators module - Advanced Python topic.
Provides decorators for input validation, error handling, and caching.
"""

import functools
from typing import Callable, Any
from datetime import datetime, timedelta


def validate_input(validator_func: Callable) -> Callable:
    """
    Decorator for validating function inputs.
    
    Usage:
        @validate_input(validate_price)
        def process_price(price):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate first argument
            if args and not validator_func(args[0]):
                raise ValueError(f"Invalid input: {args[0]}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def error_handler(exception_type: Exception = Exception) -> Callable:
    """
    Decorator for handling exceptions gracefully.
    
    Usage:
        @error_handler(ValueError)
        def risky_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                print(f"Error in {func.__name__}: {str(e)}")
                return None
        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution time and arguments.
    
    Usage:
        @log_execution
        def expensive_operation():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        print(f"[LOG] Executing {func.__name__} with args={args}, kwargs={kwargs}")
        
        result = func(*args, **kwargs)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[LOG] {func.__name__} completed in {elapsed:.4f}s")
        return result
    return wrapper


def cache_result(timeout_seconds: int = 300) -> Callable:
    """
    Decorator for caching function results with timeout.
    Useful for expensive API calls.
    
    Usage:
        @cache_result(timeout_seconds=600)
        def fetch_price(symbol):
            ...
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from args
            cache_key = str(args) + str(kwargs)
            now = datetime.now()
            
            # Check if cache exists and is valid
            if cache_key in cache:
                cached_time = cache_time[cache_key]
                if now - cached_time < timedelta(seconds=timeout_seconds):
                    print(f"[CACHE] Using cached result for {func.__name__}")
                    return cache[cache_key]
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_time[cache_key] = now
            return result
        
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay_seconds: float = 1.0) -> Callable:
    """
    Decorator for retrying function on failure.
    
    Usage:
        @retry(max_attempts=3, delay_seconds=2)
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        print(f"[RETRY] Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    print(f"[RETRY] Attempt {attempt + 1} failed, retrying in {delay_seconds}s...")
                    time.sleep(delay_seconds)
        return wrapper
    return decorator


def type_check(**type_hints) -> Callable:
    """
    Decorator for runtime type checking.
    
    Usage:
        @type_check(price=float, symbol=str)
        def update_price(price, symbol):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check keyword arguments
            for arg_name, expected_type in type_hints.items():
                if arg_name in kwargs:
                    if not isinstance(kwargs[arg_name], expected_type):
                        raise TypeError(
                            f"Argument '{arg_name}' must be {expected_type.__name__}, "
                            f"got {type(kwargs[arg_name]).__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def deprecated(message: str = "This function is deprecated.") -> Callable:
    """
    Decorator to mark function as deprecated.
    
    Usage:
        @deprecated("Use new_function instead")
        def old_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[DEPRECATED] {func.__name__}: {message}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
