"""
Tornado integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import TelescopeClient


class TornadoIntegration:
    """
    Tornado integration for Telescope client.

    Automatically captures exceptions and provides tracing for Tornado applications.
    """

    identifier = "tornado"

    def __init__(self, **options: Any):
        """Initialize Tornado integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Tornado integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from opentelemetry.instrumentation.tornado import TornadoInstrumentor
            from tornado.web import Application, RequestHandler

            class TelescopeRequestHandler(RequestHandler):
                """Base request handler with Telescope integration."""

                def write_error(self, status_code: int, **kwargs):
                    """Handle errors with Telescope."""
                    if "exc_info" in kwargs:
                        exc_type, exc_value, exc_traceback = kwargs["exc_info"]

                        user_context = {}
                        if hasattr(self, "current_user") and self.current_user:
                            user_context = {
                                "id": str(getattr(self.current_user, "id", "")),
                                "username": getattr(self.current_user, "username", ""),
                                "email": getattr(self.current_user, "email", ""),
                            }

                        tags = {
                            "url": self.request.uri,
                            "method": self.request.method,
                            "user_agent": self.request.headers.get("User-Agent", ""),
                        }

                        extra = {
                            "request": {
                                "url": self.request.uri,
                                "method": self.request.method,
                                "headers": dict(self.request.headers),
                                "query_string": dict(self.request.arguments),
                            }
                        }

                        event_id = client.capture_exception(
                            exc_value,
                            tags=tags,
                            extra=extra,
                            user=user_context,
                        )

                        self.write(f"Internal server error (Event ID: {event_id})")
                    else:
                        self.write(f"Error {status_code}")

            def init_app(app: Application):
                """Initialize Tornado app with Telescope."""
                TornadoInstrumentor().instrument()

                # Replace default RequestHandler with TelescopeRequestHandler
                app.default_handler_class = TelescopeRequestHandler

            return init_app

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("Tornado not found, skipping Tornado integration") from e


def setup_tornado_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return TornadoIntegration().setup(client)
