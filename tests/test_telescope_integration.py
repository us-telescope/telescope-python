#!/usr/bin/env python3
"""
Test script to verify Telescope Python client integration with the server.
"""

import time
import sys
import os

# Add the telescope-python-client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "telescope-python-client"))

from telescope import TelescopeClient, set_user_context, capture_errors
from telescope_client.context import set_client
from opentelemetry import trace


def test_telescope_integration():
    """Test the Telescope Python client with the running server."""

    print("🔭 Testing Telescope Python Client Integration")
    print("=" * 50)

    # Initialize the client
    client = TelescopeClient(
        dsn="http://localhost:8080",
        project_id="TS-438154",  # Use existing project
        environment="development",
    )

    # Set as global client for decorators
    set_client(client)

    print(f"✅ Client initialized with project_id: {client.project_id}")
    print(f"✅ DSN: {client.dsn}")
    print(f"✅ Environment: {client.environment}")

    # Test 1: Capture a simple exception
    print("\n📝 Test 1: Capturing a simple exception...")
    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        event_id = client.capture_exception(
            e, extra={"test_type": "division_by_zero", "test_number": 1}
        )
        print(f"✅ Exception captured with event_id: {event_id}")

    # Test 2: Capture a message
    print("\n📝 Test 2: Capturing a message...")
    event_id = client.capture_message(
        "Test message from Python client",
        level="info",
        extra={"test_type": "message_capture", "test_number": 2},
    )
    print(f"✅ Message captured with event_id: {event_id}")

    # Test 3: Capture with user context
    print("\n📝 Test 3: Capturing with user context...")
    set_user_context(
        user_id="test-user-123", email="test@example.com", username="testuser"
    )

    try:
        # Simulate another error
        data = {"key": "value"}
        result = data["nonexistent_key"]
    except KeyError as e:
        event_id = client.capture_exception(
            e,
            extra={
                "test_type": "key_error",
                "test_number": 3,
                "data_keys": list(data.keys()),
            },
        )
        print(f"✅ Exception with user context captured with event_id: {event_id}")

    # Test 4: Capture with tags and extra context
    print("\n📝 Test 4: Capturing with tags and extra context...")

    try:
        # Simulate authentication error
        raise ValueError("Invalid credentials provided")
    except ValueError as e:
        event_id = client.capture_exception(
            e,
            tags={"component": "auth", "severity": "high"},
            extra={
                "test_type": "auth_error",
                "test_number": 4,
                "login_attempt": "failed",
            },
        )
        print(
            f"✅ Exception with tags and extra context captured with event_id: {event_id}"
        )

    # Test 5: Test decorator
    print("\n📝 Test 5: Testing decorator...")

    @capture_errors(tags={"component": "math"}, reraise=False)
    def risky_function(x, y):
        """A function that might fail."""
        if y == 0:
            raise ValueError("Cannot divide by zero in risky_function")
        return x / y

    # This should be captured automatically
    result = risky_function(10, 0)
    print("✅ Decorator captured the exception automatically")

    # Test 6: Performance monitoring
    print("\n📝 Test 6: Testing performance monitoring...")

    with client.start_transaction("test_transaction") as transaction:
        # Simulate some work
        time.sleep(0.1)

        # Create child spans using OpenTelemetry tracer
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("database_query") as span:
            span.set_attribute("db.statement", "SELECT * FROM users")
            time.sleep(0.05)

        with tracer.start_as_current_span("api_call") as span:
            span.set_attribute("http.method", "GET")
            span.set_attribute("http.url", "https://api.example.com/data")
            time.sleep(0.03)

    print("✅ Performance transaction completed")

    print("\n🎉 All tests completed successfully!")
    print("\n📊 Check your Telescope dashboard at: http://localhost:8080")
    print("   You should see 4-5 new events in the TEST-PYTHON-CLIENT project")


if __name__ == "__main__":
    # Wait a bit for the server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)

    try:
        test_telescope_integration()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
