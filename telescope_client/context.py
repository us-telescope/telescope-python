"""
Context management for Telescope client
"""

import threading
from typing import Optional, Dict, Any
from .client import TelescopeClient

# Thread-local storage for client and context
_local = threading.local()


def set_client(client: TelescopeClient):
    """Set the global Telescope client."""
    _local.client = client


def get_client() -> Optional[TelescopeClient]:
    """Get the current Telescope client."""
    return getattr(_local, "client", None)


def set_user_context(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
    **extra_fields,
):
    """
    Set user context for error reporting.

    Args:
        user_id: User identifier
        username: Username
        email: User email
        **extra_fields: Additional user fields

    Example:
        set_user_context(
            user_id="12345",
            username="john_doe",
            email="john@example.com",
            subscription_tier="premium"
        )
    """
    if not hasattr(_local, "context"):
        _local.context = {}

    user_context = {}
    if user_id:
        user_context["id"] = user_id
    if username:
        user_context["username"] = username
    if email:
        user_context["email"] = email

    user_context.update(extra_fields)
    _local.context["user"] = user_context


def set_tags(**tags):
    """
    Set tags for error reporting.

    Args:
        **tags: Tag key-value pairs

    Example:
        set_tags(
            component="payment",
            version="1.2.3",
            feature_flag="new_checkout"
        )
    """
    if not hasattr(_local, "context"):
        _local.context = {}

    if "tags" not in _local.context:
        _local.context["tags"] = {}

    _local.context["tags"].update(tags)


def set_extra(**extra):
    """
    Set extra context data for error reporting.

    Args:
        **extra: Extra context key-value pairs

    Example:
        set_extra(
            request_id="req_123456",
            correlation_id="corr_789",
            feature_flags={"new_ui": True}
        )
    """
    if not hasattr(_local, "context"):
        _local.context = {}

    if "extra" not in _local.context:
        _local.context["extra"] = {}

    _local.context["extra"].update(extra)


def get_context() -> Dict[str, Any]:
    """Get the current context."""
    return getattr(_local, "context", {})


def clear_context():
    """Clear all context data."""
    if hasattr(_local, "context"):
        _local.context = {}


def with_context(**context_data):
    """
    Context manager to temporarily set context data.

    Args:
        **context_data: Context data to set

    Example:
        with with_context(user_id="123", component="auth"):
            # Any errors here will include this context
            authenticate_user()
    """

    class ContextManager:
        def __init__(self, context_data):
            self.context_data = context_data
            self.original_context = None

        def __enter__(self):
            # Save original context
            self.original_context = get_context().copy()

            # Apply new context
            for key, value in self.context_data.items():
                if key == "user":
                    set_user_context(**value)
                elif key == "tags":
                    set_tags(**value)
                elif key == "extra":
                    set_extra(**value)

            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            # Restore original context
            if hasattr(_local, "context"):
                _local.context = self.original_context

    return ContextManager(context_data)


def capture_context_in_exception(exception: Exception, **additional_context):
    """
    Capture an exception with current context plus additional context.

    Args:
        exception: Exception to capture
        **additional_context: Additional context to include

    Example:
        try:
            risky_operation()
        except Exception as e:
            capture_context_in_exception(
                e,
                operation="risky_operation",
                attempt_number=3
            )
            raise
    """
    client = get_client()
    if not client:
        return

    context = get_context()

    # Merge contexts
    user = context.get("user", {})
    tags = context.get("tags", {})
    extra = context.get("extra", {})

    # Add additional context
    if "user" in additional_context:
        user.update(additional_context.pop("user"))
    if "tags" in additional_context:
        tags.update(additional_context.pop("tags"))
    if "extra" in additional_context:
        extra.update(additional_context.pop("extra"))

    # Remaining additional_context goes to extra
    extra.update(additional_context)

    client.capture_exception(
        exception,
        user=user if user else None,
        tags=tags if tags else None,
        extra=extra if extra else None,
    )


class TelescopeContextMiddleware:
    """
    Middleware to automatically manage Telescope context in web applications.
    """

    def __init__(self, client: TelescopeClient):
        self.client = client

    def __call__(self, request, response):
        """Process request and set up context."""
        # Clear any existing context
        clear_context()

        # Set client for this request
        set_client(self.client)

        # Extract user context if available
        if hasattr(request, "user") and hasattr(request.user, "is_authenticated"):
            if request.user.is_authenticated:
                set_user_context(
                    user_id=str(request.user.id),
                    username=getattr(request.user, "username", ""),
                    email=getattr(request.user, "email", ""),
                )

        # Set request-specific tags
        set_tags(
            url=getattr(request, "path", ""),
            method=getattr(request, "method", ""),
            user_agent=getattr(request, "META", {}).get("HTTP_USER_AGENT", ""),
        )

        # Set request-specific extra data
        set_extra(
            request_id=getattr(request, "META", {}).get("HTTP_X_REQUEST_ID", ""),
            ip_address=getattr(request, "META", {}).get("REMOTE_ADDR", ""),
        )

        return response
