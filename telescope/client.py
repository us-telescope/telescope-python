"""
Telescope Client with OpenTelemetry Integration
"""

import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class TelescopeClient:
    """
    Main Telescope client with OpenTelemetry integration.

    Features:
    - Error tracking with trace correlation
    - Performance monitoring
    - Environment-aware reporting
    - Automatic context enrichment
    """

    def __init__(
        self,
        dsn: str,
        project_id: str,
        environment: str = "production",
        api_key: Optional[str] = None,
        enable_tracing: bool = True,
        enable_performance: bool = True,
        sample_rate: float = 1.0,
        otlp_endpoint: Optional[str] = None,
    ):
        """
        Initialize Telescope client.

        Args:
            dsn: Telescope server endpoint
            project_id: Project identifier
            environment: Environment name (production, staging, development)
            api_key: API key for authentication
            enable_tracing: Enable OpenTelemetry tracing
            enable_performance: Enable performance monitoring
            sample_rate: Error sampling rate (0.0 to 1.0)
            otlp_endpoint: OpenTelemetry collector endpoint
        """
        # Import required modules
        import requests
        from opentelemetry import trace
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        self.dsn = dsn.rstrip("/")
        self.project_id = project_id
        self.environment = environment
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.enable_tracing = enable_tracing
        self.enable_performance = enable_performance

        # Initialize OpenTelemetry
        if enable_tracing:
            self._setup_tracing(otlp_endpoint)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        # Setup HTTP session
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

        # Instrument requests
        if enable_tracing:
            RequestsInstrumentor().instrument()

    def _setup_tracing(self, otlp_endpoint: Optional[str]):
        """Setup OpenTelemetry tracing."""
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        trace.set_tracer_provider(TracerProvider())

        if otlp_endpoint:
            # Export to OTLP collector
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

    def capture_exception(
        self,
        exception: Exception,
        level: str = "error",
        tags: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
        user: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[List[str]] = None,
    ) -> str:
        """
        Capture an exception with OpenTelemetry context.

        Args:
            exception: The exception to capture
            level: Error level (error, warning, info, debug, fatal)
            tags: Additional tags
            extra: Extra context data
            user: User information
            fingerprint: Custom fingerprint for grouping

        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())

        # Get current span and trace context
        from opentelemetry import trace
        from opentelemetry.trace import Status, StatusCode

        current_span = trace.get_current_span()
        trace_id = None
        span_id = None

        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")

            # Record exception in span
            current_span.record_exception(exception)
            current_span.set_status(Status(StatusCode.ERROR, str(exception)))

        # Build event payload
        event_data = {
            "event_id": event_id,
            "project_id": self.project_id,
            "environment_id": self._get_environment_id(),
            "level": level,
            "event_type": "error",
            "message": str(exception),
            "exception_type": exception.__class__.__name__,
            "stack_trace": self._format_stacktrace(exception),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "contexts": {
                "trace": {
                    "trace_id": trace_id,
                    "span_id": span_id,
                }
                if trace_id
                else {},
                "runtime": self._get_runtime_context(),
            },
            "tags": tags or {},
            "extra": extra or {},
            "user": user or {},
        }

        # Add OpenTelemetry baggage
        from opentelemetry import baggage

        baggage_items = baggage.get_all()
        if baggage_items:
            event_data["contexts"]["baggage"] = dict(baggage_items)

        # Add fingerprint if provided
        if fingerprint:
            event_data["fingerprint"] = fingerprint

        # Send to Telescope
        self._send_event(event_data)

        return event_id

    def capture_message(
        self,
        message: str,
        level: str = "info",
        tags: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Capture a message event.

        Args:
            message: The message to capture
            level: Message level
            tags: Additional tags
            extra: Extra context data

        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())

        # Get trace context
        from opentelemetry import trace

        current_span = trace.get_current_span()
        trace_id = None
        span_id = None

        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")

        event_data = {
            "event_id": event_id,
            "project_id": self.project_id,
            "environment_id": self._get_environment_id(),
            "level": level,
            "event_type": "message",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "contexts": {
                "trace": {
                    "trace_id": trace_id,
                    "span_id": span_id,
                }
                if trace_id
                else {},
                "runtime": self._get_runtime_context(),
            },
            "tags": tags or {},
            "extra": extra or {},
        }

        self._send_event(event_data)
        return event_id

    def start_transaction(self, name: str, op: str = "http.server"):
        """
        Start a new transaction (root span).

        Args:
            name: Transaction name
            op: Operation type

        Returns:
            OpenTelemetry span
        """

        span = self.tracer.start_span(
            name,
            attributes={
                "telescope.transaction": True,
                "telescope.op": op,
                "telescope.project_id": self.project_id,
                "telescope.environment": self.environment,
            },
        )
        return span

    def _get_environment_id(self) -> Optional[int]:
        """Get environment ID from cache or API."""
        # This would typically be cached
        # For now, return None and let server handle it
        return None

    def _format_stacktrace(self, exception: Exception) -> List[Dict[str, Any]]:
        """Format exception stacktrace for Telescope."""
        tb = traceback.extract_tb(exception.__traceback__)
        frames = []

        for frame in tb:
            frames.append(
                {
                    "filename": frame.filename,
                    "function": frame.name,
                    "lineno": frame.lineno,
                    "colno": 0,
                    "context_line": frame.line,
                    "pre_context": [],
                    "post_context": [],
                    "in_app": not frame.filename.startswith("/"),
                }
            )

        return frames

    def _get_runtime_context(self) -> Dict[str, Any]:
        """Get runtime context information."""
        import platform
        import sys

        return {
            "name": "python",
            "version": sys.version,
            "build": platform.python_build(),
            "platform": platform.platform(),
        }

    def _send_event(self, event_data: Dict[str, Any]):
        """Send event to Telescope server."""
        try:
            from opentelemetry.trace import Status, StatusCode

            with self.tracer.start_span("telescope.send_event") as span:
                span.set_attributes(
                    {
                        "telescope.event_id": event_data["event_id"],
                        "telescope.level": event_data["level"],
                        "telescope.event_type": event_data["event_type"],
                    }
                )

                response = self.session.post(
                    f"{self.dsn}/api/v1/events/",
                    json=event_data,
                    timeout=10,
                )

                if response.status_code not in (200, 201, 202):
                    span.set_status(
                        Status(StatusCode.ERROR, f"HTTP {response.status_code}")
                    )
                    print(f"Failed to send event to Telescope: {response.status_code}")
                else:
                    span.set_status(Status(StatusCode.OK))

        except Exception as e:
            print(f"Error sending event to Telescope: {e}")

    def flush(self, timeout: float = 2.0):
        """Flush any pending events."""
        if self.enable_tracing:
            from opentelemetry import trace

            # Force flush spans
            trace.get_tracer_provider().force_flush(timeout_millis=int(timeout * 1000))

    def close(self):
        """Close the client and cleanup resources."""
        self.flush()
        if hasattr(self, "session"):
            self.session.close()
