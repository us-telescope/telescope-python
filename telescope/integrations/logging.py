"""
Logging integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import TelescopeClient


class LoggingIntegration:
    """
    Logging integration for Telescope client.

    Automatically captures log messages and provides tracing for Python logging.
    """

    identifier = "logging"

    def __init__(self, **options: Any):
        """Initialize Logging integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Logging integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            import logging
            from logging import LogRecord

            from opentelemetry.instrumentation.logging import LoggingInstrumentor

            # Instrument logging
            LoggingInstrumentor().instrument()

            # Create custom log handler
            class TelescopeLogHandler(logging.Handler):
                """Custom log handler that sends logs to Telescope."""

                def __init__(self, client: "TelescopeClient"):
                    super().__init__()
                    self.client = client

                def emit(self, record: LogRecord):
                    """Emit log record to Telescope."""
                    try:
                        # Map log levels to Telescope levels
                        level_mapping = {
                            logging.DEBUG: "debug",
                            logging.INFO: "info",
                            logging.WARNING: "warning",
                            logging.ERROR: "error",
                            logging.CRITICAL: "fatal",
                        }

                        telescope_level = level_mapping.get(record.levelno, "info")

                        # Extract context from log record
                        extra = {
                            "logging": {
                                "logger_name": record.name,
                                "module": record.module,
                                "filename": record.filename,
                                "lineno": record.lineno,
                                "funcName": record.funcName,
                                "pathname": record.pathname,
                                "process": record.process,
                                "thread": record.thread,
                                "threadName": record.threadName,
                            }
                        }

                        # Add exception info if available
                        if record.exc_info:
                            extra["logging"]["exc_info"] = self.format(record)

                        # Add extra fields from log record
                        if hasattr(record, "extra_fields"):
                            extra["logging"]["extra_fields"] = record.extra_fields

                        # Send to Telescope
                        if telescope_level in ["error", "fatal"]:
                            # For error and fatal levels, capture as exceptions
                            if record.exc_info:
                                exc_type, exc_value, exc_traceback = record.exc_info
                                self.client.capture_exception(
                                    exc_value,
                                    level=telescope_level,
                                    extra=extra,
                                )
                            else:
                                # Create a synthetic exception for error logs
                                class LogError(Exception):
                                    pass

                                log_error = LogError(record.getMessage())
                                self.client.capture_exception(
                                    log_error,
                                    level=telescope_level,
                                    extra=extra,
                                )
                        else:
                            # For other levels, capture as messages
                            self.client.capture_message(
                                record.getMessage(),
                                level=telescope_level,
                                extra=extra,
                            )

                    except Exception:
                        # Don't let Telescope errors break logging
                        pass

            # Add Telescope handler to root logger
            telescope_handler = TelescopeLogHandler(client)
            telescope_handler.setLevel(logging.ERROR)  # Only capture ERROR and above
            logging.getLogger().addHandler(telescope_handler)

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("Logging not found, skipping Logging integration") from e


def setup_logging_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return LoggingIntegration().setup(client)
