"""
Sanic integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

from opentelemetry.instrumentation.sanic import SanicInstrumentor

if TYPE_CHECKING:
    from ..client import TelescopeClient


class SanicIntegration:
    """
    Sanic integration for Telescope client.

    Automatically captures exceptions and provides tracing for Sanic applications.
    """

    identifier = "sanic"

    def __init__(self, **options: Any):
        """Initialize Sanic integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Sanic integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from sanic import Request, Sanic
            from sanic.response import text

            def init_app(app: Sanic):
                """Initialize Sanic app with Telescope."""

                # Instrument Sanic
                SanicInstrumentor().instrument_app(app)

                @app.exception(Exception)
                async def handle_exception(request: Request, exception: Exception):
                    """Handle Sanic exceptions."""
                    user_context = {}
                    if hasattr(request, "user"):
                        user_context = {
                            "id": str(request.user.id),
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
                            "query_string": dict(request.args),
                        }
                    }

                    event_id = client.capture_exception(
                        exception,
                        tags=tags,
                        extra=extra,
                        user=user_context,
                    )

                    # Return error response with Telescope event ID
                    return text(
                        f"Internal server error (Event ID: {event_id})", status=500
                    )

            return init_app

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("Sanic not found, skipping Sanic integration") from e


def setup_sanic_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return SanicIntegration().setup(client)
