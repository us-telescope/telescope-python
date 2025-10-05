"""
Requests integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor

if TYPE_CHECKING:
    from ..client import TelescopeClient


class RequestsIntegration:
    """
    Requests integration for Telescope client.

    Automatically captures HTTP errors and provides tracing for Requests operations.
    """

    identifier = "requests"

    def __init__(self, **options: Any):
        """Initialize Requests integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Requests integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from requests import Session

            def init_requests():
                """Initialize Requests with Telescope."""

                # Instrument Requests
                RequestsInstrumentor().instrument()

                # Monkey patch Session methods to capture errors
                original_request = Session.request

                def request_with_telescope(self, method, url, **kwargs):
                    """Make HTTP request with Telescope tracing."""
                    with client.tracer.start_span("http.request") as span:
                        span.set_attributes(
                            {
                                "http.method": method.upper(),
                                "http.url": url,
                                "http.scheme": url.split("://")[0]
                                if "://" in url
                                else "http",
                            }
                        )

                        try:
                            response = original_request(self, method, url, **kwargs)

                            span.set_attributes(
                                {
                                    "http.status_code": response.status_code,
                                    "http.response.status_code": response.status_code,
                                }
                            )

                            if response.status_code >= 400:
                                span.set_status(
                                    trace.Status(
                                        trace.StatusCode.ERROR,
                                        f"HTTP {response.status_code}",
                                    )
                                )

                                # Capture HTTP errors as Telescope events
                                tags = {
                                    "http.method": method.upper(),
                                    "http.url": url,
                                    "http.status_code": str(response.status_code),
                                }

                                extra = {
                                    "http": {
                                        "method": method.upper(),
                                        "url": url,
                                        "status_code": response.status_code,
                                        "headers": dict(response.headers),
                                        "response_text": response.text[
                                            :1000
                                        ],  # Limit response text
                                    }
                                }

                                client.capture_message(
                                    f"HTTP {response.status_code} error",
                                    level="error",
                                    tags=tags,
                                    extra=extra,
                                )
                            else:
                                span.set_status(trace.Status(trace.StatusCode.OK))

                            return response

                        except Exception as e:
                            span.set_status(
                                trace.Status(trace.StatusCode.ERROR, str(e))
                            )

                            tags = {
                                "http.method": method.upper(),
                                "http.url": url,
                            }

                            extra = {
                                "http": {
                                    "method": method.upper(),
                                    "url": url,
                                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                                }
                            }

                            client.capture_exception(
                                e,
                                tags=tags,
                                extra=extra,
                            )
                            raise

                # Apply monkey patch
                Session.request = request_with_telescope

            return init_requests

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable(
                "Requests not found, skipping Requests integration"
            ) from e


def setup_requests_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return RequestsIntegration().setup(client)
