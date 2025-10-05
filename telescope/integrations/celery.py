"""
Celery integration for Telescope client.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import TelescopeClient


class CeleryIntegration:
    """
    Celery integration for Telescope client.

    Automatically captures Celery task errors and provides tracing for Celery operations.
    """

    identifier = "celery"

    def __init__(self, **options: Any):
        """Initialize Celery integration."""
        self.options = options

    def setup(self, client: "TelescopeClient"):
        """
        Setup Celery integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        try:
            from celery import Celery
            from celery.signals import task_failure, task_postrun, task_prerun
            from opentelemetry import trace
            from opentelemetry.instrumentation.celery import CeleryInstrumentor

            def init_celery(celery_app: Celery):
                """Initialize Celery app with Telescope."""

                # Instrument Celery
                CeleryInstrumentor().instrument()

                @task_prerun.connect
                def task_prerun_handler(
                    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds
                ):
                    """Handle task prerun events."""
                    with client.tracer.start_span("celery.task") as span:
                        span.set_attributes(
                            {
                                "celery.task.name": task.name,
                                "celery.task.id": task_id,
                                "celery.task.args": str(args) if args else "",
                                "celery.task.kwargs": str(kwargs) if kwargs else "",
                            }
                        )
                        # Store span in task context for later use
                        if hasattr(task, "request"):
                            task.request._telescope_span = span

                @task_postrun.connect
                def task_postrun_handler(
                    sender=None,
                    task_id=None,
                    task=None,
                    args=None,
                    kwargs=None,
                    retval=None,
                    state=None,
                    **kwds,
                ):
                    """Handle task postrun events."""
                    if hasattr(task, "request") and hasattr(
                        task.request, "_telescope_span"
                    ):
                        task.request._telescope_span.set_status(
                            trace.Status(trace.StatusCode.OK)
                        )
                        task.request._telescope_span.end()

                @task_failure.connect
                def task_failure_handler(
                    sender=None,
                    task_id=None,
                    exception=None,
                    traceback=None,
                    einfo=None,
                    **kwds,
                ):
                    """Handle task failure events."""
                    if hasattr(sender, "request") and hasattr(
                        sender.request, "_telescope_span"
                    ):
                        sender.request._telescope_span.set_status(
                            trace.Status(trace.StatusCode.ERROR, str(exception))
                        )
                        sender.request._telescope_span.end()

                    # Extract task context
                    task_context = {}
                    if hasattr(sender, "request"):
                        task_context = {
                            "task_id": task_id,
                            "task_name": sender.name,
                            "args": str(sender.request.args)
                            if hasattr(sender.request, "args")
                            else "",
                            "kwargs": str(sender.request.kwargs)
                            if hasattr(sender.request, "kwargs")
                            else "",
                        }

                    tags = {
                        "celery.task.name": sender.name,
                        "celery.task.id": task_id,
                    }

                    extra = {
                        "celery": task_context,
                    }

                    client.capture_exception(
                        exception,
                        tags=tags,
                        extra=extra,
                    )

            return init_celery

        except ImportError as e:
            from ..integrations.base import DidNotEnable

            raise DidNotEnable("Celery not found, skipping Celery integration") from e


def setup_celery_integration(client: "TelescopeClient"):
    """
    Legacy function for backward compatibility.

    Args:
        client: TelescopeClient instance
    """
    return CeleryIntegration().setup(client)
