#!/usr/bin/env python3
"""
Fixed integration test with correct payload format for Telescope server.
"""

import time
import sys
import os
import json
import traceback

# Add the telescope-python-client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "telescope-python-client"))

from telescope import TelescopeClient, set_user_context
from telescope_client.context import set_client
from opentelemetry import trace


class FixedTelescopeClient(TelescopeClient):
    """
    Fixed Telescope client that sends the correct payload format.
    """

    def _send_event(self, event_data):
        """Send event to Telescope server with correct format."""
        try:
            # Transform the payload to match server expectations
            server_payload = {
                "project_id": event_data["project_id"],
                "event_type": event_data.get("event_type", "error"),
                "level": event_data.get("level", "error"),
                "message": event_data.get("message", ""),
                "timestamp": event_data.get("timestamp"),
            }

            # Add optional fields if present
            if "exception_type" in event_data:
                server_payload["exception_type"] = event_data["exception_type"]

            if "stack_trace" in event_data:
                server_payload["stack_trace"] = event_data["stack_trace"]

            # Convert contexts to context (single)
            if "contexts" in event_data:
                server_payload["context"] = event_data["contexts"]

            # Add other optional fields
            optional_fields = [
                "user_id",
                "session_id",
                "url",
                "user_agent",
                "environment_id",
            ]
            for field in optional_fields:
                if field in event_data:
                    server_payload[field] = event_data[field]

            # Merge tags and extra into context
            if not server_payload.get("context"):
                server_payload["context"] = {}

            if event_data.get("tags"):
                server_payload["context"]["tags"] = event_data["tags"]

            if event_data.get("extra"):
                server_payload["context"]["extra"] = event_data["extra"]

            if event_data.get("user"):
                server_payload["context"]["user"] = event_data["user"]

            print(
                f"📤 Sending payload: {json.dumps(server_payload, indent=2, default=str)}"
            )

            with self.tracer.start_span("telescope.send_event") as span:
                span.set_attributes(
                    {
                        "telescope.event_id": event_data.get("event_id", "unknown"),
                        "telescope.level": server_payload["level"],
                        "telescope.event_type": server_payload["event_type"],
                    }
                )

                response = self.session.post(
                    f"{self.dsn}/api/v1/events/",
                    json=server_payload,
                    timeout=10,
                )

                if response.status_code not in (200, 201, 202):
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR, f"HTTP {response.status_code}"
                        )
                    )
                    print(f"❌ Failed to send event: {response.status_code}")
                    print(f"Response: {response.text}")
                else:
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    print(f"✅ Event sent successfully: {response.status_code}")
                    print(f"Response: {response.text}")

        except Exception as e:
            print(f"❌ Error sending event to Telescope: {e}")
            import traceback

            traceback.print_exc()


def test_fixed_integration():
    """Test the fixed Telescope Python client with the running server."""

    print("🔭 Testing Fixed Telescope Python Client Integration")
    print("=" * 55)

    # Initialize the fixed client
    client = FixedTelescopeClient(
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
        print(f"Event ID: {event_id}")

    # Test 2: Capture a message
    print("\n📝 Test 2: Capturing a message...")
    event_id = client.capture_message(
        "Test message from Python client",
        level="info",
        extra={"test_type": "message_capture", "test_number": 2},
    )
    print(f"Event ID: {event_id}")

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
        print(f"Event ID: {event_id}")

    print("\n🎉 All tests completed!")
    print("\n📊 Check your Telescope dashboard at: http://localhost:8080")
    print("   You should see new events in the TS-438154 project")


if __name__ == "__main__":
    # Wait a bit for the server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)

    try:
        test_fixed_integration()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
