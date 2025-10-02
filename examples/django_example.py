"""
Django Example with Telescope and OpenTelemetry Integration
"""

# settings.py
import os
from telescope_client import TelescopeClient, setup_django_integration

# Telescope Configuration
TELESCOPE_CLIENT = TelescopeClient(
    dsn=os.getenv("TELESCOPE_DSN", "http://localhost:8080"),
    project_id=os.getenv("TELESCOPE_PROJECT_ID", "TS-123456"),
    environment=os.getenv("ENVIRONMENT", "development"),
    api_key=os.getenv("TELESCOPE_API_KEY"),
    enable_tracing=True,
    enable_performance=True,
    sample_rate=1.0 if os.getenv("ENVIRONMENT") == "production" else 0.5,
    otlp_endpoint=os.getenv("OTLP_ENDPOINT"),  # Optional: send to OTEL collector
)

# Setup Django integration (automatic error capture)
setup_django_integration(TELESCOPE_CLIENT)

# OpenTelemetry Django settings
INSTALLED_APPS = [
    # ... your apps
    "opentelemetry.instrumentation.django",
]

# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from telescope_client import capture_errors, trace_function, set_user_context, set_tags
from opentelemetry import trace
import json

tracer = trace.get_tracer(__name__)


@require_http_methods(["POST"])
@capture_errors(tags={"component": "payment"})
def process_payment(request):
    """Process payment with automatic error capture and tracing."""

    # Set user context for error reporting
    if request.user.is_authenticated:
        set_user_context(
            user_id=str(request.user.id),
            username=request.user.username,
            email=request.user.email,
        )

    # Set request-specific tags
    set_tags(
        endpoint="process_payment",
        method=request.method,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    with tracer.start_span("payment.process") as span:
        try:
            data = json.loads(request.body)
            amount = data.get("amount")
            currency = data.get("currency", "USD")

            # Add span attributes
            span.set_attributes(
                {
                    "payment.amount": amount,
                    "payment.currency": currency,
                    "payment.user_id": str(request.user.id)
                    if request.user.is_authenticated
                    else None,
                }
            )

            # Validate payment
            if not amount or amount <= 0:
                raise ValueError("Invalid payment amount")

            # Process payment (this will be traced automatically)
            result = charge_payment(amount, currency)

            span.set_attribute("payment.transaction_id", result["transaction_id"])
            span.set_attribute("payment.success", True)

            return JsonResponse(
                {
                    "success": True,
                    "transaction_id": result["transaction_id"],
                    "amount": amount,
                    "currency": currency,
                }
            )

        except ValueError as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            return JsonResponse({"error": str(e)}, status=400)

        except Exception as e:
            # This will be automatically captured by @capture_errors
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


@trace_function(tags={"component": "payment", "external_service": True})
def charge_payment(amount, currency):
    """Charge payment via external service."""
    import time

    # Simulate external API call
    with tracer.start_span("payment.external_api") as span:
        span.set_attributes(
            {
                "http.method": "POST",
                "http.url": "https://api.stripe.com/v1/charges",
                "payment.amount": amount,
                "payment.currency": currency,
            }
        )

        # Simulate processing time
        time.sleep(0.1)

        # Simulate occasional failures
        import random

        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Payment gateway timeout")

        transaction_id = f"txn_{int(time.time())}"
        span.set_attribute("payment.transaction_id", transaction_id)

        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "amount": amount,
            "currency": currency,
        }


# models.py
from django.db import models
from telescope_client import performance_monitor


class PaymentModel(models.Model):
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    @performance_monitor(threshold_ms=100, tags={"model": "Payment"})
    def save(self, *args, **kwargs):
        """Save with performance monitoring."""
        super().save(*args, **kwargs)

    @classmethod
    @trace_function(tags={"component": "database"}, capture_args=True)
    def get_recent_payments(cls, user_id, days=30):
        """Get recent payments with tracing."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        return cls.objects.filter(
            user_id=user_id, created_at__gte=cutoff_date
        ).order_by("-created_at")


# middleware.py
from telescope_client.context import TelescopeContextMiddleware


class TelescopeMiddleware:
    """Django middleware for Telescope context management."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.telescope_middleware = TelescopeContextMiddleware(TELESCOPE_CLIENT)

    def __call__(self, request):
        # Set up Telescope context
        self.telescope_middleware(request, None)

        response = self.get_response(request)
        return response


# Add to MIDDLEWARE in settings.py
MIDDLEWARE = [
    "myapp.middleware.TelescopeMiddleware",
    # ... other middleware
]


# management/commands/test_telescope.py
from django.core.management.base import BaseCommand
from telescope_client import set_tags, capture_errors
import time


class Command(BaseCommand):
    help = "Test Telescope integration"

    @capture_errors(tags={"component": "management_command"})
    def handle(self, *args, **options):
        """Test command with error capture."""

        set_tags(
            command="test_telescope",
            environment="test",
        )

        self.stdout.write("Testing Telescope integration...")

        # Test successful operation
        with tracer.start_span("test.success") as span:
            span.set_attribute("test.type", "success")
            self.stdout.write("✓ Success test passed")

        # Test performance monitoring
        @performance_monitor(threshold_ms=50)
        def slow_operation():
            time.sleep(0.1)  # This will trigger performance alert

        slow_operation()
        self.stdout.write("✓ Performance monitoring test completed")

        # Test error capture
        try:
            raise ValueError("This is a test error")
        except ValueError as e:
            TELESCOPE_CLIENT.capture_exception(
                e, tags={"test": True}, extra={"command": "test_telescope"}
            )
            self.stdout.write("✓ Error capture test completed")

        # Test message capture
        TELESCOPE_CLIENT.capture_message(
            "Telescope integration test completed successfully",
            level="info",
            tags={"test": True, "component": "management_command"},
        )

        self.stdout.write(
            self.style.SUCCESS("All Telescope tests completed successfully!")
        )
