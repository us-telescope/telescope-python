"""
CLI tools for Telescope client
"""

import argparse
import sys
from .client import TelescopeClient


def test_connection():
    """CLI tool to test connection to Telescope server."""
    parser = argparse.ArgumentParser(description="Test Telescope connection")
    parser.add_argument("--dsn", required=True, help="Telescope server DSN")
    parser.add_argument("--project-id", required=True, help="Project ID")
    parser.add_argument("--api-key", help="API key")
    parser.add_argument("--environment", default="test", help="Environment")

    args = parser.parse_args()

    print(f"Testing connection to {args.dsn}...")
    print(f"Project ID: {args.project_id}")
    print(f"Environment: {args.environment}")

    try:
        client = TelescopeClient(
            dsn=args.dsn,
            project_id=args.project_id,
            api_key=args.api_key,
            environment=args.environment,
        )

        # Test message capture
        event_id = client.capture_message(
            "Test message from Telescope Python client",
            level="info",
            tags={"test": True, "cli": True},
        )

        print(f"✓ Successfully sent test message (Event ID: {event_id})")

        # Test exception capture
        try:
            raise ValueError("Test exception from Telescope Python client")
        except ValueError as e:
            event_id = client.capture_exception(
                e,
                tags={"test": True, "cli": True},
                extra={"test_type": "connection_test"},
            )
            print(f"✓ Successfully sent test exception (Event ID: {event_id})")

        # Flush any pending events
        client.flush()
        client.close()

        print("✓ Connection test completed successfully!")
        return 0

    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_connection())
