#!/usr/bin/env python3
"""
Debug script to see what the Telescope client is sending.
"""

import json
import sys
import os

# Add the telescope-python-client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "telescope-python-client"))

from telescope_client import TelescopeClient


def debug_telescope_client():
    """Debug what the client sends."""

    print("🔍 Debugging Telescope Client Payload")
    print("=" * 40)

    # Initialize the client
    client = TelescopeClient(
        dsn="http://localhost:8080", project_id="TS-438154", environment="development"
    )

    # Monkey patch the _send_event method to see what's being sent
    original_send_event = client._send_event

    def debug_send_event(event_data):
        print("\n📤 Event payload being sent:")
        print(json.dumps(event_data, indent=2, default=str))
        print("\n" + "=" * 50)
        return original_send_event(event_data)

    client._send_event = debug_send_event

    # Test 1: Simple exception
    print("\n🧪 Test: Capturing a simple exception...")
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        event_id = client.capture_exception(e)
        print(f"Event ID: {event_id}")


if __name__ == "__main__":
    debug_telescope_client()
