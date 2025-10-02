# Telescope Python Client

A comprehensive Python client for Telescope error monitoring with OpenTelemetry integration.

## Features

🔹 **Error Tracking**: Automatic exception capture and reporting  
🔹 **OpenTelemetry Integration**: Full tracing and metrics support  
🔹 **Framework Support**: Django, Flask, FastAPI, Celery integrations  
🔹 **Environment Awareness**: Production, staging, development separation  
🔹 **Performance Monitoring**: Slow query and function execution tracking  
🔹 **Context Enrichment**: Automatic user, request, and custom context  
🔹 **Retry Logic**: Built-in retry mechanisms with telemetry  

## Installation

```bash
# Basic installation
pip install telescope-python

# With Django support
pip install telescope-python[django]

# With Flask support  
pip install telescope-python[flask]

# With FastAPI support
pip install telescope-python[fastapi]

# With all integrations
pip install telescope-python[all]
```

## Quick Start

### Basic Setup

```python
from telescope_client import TelescopeClient

# Initialize client
client = TelescopeClient(
    dsn="https://your-telescope-server.com",
    project_id="TS-123456",
    environment="production",
    api_key="your-api-key",
    enable_tracing=True,
)

# Capture an exception
try:
    risky_operation()
except Exception as e:
    client.capture_exception(e)

# Capture a message
client.capture_message("Payment processed successfully", level="info")
```

### Django Integration

```python
# settings.py
from telescope_client import TelescopeClient, setup_django_integration

TELESCOPE_CLIENT = TelescopeClient(
    dsn="https://your-telescope-server.com",
    project_id="TS-123456", 
    environment="production",
    api_key="your-api-key",
)

# Setup automatic Django integration
setup_django_integration(TELESCOPE_CLIENT)
```

### Flask Integration

```python
from flask import Flask
from telescope_client import TelescopeClient, setup_flask_integration

app = Flask(__name__)

client = TelescopeClient(
    dsn="https://your-telescope-server.com",
    project_id="TS-123456",
    environment="production", 
)

# Setup Flask integration
init_telescope = setup_flask_integration(client)
init_telescope(app)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from telescope_client import TelescopeClient, setup_fastapi_integration

app = FastAPI()

client = TelescopeClient(
    dsn="https://your-telescope-server.com",
    project_id="TS-123456",
    environment="production",
)

# Setup FastAPI integration
init_telescope = setup_fastapi_integration(client)
init_telescope(app)
```

## Advanced Usage

### Decorators

```python
from telescope_client import capture_errors, trace_function, performance_monitor

# Automatic error capture
@capture_errors(tags={"component": "payment"})
def process_payment(amount):
    return charge_card(amount)

# Function tracing
@trace_function(tags={"component": "database"}, capture_args=True)
def get_user(user_id):
    return User.objects.get(id=user_id)

# Performance monitoring
@performance_monitor(threshold_ms=500)
def expensive_operation():
    # Will report if takes longer than 500ms
    time.sleep(1)
```

### Context Management

```python
from telescope_client import set_user_context, set_tags, with_context

# Set user context
set_user_context(
    user_id="12345",
    username="john_doe", 
    email="john@example.com"
)

# Set tags
set_tags(
    component="auth",
    version="1.2.3"
)

# Temporary context
with with_context(user_id="123", component="payment"):
    # Any errors here will include this context
    process_payment()
```

### OpenTelemetry Tracing

```python
# Start a transaction
with client.start_transaction("payment_flow", op="payment") as span:
    span.set_attribute("payment.amount", 100.00)
    span.set_attribute("payment.currency", "USD")
    
    try:
        result = process_payment(100.00)
        span.set_attribute("payment.success", True)
    except Exception as e:
        span.record_exception(e)
        span.set_status(trace.Status(trace.StatusCode.ERROR))
        raise
```

### Environment-Specific Configuration

```python
import os

client = TelescopeClient(
    dsn=os.getenv("TELESCOPE_DSN"),
    project_id=os.getenv("TELESCOPE_PROJECT_ID"),
    environment=os.getenv("ENVIRONMENT", "production"),
    api_key=os.getenv("TELESCOPE_API_KEY"),
    
    # Environment-specific settings
    sample_rate=1.0 if os.getenv("ENVIRONMENT") == "production" else 0.1,
    enable_tracing=os.getenv("ENVIRONMENT") != "test",
    enable_performance=True,
)
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dsn` | str | Required | Telescope server endpoint |
| `project_id` | str | Required | Project identifier |
| `environment` | str | "production" | Environment name |
| `api_key` | str | None | API key for authentication |
| `enable_tracing` | bool | True | Enable OpenTelemetry tracing |
| `enable_performance` | bool | True | Enable performance monitoring |
| `sample_rate` | float | 1.0 | Error sampling rate (0.0-1.0) |
| `otlp_endpoint` | str | None | OpenTelemetry collector endpoint |

## OpenTelemetry Integration

The client automatically integrates with OpenTelemetry to provide:

### Trace Correlation
- Links errors to distributed traces
- Provides trace and span IDs in error reports
- Correlates errors across service boundaries

### Automatic Instrumentation
- HTTP requests (incoming and outgoing)
- Database queries
- Framework-specific operations
- Background tasks (Celery)

### Custom Spans
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_span("custom_operation") as span:
    span.set_attribute("operation.type", "data_processing")
    span.set_attribute("operation.batch_size", 1000)
    
    # Your code here
    process_data_batch()
```

### Metrics Collection
```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Create counters and gauges
error_counter = meter.create_counter("errors_total")
response_time_histogram = meter.create_histogram("response_time_seconds")

# Record metrics
error_counter.add(1, {"error_type": "validation"})
response_time_histogram.record(0.150, {"endpoint": "/api/users"})
```

## Best Practices

### 1. Environment Configuration
```python
# Use environment variables for configuration
client = TelescopeClient(
    dsn=os.getenv("TELESCOPE_DSN"),
    project_id=os.getenv("TELESCOPE_PROJECT_ID"),
    environment=os.getenv("ENVIRONMENT", "production"),
)
```

### 2. Context Enrichment
```python
# Set context early in request lifecycle
set_user_context(user_id=request.user.id)
set_tags(
    request_id=request.headers.get("X-Request-ID"),
    feature_flags=get_active_feature_flags(request.user)
)
```

### 3. Performance Monitoring
```python
# Monitor critical paths
@performance_monitor(threshold_ms=100, tags={"critical": True})
def critical_database_query():
    return expensive_query()
```

### 4. Error Grouping
```python
# Use fingerprints for custom error grouping
client.capture_exception(
    exception,
    fingerprint=["payment", "stripe", error.code]
)
```

## Testing

```bash
# Run tests
pytest

# Test connection to Telescope server
telescope-test --dsn https://your-server.com --project-id TS-123456
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
