"""
Telescope Python Client with OpenTelemetry Integration
=====================================================

A comprehensive error monitoring and observability client for Python applications
that integrates with OpenTelemetry for enhanced tracing and metrics collection.

Features:
- Error tracking and reporting
- OpenTelemetry trace correlation
- Performance monitoring
- Environment-aware reporting
- Automatic context enrichment
"""

from .client import TelescopeClient
from .integrations import setup_django_integration, setup_flask_integration
from .decorators import capture_errors, trace_function
from .context import set_user_context, set_tags, clear_context

__version__ = "1.0.0"
__all__ = [
    "TelescopeClient",
    "setup_django_integration",
    "setup_flask_integration",
    "capture_errors",
    "trace_function",
    "set_user_context",
    "set_tags",
    "clear_context",
]
