"""
Quart integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

from opentelemetry.instrumentation.quart import QuartInstrumentor

if TYPE_CHECKING:
    from ..client import TelescopeClient


class QuartIntegration:
    """
    Quart integration for Telescope client.

    Automatically captures exceptions and provides tracing for Quart applications.
    """

    identifier = "quart"

    def __init__(self, **options: Any):
        """Initialize Quart integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Quart integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from quart import Quart, g, request

            def init_app(app: Quart):
                """Initialize Quart app with Telescope."""

                # Instrument Quart
                QuartInstrumentor().instrument_app(app)

                @app.errorhandler(Exception)
                async def handle_exception(error: Exception):
                    """Handle Quart exceptions."""
                    user_context = {}
                    if hasattr(g, "user"):
                        user_context = {
                            "id": str(g.user.id),
                            "username": getattr(g.user, "username", ""),
                            "email": getattr(g.user, "email", ""),
                        }

                    tags = {
                        "url": request.path,
                        "method": request.method,
                        "user_agent": request.headers.get("User-Agent", ""),
                    }

                    extra = {
                        "request": {
                            "url": request.path,
                            "method": request.method,
                            "headers": dict(request.headers),
                            "data": await request.get_data() if request.is_json else {},
                            "query_string": dict(request.args),
                        }
                    }

                    event_id = client.capture_exception(
                        error,
                        tags=tags,
                        extra=extra,
                        user=user_context,
                    )

                    # Return error response with Telescope event ID
                    return f"Internal server error (Event ID: {event_id})", 500

            return init_app

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("Quart not found, skipping Quart integration") from e


def setup_quart_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return QuartIntegration().setup(client)
