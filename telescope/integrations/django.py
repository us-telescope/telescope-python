"""
Django integration for Telescope
"""

from ..client import TelescopeClient


class DjangoIntegration:
    """
    Django integration for Telescope client.

    Automatically captures exceptions and provides tracing for Django applications.

    Example:
        from telescope import TelescopeClient
        from telescope.integrations.django import DjangoIntegration

        client = TelescopeClient(
            dsn="http://localhost:8080",
            project_id="MY-PROJECT",
            enable_tracing=True
        )

        # Setup Django integration
        DjangoIntegration().setup(client)
    """

    def __init__(self, **options):
        """
        Initialize Django integration.

        Args:
            **options: Additional options for Django integration
        """
        self.options = options

    def setup(self, client: TelescopeClient):
        """
        Setup Django integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from django.core.signals import got_request_exception
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

            # Instrument Django
            DjangoInstrumentor().instrument()
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


def setup_django_integration(client: TelescopeClient):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    DjangoIntegration().setup(client)
