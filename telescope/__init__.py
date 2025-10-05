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
from .context import clear_context, set_tags, set_user_context
from .decorators import capture_errors, trace_function
from .integrations.django import DjangoIntegration, setup_django_integration
from .integrations.fastapi import FastAPIIntegration, setup_fastapi_integration
from .integrations.flask import FlaskIntegration, setup_flask_integration

__version__ = "1.0.0"
__all__ = [
    "TelescopeClient",
    "setup_django_integration",
    "setup_flask_integration",
    "setup_fastapi_integration",
    "DjangoIntegration",
    "FlaskIntegration",
    "FastAPIIntegration",
    "capture_errors",
    "trace_function",
    "set_user_context",
    "set_tags",
    "clear_context",
]
