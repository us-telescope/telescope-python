"""
FastAPI integration for Telescope
"""

from ..client import TelescopeClient


class FastAPIIntegration:
    """
    FastAPI integration for Telescope client.

    Automatically captures exceptions and provides tracing for FastAPI applications.

    Example:
        from telescope import TelescopeClient
        from telescope.integrations.fastapi import FastAPIIntegration

        client = TelescopeClient(
            dsn="http://localhost:8080",
            project_id="MY-PROJECT",
            enable_tracing=True
        )

        # Setup FastAPI integration
        FastAPIIntegration().setup(client)
    """

    def __init__(self, **options):
        """
        Initialize FastAPI integration.

        Args:
            **options: Additional options for FastAPI integration
        """
        self.options = options

    def setup(self, client: TelescopeClient):
        """
        Setup FastAPI integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from fastapi import FastAPI, HTTPException, Request
            from fastapi.responses import JSONResponse
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            def init_app(app: FastAPI):
                """Initialize FastAPI app with Telescope."""

                # Instrument FastAPI
                FastAPIInstrumentor().instrument_app(app)

                # Instrument SQLAlchemy if available
                try:
                    SQLAlchemyInstrumentor().instrument()
                except Exception:
                    pass

                @app.exception_handler(Exception)
                async def telescope_exception_handler(request: Request, exc: Exception):
                    """Handle FastAPI exceptions with Telescope."""

                    # Extract user context if available
                    user_context = {}
                    if hasattr(request.state, "user") and request.state.user:
                        user_context = {
                            "id": str(request.state.user.id),
                            "username": getattr(request.state.user, "username", ""),
                            "email": getattr(request.state.user, "email", ""),
                        }

                    tags = {
                        "url": str(request.url),
                        "method": request.method,
                        "user_agent": request.headers.get("user-agent", ""),
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

                    # Capture the exception
                    event_id = client.capture_exception(
                        exc,
                        tags=tags,
                        extra=extra,
                        user=user_context,
                    )

                    # Return appropriate response
                    if isinstance(exc, HTTPException):
                        return JSONResponse(
                            status_code=exc.status_code,
                            content={
                                "detail": exc.detail,
                                "telescope_event_id": event_id,
                            },
                        )
                    else:
                        return JSONResponse(
                            status_code=500,
                            content={
                                "detail": "Internal server error",
                                "telescope_event_id": event_id,
                            },
                        )

                return app

            return init_app

        except ImportError:
            print("FastAPI not found, skipping FastAPI integration")


def setup_fastapi_integration(client: TelescopeClient):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return FastAPIIntegration().setup(client)
