"""
Redis integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import TelescopeClient


class RedisIntegration:
    """
    Redis integration for Telescope client.

    Automatically captures Redis errors and provides tracing for Redis operations.
    """

    identifier = "redis"

    def __init__(self, **options: Any):
        """Initialize Redis integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Redis integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from opentelemetry import trace
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            from redis import Redis

            def init_redis(redis_client: Redis):
                """Initialize Redis client with Telescope."""

                # Instrument Redis
                RedisInstrumentor().instrument()

                # Monkey patch Redis client to capture errors
                original_execute_command = redis_client.execute_command

                def execute_command_with_telescope(*args, **kwargs):
                    """Execute Redis command with Telescope tracing."""
                    command = args[0] if args else "unknown"

                    with client.tracer.start_span("redis.command") as span:
                        span.set_attributes(
                            {
                                "db.system": "redis",
                                "db.operation": command,
                                "db.redis.command": command,
                            }
                        )

                        try:
                            result = original_execute_command(*args, **kwargs)
                            span.set_status(trace.Status(trace.StatusCode.OK))
                            return result
                        except Exception as e:
                            span.set_status(
                                trace.Status(trace.StatusCode.ERROR, str(e))
                            )

                            tags = {
                                "db.system": "redis",
                                "db.operation": command,
                            }

                            extra = {
                                "redis": {
                                    "command": command,
                                    "args": args[1:] if len(args) > 1 else [],
                                    "kwargs": kwargs,
                                }
                            }

                            client.capture_exception(
                                e,
                                tags=tags,
                                extra=extra,
                            )
                            raise

                redis_client.execute_command = execute_command_with_telescope

            return init_redis

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("Redis not found, skipping Redis integration") from e


def setup_redis_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return RedisIntegration().setup(client)
