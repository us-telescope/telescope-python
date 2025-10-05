"""
Starlette integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import TelescopeClient


class StarletteIntegration:
    """
    Starlette integration for Telescope client.

    Automatically captures exceptions and provides tracing for Starlette applications.
    """

    identifier = "starlette"

    def __init__(self, **options: Any):
        """Initialize Starlette integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Starlette integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from opentelemetry.instrumentation.starlette import StarletteInstrumentor
            from starlette.applications import Starlette
            from starlette.middleware.base import BaseHTTPMiddleware
            from starlette.requests import Request
            from starlette.responses import Response

            class TelescopeMiddleware(BaseHTTPMiddleware):
                def __init__(self, app, client: "TelescopeClient"):
                    super().__init__(app)
                    self.client = client

                async def dispatch(self, request: Request, call_next):
                    try:
                        response = await call_next(request)
                        return response
                    except Exception as e:
                        # Extract user context if available
                        user_context = {}
                        if hasattr(request, "user") and request.user:
                            user_context = {
                                "id": str(getattr(request.user, "id", "")),
                                "username": getattr(request.user, "username", ""),
                                "email": getattr(request.user, "email", ""),
                            }

                        tags = {
                            "url": str(request.url),
                            "method": request.method,
                            "user_agent": request.headers.get("user-agent", ""),
                        }

                        extra = {
                            "request": {
                                "url": str(request.url),
                                "method": request.method,
                                "headers": dict(request.headers),
                                "query_params": dict(request.query_params),
                            }
                        }

                        event_id = self.client.capture_exception(
                            e,
                            tags=tags,
                            extra=extra,
                            user=user_context,
                        )

                        # Return error response with Telescope event ID
                        return Response(
                            content=f"Internal server error (Event ID: {event_id})",
                            status_code=500,
                            media_type="text/plain",
                        )

            def init_app(app: Starlette):
                """Initialize Starlette app with Telescope."""
                StarletteInstrumentor().instrument_app(app)
                app.add_middleware(TelescopeMiddleware, client=client)

            return init_app

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable(
                "Starlette not found, skipping Starlette integration"
            ) from e


def setup_starlette_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return StarletteIntegration().setup(client)
