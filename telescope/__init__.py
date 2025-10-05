"""
Telescope Python Client with OpenTelemetry Integration
=====================================================

A comprehensive error monitoring and observability client for Python applications
that integrates with OpenTelemetry for enhanced tracing and metrics collection.

Features:
- Error tracking and reporting
- OpenTelemetry trace correlation
- Performance monitoring
- Environment-aware reporting
- Automatic context enrichment
"""

from .client import TelescopeClient
from .context import clear_context, set_tags, set_user_context
from .decorators import capture_errors, trace_function

# Async Framework Integrations
from .integrations.aiohttp import AioHttpIntegration, setup_aiohttp_integration

# Base Integration
from .integrations.base import DidNotEnable, Integration, IntegrationRegistry

# Task Queue Integrations
from .integrations.celery import CeleryIntegration, setup_celery_integration

# Web Framework Integrations
from .integrations.django import DjangoIntegration, setup_django_integration
from .integrations.fastapi import FastAPIIntegration, setup_fastapi_integration
from .integrations.flask import FlaskIntegration, setup_flask_integration

# Logging Integrations
from .integrations.logging import LoggingIntegration, setup_logging_integration

# AI/ML Integrations
from .integrations.openai import OpenAIIntegration, setup_openai_integration
from .integrations.quart import QuartIntegration, setup_quart_integration
from .integrations.redis import RedisIntegration, setup_redis_integration

# HTTP Client Integrations
from .integrations.requests import RequestsIntegration, setup_requests_integration
from .integrations.sanic import SanicIntegration, setup_sanic_integration

# Database Integrations
from .integrations.sqlalchemy import SQLAlchemyIntegration, setup_sqlalchemy_integration
from .integrations.starlette import StarletteIntegration, setup_starlette_integration
from .integrations.tornado import TornadoIntegration, setup_tornado_integration

__version__ = "1.0.0"
__all__ = [
    "TelescopeClient",
    # Web Framework Integrations
    "DjangoIntegration",
    "FlaskIntegration",
    "FastAPIIntegration",
    "StarletteIntegration",
    "QuartIntegration",
    "SanicIntegration",
    "TornadoIntegration",
    # Async Framework Integrations
    "AioHttpIntegration",
    # Database Integrations
    "SQLAlchemyIntegration",
    "RedisIntegration",
    # Task Queue Integrations
    "CeleryIntegration",
    # AI/ML Integrations
    "OpenAIIntegration",
    # HTTP Client Integrations
    "RequestsIntegration",
    # Logging Integrations
    "LoggingIntegration",
    # Base Integration
    "Integration",
    "DidNotEnable",
    "IntegrationRegistry",
    # Legacy setup functions
    "setup_django_integration",
    "setup_flask_integration",
    "setup_fastapi_integration",
    "setup_starlette_integration",
    "setup_quart_integration",
    "setup_sanic_integration",
    "setup_tornado_integration",
    "setup_aiohttp_integration",
    "setup_sqlalchemy_integration",
    "setup_redis_integration",
    "setup_celery_integration",
    "setup_openai_integration",
    "setup_requests_integration",
    "setup_logging_integration",
    # Decorators and Context
    "capture_errors",
    "trace_function",
    "set_user_context",
    "set_tags",
    "clear_context",
]
