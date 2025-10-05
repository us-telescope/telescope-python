"""
SQLAlchemy integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import TelescopeClient


class SQLAlchemyIntegration:
    """
    SQLAlchemy integration for Telescope client.

    Automatically captures database errors and provides tracing for SQLAlchemy operations.
    """

    identifier = "sqlalchemy"

    def __init__(self, **options: Any):
        """Initialize SQLAlchemy integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup SQLAlchemy integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            from sqlalchemy import event
            from sqlalchemy.engine import Engine

            def init_engine(engine: Engine):
                """Initialize SQLAlchemy engine with Telescope."""

                # Instrument SQLAlchemy
                SQLAlchemyInstrumentor().instrument()

                @event.listens_for(Engine, "connect")
                def receive_connect(dbapi_connection, connection_record):
                    """Handle database connection events."""
                    with client.tracer.start_span("sqlalchemy.connect") as span:
                        span.set_attributes(
                            {
                                "db.system": "sqlalchemy",
                                "db.connection_string": str(engine.url).replace(
                                    engine.url.password or "", "***"
                                )
                                if engine.url.password
                                else str(engine.url),
                            }
                        )

                @event.listens_for(Engine, "before_cursor_execute")
                def receive_before_cursor_execute(
                    conn, cursor, statement, parameters, context, executemany
                ):
                    """Handle before cursor execute events."""
                    context._telescope_span = client.tracer.start_span(
                        "sqlalchemy.query"
                    )
                    context._telescope_span.set_attributes(
                        {
                            "db.statement": statement,
                            "db.system": "sqlalchemy",
                        }
                    )

                @event.listens_for(Engine, "after_cursor_execute")
                def receive_after_cursor_execute(
                    conn, cursor, statement, parameters, context, executemany
                ):
                    """Handle after cursor execute events."""
                    if hasattr(context, "_telescope_span"):
                        context._telescope_span.end()

                @event.listens_for(Engine, "handle_error")
                def receive_handle_error(exception_context):
                    """Handle database errors."""
                    exception = exception_context.original_exception

                    tags = {
                        "db.system": "sqlalchemy",
                        "db.operation": getattr(exception_context, "statement", ""),
                    }

                    extra = {
                        "database": {
                            "statement": getattr(exception_context, "statement", ""),
                            "parameters": getattr(exception_context, "parameters", ""),
                        }
                    }

                    client.capture_exception(
                        exception,
                        tags=tags,
                        extra=extra,
                    )

            return init_engine

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable(
                "SQLAlchemy not found, skipping SQLAlchemy integration"
            ) from e


def setup_sqlalchemy_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return SQLAlchemyIntegration().setup(client)
