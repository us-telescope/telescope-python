"""
Flask integration for Telescope
"""

from ..client import TelescopeClient


class FlaskIntegration:
    """
    Flask integration for Telescope client.

    Automatically captures exceptions and provides tracing for Flask applications.

    Example:
        from telescope import TelescopeClient
        from telescope.integrations.flask import FlaskIntegration

        client = TelescopeClient(
            dsn="http://localhost:8080",
            project_id="MY-PROJECT",
            enable_tracing=True
        )

        # Setup Flask integration
        FlaskIntegration().setup(client)
    """

    def __init__(self, **options):
        """
        Initialize Flask integration.

        Args:
            **options: Additional options for Flask integration
        """
        self.options = options

    def setup(self, client: TelescopeClient):
        """
        Setup Flask integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from flask import Flask, g, request
            from opentelemetry.instrumentation.flask import FlaskInstrumentor
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            def init_app(app: Flask):
                """Initialize Flask app with Telescope."""

                # Instrument Flask
                FlaskInstrumentor().instrument_app(app)

                # Instrument SQLAlchemy if available
                try:
                    SQLAlchemyInstrumentor().instrument()
                except Exception:
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
                        "url": request.path,
                        "method": request.method,
                        "user_agent": request.headers.get("User-Agent", ""),
                    }

                    extra = {
                        "request": {
                            "url": request.url,
                            "method": request.method,
                            "headers": dict(request.headers),
                            "data": request.get_json() if request.is_json else {},
                            "args": request.args,
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


def setup_flask_integration(client: TelescopeClient):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    FlaskIntegration().setup(client)
