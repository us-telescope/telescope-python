"""
Framework integrations for Telescope client
"""

from .client import TelescopeClient


def setup_django_integration(client: TelescopeClient):
    """
    Setup Django integration with automatic error capture and tracing.
    """
    try:
        from django.core.signals import got_request_exception
        from django.db import connection
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

        # Instrument Django
        DjangoInstrumentor().instrument()

        # Instrument database
        Psycopg2Instrumentor().instrument()

        def handle_exception(sender, request, **kwargs):
            """Handle Django exceptions."""
            import sys

            exc_info = sys.exc_info()
            if exc_info[1]:
                # Extract request context
                user_context = {}
                if hasattr(request, "user") and request.user.is_authenticated:
                    user_context = {
                        "id": str(request.user.id),
                        "username": request.user.username,
                        "email": getattr(request.user, "email", ""),
                    }

                tags = {
                    "url": request.get_full_path(),
                    "method": request.method,
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                }

                extra = {
                    "request": {
                        "url": request.get_full_path(),
                        "method": request.method,
                        "headers": dict(request.headers),
                        "data": request.POST.dict() if request.POST else {},
                        "query_string": request.GET.dict(),
                    }
                }

                client.capture_exception(
                    exc_info[1],
                    tags=tags,
                    extra=extra,
                    user=user_context,
                )

        got_request_exception.connect(handle_exception)

    except ImportError:
        print("Django not found, skipping Django integration")


def setup_flask_integration(client: TelescopeClient):
    """
    Setup Flask integration with automatic error capture and tracing.
    """
    try:
        from flask import Flask, request, g
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        def init_app(app: Flask):
            """Initialize Flask app with Telescope."""

            # Instrument Flask
            FlaskInstrumentor().instrument_app(app)

            # Instrument SQLAlchemy if available
            try:
                SQLAlchemyInstrumentor().instrument()
            except:
                pass

            @app.errorhandler(Exception)
            def handle_exception(error):
                """Handle Flask exceptions."""
                user_context = {}
                if hasattr(g, "user"):
                    user_context = {
                        "id": str(g.user.id),
                        "username": getattr(g.user, "username", ""),
                        "email": getattr(g.user, "email", ""),
                    }

                tags = {
                    "url": request.url,
                    "method": request.method,
                    "endpoint": request.endpoint,
                }

                extra = {
                    "request": {
                        "url": request.url,
                        "method": request.method,
                        "headers": dict(request.headers),
                        "data": request.get_json() if request.is_json else {},
                        "args": request.args.to_dict(),
                    }
                }

                client.capture_exception(
                    error,
                    tags=tags,
                    extra=extra,
                    user=user_context,
                )

                # Re-raise the exception
                raise error

        return init_app

    except ImportError:
        print("Flask not found, skipping Flask integration")
        return None


def setup_fastapi_integration(client: TelescopeClient):
    """
    Setup FastAPI integration with automatic error capture and tracing.
    """
    try:
        from fastapi import FastAPI, Request, HTTPException
        from fastapi.responses import JSONResponse
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        def init_app(app: FastAPI):
            """Initialize FastAPI app with Telescope."""

            # Instrument FastAPI
            FastAPIInstrumentor.instrument_app(app)

            # Instrument SQLAlchemy if available
            try:
                SQLAlchemyInstrumentor().instrument()
            except:
                pass

            @app.exception_handler(Exception)
            async def handle_exception(request: Request, exc: Exception):
                """Handle FastAPI exceptions."""

                # Extract user context if available
                user_context = {}
                if hasattr(request.state, "user"):
                    user = request.state.user
                    user_context = {
                        "id": str(getattr(user, "id", "")),
                        "username": getattr(user, "username", ""),
                        "email": getattr(user, "email", ""),
                    }

                tags = {
                    "url": str(request.url),
                    "method": request.method,
                    "path": request.url.path,
                }

                extra = {
                    "request": {
                        "url": str(request.url),
                        "method": request.method,
                        "headers": dict(request.headers),
                        "path_params": request.path_params,
                        "query_params": dict(request.query_params),
                    }
                }

                client.capture_exception(
                    exc,
                    tags=tags,
                    extra=extra,
                    user=user_context,
                )

                # Return error response
                if isinstance(exc, HTTPException):
                    return JSONResponse(
                        status_code=exc.status_code, content={"detail": exc.detail}
                    )

                return JSONResponse(
                    status_code=500, content={"detail": "Internal server error"}
                )

        return init_app

    except ImportError:
        print("FastAPI not found, skipping FastAPI integration")
        return None


def setup_celery_integration(client: TelescopeClient):
    """
    Setup Celery integration for background task monitoring.
    """
    try:
        from celery import Celery
        from celery.signals import task_failure
        from opentelemetry.instrumentation.celery import CeleryInstrumentor

        # Instrument Celery
        CeleryInstrumentor().instrument()

        @task_failure.connect
        def handle_task_failure(
            sender=None,
            task_id=None,
            exception=None,
            traceback=None,
            einfo=None,
            **kwargs,
        ):
            """Handle Celery task failures."""

            tags = {
                "task_name": sender.name if sender else "unknown",
                "task_id": task_id,
                "celery_task": True,
            }

            extra = {
                "task": {
                    "name": sender.name if sender else "unknown",
                    "id": task_id,
                    "args": getattr(sender, "args", []),
                    "kwargs": getattr(sender, "kwargs", {}),
                }
            }

            client.capture_exception(
                exception,
                tags=tags,
                extra=extra,
            )

    except ImportError:
        print("Celery not found, skipping Celery integration")


def setup_logging_integration(client: TelescopeClient, level: str = "ERROR"):
    """
    Setup Python logging integration to capture log messages.
    """
    import logging
    from opentelemetry.instrumentation.logging import LoggingInstrumentor

    # Instrument logging
    LoggingInstrumentor().instrument()

    class TelescopeHandler(logging.Handler):
        """Custom logging handler for Telescope."""

        def __init__(self, client: TelescopeClient):
            super().__init__()
            self.client = client

        def emit(self, record):
            """Emit a log record to Telescope."""
            try:
                # Map logging levels to Telescope levels
                level_mapping = {
                    logging.DEBUG: "debug",
                    logging.INFO: "info",
                    logging.WARNING: "warning",
                    logging.ERROR: "error",
                    logging.CRITICAL: "fatal",
                }

                telescope_level = level_mapping.get(record.levelno, "info")

                tags = {
                    "logger": record.name,
                    "level": record.levelname,
                }

                extra = {
                    "logging": {
                        "name": record.name,
                        "level": record.levelname,
                        "pathname": record.pathname,
                        "lineno": record.lineno,
                        "funcName": record.funcName,
                    }
                }

                if record.exc_info:
                    # This is an exception
                    client.capture_exception(
                        record.exc_info[1],
                        level=telescope_level,
                        tags=tags,
                        extra=extra,
                    )
                else:
                    # This is a message
                    client.capture_message(
                        record.getMessage(),
                        level=telescope_level,
                        tags=tags,
                        extra=extra,
                    )

            except Exception:
                # Don't let logging errors break the application
                pass

    # Add handler to root logger
    handler = TelescopeHandler(client)
    handler.setLevel(getattr(logging, level.upper()))
    logging.getLogger().addHandler(handler)

    return handler
