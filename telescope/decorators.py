"""
Decorators for Telescope client
"""

import functools
from typing import Optional, Dict, Any, Callable
from opentelemetry import trace
from .context import get_client


def capture_errors(
    level: str = "error",
    tags: Optional[Dict[str, str]] = None,
    extra: Optional[Dict[str, Any]] = None,
    reraise: bool = True,
):
    """
    Decorator to automatically capture exceptions from functions.

    Args:
        level: Error level for captured exceptions
        tags: Additional tags to add to captured exceptions
        extra: Additional context data
        reraise: Whether to re-raise the exception after capturing

    Example:
        @capture_errors(tags={"component": "payment"})
        def process_payment(amount):
            # This will automatically capture any exceptions
            return charge_card(amount)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client = get_client()
            if not client:
                return func(*args, **kwargs)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture the exception
                client.capture_exception(
                    e,
                    level=level,
                    tags=tags,
                    extra=extra,
                )

                if reraise:
                    raise
                return None

        return wrapper

    return decorator


def trace_function(
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    capture_args: bool = False,
    capture_result: bool = False,
):
    """
    Decorator to trace function execution with OpenTelemetry.

    Args:
        name: Custom span name (defaults to function name)
        tags: Additional tags/attributes for the span
        capture_args: Whether to capture function arguments
        capture_result: Whether to capture function result

    Example:
        @trace_function(tags={"component": "database"}, capture_args=True)
        def get_user(user_id):
            return User.objects.get(id=user_id)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = name or f"{func.__module__}.{func.__name__}"

            with tracer.start_span(span_name) as span:
                # Add function metadata
                span.set_attributes(
                    {
                        "function.name": func.__name__,
                        "function.module": func.__module__,
                    }
                )

                # Add custom tags
                if tags:
                    for key, value in tags.items():
                        span.set_attribute(key, value)

                # Capture arguments if requested
                if capture_args:
                    try:
                        import inspect

                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()

                        for param_name, param_value in bound_args.arguments.items():
                            # Only capture simple types to avoid serialization issues
                            if isinstance(param_value, (str, int, float, bool)):
                                span.set_attribute(
                                    f"function.args.{param_name}", param_value
                                )
                    except Exception:
                        # Don't let argument capture break the function
                        pass

                try:
                    result = func(*args, **kwargs)

                    # Capture result if requested
                    if capture_result and isinstance(result, (str, int, float, bool)):
                        span.set_attribute("function.result", result)

                    return result

                except Exception as e:
                    # Record exception in span
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


def performance_monitor(
    threshold_ms: float = 1000.0,
    tags: Optional[Dict[str, str]] = None,
):
    """
    Decorator to monitor function performance and report slow executions.

    Args:
        threshold_ms: Threshold in milliseconds to report slow executions
        tags: Additional tags for performance events

    Example:
        @performance_monitor(threshold_ms=500, tags={"component": "api"})
        def expensive_operation():
            # Will report if takes longer than 500ms
            time.sleep(1)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            client = get_client()
            tracer = trace.get_tracer(__name__)

            start_time = time.time()

            with tracer.start_span(f"performance.{func.__name__}") as span:
                span.set_attributes(
                    {
                        "function.name": func.__name__,
                        "function.module": func.__module__,
                        "performance.threshold_ms": threshold_ms,
                    }
                )

                if tags:
                    for key, value in tags.items():
                        span.set_attribute(key, value)

                try:
                    result = func(*args, **kwargs)

                    # Calculate execution time
                    execution_time = (time.time() - start_time) * 1000
                    span.set_attribute("performance.duration_ms", execution_time)

                    # Report slow execution
                    if client and execution_time > threshold_ms:
                        performance_tags = {
                            "function": func.__name__,
                            "module": func.__module__,
                            "slow_execution": True,
                        }
                        if tags:
                            performance_tags.update(tags)

                        client.capture_message(
                            f"Slow execution: {func.__name__} took {execution_time:.2f}ms",
                            level="warning",
                            tags=performance_tags,
                            extra={
                                "performance": {
                                    "duration_ms": execution_time,
                                    "threshold_ms": threshold_ms,
                                    "function": func.__name__,
                                }
                            },
                        )

                    return result

                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    span.set_attribute("performance.duration_ms", execution_time)
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


def retry_with_telemetry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator to retry functions with telemetry tracking.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry

    Example:
        @retry_with_telemetry(max_retries=3, exceptions=(ConnectionError,))
        def call_external_api():
            return requests.get("https://api.example.com/data")
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            client = get_client()
            tracer = trace.get_tracer(__name__)

            with tracer.start_span(f"retry.{func.__name__}") as span:
                span.set_attributes(
                    {
                        "function.name": func.__name__,
                        "retry.max_attempts": max_retries,
                        "retry.delay": delay,
                        "retry.backoff": backoff,
                    }
                )

                last_exception = None
                current_delay = delay

                for attempt in range(max_retries + 1):
                    span.set_attribute("retry.attempt", attempt + 1)

                    try:
                        result = func(*args, **kwargs)

                        if attempt > 0:
                            # Log successful retry
                            span.set_attribute("retry.succeeded", True)
                            if client:
                                client.capture_message(
                                    f"Function {func.__name__} succeeded after {attempt} retries",
                                    level="info",
                                    tags={
                                        "function": func.__name__,
                                        "retry_success": True,
                                        "attempts": attempt + 1,
                                    },
                                )

                        return result

                    except exceptions as e:
                        last_exception = e
                        span.record_exception(e)

                        if attempt < max_retries:
                            # Log retry attempt
                            if client:
                                client.capture_message(
                                    f"Retrying {func.__name__} after error: {str(e)}",
                                    level="warning",
                                    tags={
                                        "function": func.__name__,
                                        "retry_attempt": True,
                                        "attempt": attempt + 1,
                                        "max_retries": max_retries,
                                    },
                                )

                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            # Final failure
                            span.set_attribute("retry.failed", True)
                            span.set_status(
                                trace.Status(trace.StatusCode.ERROR, str(e))
                            )

                            if client:
                                client.capture_exception(
                                    e,
                                    level="error",
                                    tags={
                                        "function": func.__name__,
                                        "retry_exhausted": True,
                                        "total_attempts": attempt + 1,
                                    },
                                    extra={
                                        "retry": {
                                            "max_retries": max_retries,
                                            "total_attempts": attempt + 1,
                                            "final_delay": current_delay / backoff,
                                        }
                                    },
                                )

                            raise last_exception

                # This should never be reached
                raise last_exception

        return wrapper

    return decorator
