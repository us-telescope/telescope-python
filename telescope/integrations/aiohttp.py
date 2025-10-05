"""
AioHTTP integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import TelescopeClient


class AioHttpIntegration:
    """
    AioHTTP integration for Telescope client.

    Automatically captures exceptions and provides tracing for AioHTTP applications.
    """

    identifier = "aiohttp"

    def __init__(self, **options: Any):
        """Initialize AioHTTP integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup AioHTTP integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from aiohttp import web
            from aiohttp.web_middlewares import middleware
            from opentelemetry.instrumentation.aiohttp_client import (
                AioHttpClientInstrumentor,
            )
            from opentelemetry.instrumentation.aiohttp_server import (
                AioHttpServerInstrumentor,
            )

            @middleware
            async def telescope_middleware(request, handler):
                """AioHTTP middleware for Telescope."""
                try:
                    response = await handler(request)
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
                        "user_agent": request.headers.get("User-Agent", ""),
                    }

                    extra = {
                        "request": {
                            "url": str(request.url),
                            "method": request.method,
                            "headers": dict(request.headers),
                            "query_string": dict(request.query),
                        }
                    }

                    event_id = client.capture_exception(
                        e,
                        tags=tags,
                        extra=extra,
                        user=user_context,
                    )

                    # Return error response with Telescope event ID
                    return web.Response(
                        text=f"Internal server error (Event ID: {event_id})", status=500
                    )

            def init_app(app: web.Application):
                """Initialize AioHTTP app with Telescope."""
                # Instrument AioHTTP server
                AioHttpServerInstrumentor().instrument()

                # Instrument AioHTTP client
                AioHttpClientInstrumentor().instrument()

                # Add Telescope middleware
                app.middlewares.append(telescope_middleware)

            return init_app

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("AioHTTP not found, skipping AioHTTP integration") from e


def setup_aiohttp_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return AioHttpIntegration().setup(client)
