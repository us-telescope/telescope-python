"""
OpenAI integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

if TYPE_CHECKING:
    from ..client import TelescopeClient


class OpenAIIntegration:
    """
    OpenAI integration for Telescope client.

    Automatically captures OpenAI API errors and provides tracing for OpenAI operations.
    """

    identifier = "openai"

    def __init__(self, **options: Any):
        """Initialize OpenAI integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup OpenAI integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from openai import OpenAI

            def init_openai(openai_client: OpenAI):
                """Initialize OpenAI client with Telescope."""

                # Instrument OpenAI
                OpenAIInstrumentor().instrument()

                # Monkey patch OpenAI client methods to capture errors
                original_chat_completions_create = openai_client.chat.completions.create
                original_completions_create = openai_client.completions.create
                original_embeddings_create = openai_client.embeddings.create

                def chat_completions_create_with_telescope(*args, **kwargs):
                    """Create chat completion with Telescope tracing."""
                    with client.tracer.start_span("openai.chat.completion") as span:
                        span.set_attributes(
                            {
                                "openai.operation": "chat.completion",
                                "openai.model": kwargs.get("model", "unknown"),
                            }
                        )

                        try:
                            result = original_chat_completions_create(*args, **kwargs)
                            span.set_status(trace.Status(trace.StatusCode.OK))
                            return result
                        except Exception as e:
                            span.set_status(
                                trace.Status(trace.StatusCode.ERROR, str(e))
                            )

                            tags = {
                                "openai.operation": "chat.completion",
                                "openai.model": kwargs.get("model", "unknown"),
                            }

                            extra = {
                                "openai": {
                                    "model": kwargs.get("model"),
                                    "messages": kwargs.get("messages", []),
                                    "temperature": kwargs.get("temperature"),
                                    "max_tokens": kwargs.get("max_tokens"),
                                }
                            }

                            client.capture_exception(
                                e,
                                tags=tags,
                                extra=extra,
                            )
                            raise

                def completions_create_with_telescope(*args, **kwargs):
                    """Create completion with Telescope tracing."""
                    with client.tracer.start_span("openai.completion") as span:
                        span.set_attributes(
                            {
                                "openai.operation": "completion",
                                "openai.model": kwargs.get("model", "unknown"),
                            }
                        )

                        try:
                            result = original_completions_create(*args, **kwargs)
                            span.set_status(trace.Status(trace.StatusCode.OK))
                            return result
                        except Exception as e:
                            span.set_status(
                                trace.Status(trace.StatusCode.ERROR, str(e))
                            )

                            tags = {
                                "openai.operation": "completion",
                                "openai.model": kwargs.get("model", "unknown"),
                            }

                            extra = {
                                "openai": {
                                    "model": kwargs.get("model"),
                                    "prompt": kwargs.get("prompt", ""),
                                    "temperature": kwargs.get("temperature"),
                                    "max_tokens": kwargs.get("max_tokens"),
                                }
                            }

                            client.capture_exception(
                                e,
                                tags=tags,
                                extra=extra,
                            )
                            raise

                def embeddings_create_with_telescope(*args, **kwargs):
                    """Create embedding with Telescope tracing."""
                    with client.tracer.start_span("openai.embedding") as span:
                        span.set_attributes(
                            {
                                "openai.operation": "embedding",
                                "openai.model": kwargs.get("model", "unknown"),
                            }
                        )

                        try:
                            result = original_embeddings_create(*args, **kwargs)
                            span.set_status(trace.Status(trace.StatusCode.OK))
                            return result
                        except Exception as e:
                            span.set_status(
                                trace.Status(trace.StatusCode.ERROR, str(e))
                            )

                            tags = {
                                "openai.operation": "embedding",
                                "openai.model": kwargs.get("model", "unknown"),
                            }

                            extra = {
                                "openai": {
                                    "model": kwargs.get("model"),
                                    "input": kwargs.get("input", ""),
                                }
                            }

                            client.capture_exception(
                                e,
                                tags=tags,
                                extra=extra,
                            )
                            raise

                # Apply monkey patches
                openai_client.chat.completions.create = (
                    chat_completions_create_with_telescope
                )
                openai_client.completions.create = completions_create_with_telescope
                openai_client.embeddings.create = embeddings_create_with_telescope

            return init_openai

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("OpenAI not found, skipping OpenAI integration") from e


def setup_openai_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return OpenAIIntegration().setup(client)
