"""
Telescope integrations for various frameworks
"""

# Web Frameworks
# Async Frameworks
from .aiohttp import AioHttpIntegration

# Base Integration
from .base import DidNotEnable, Integration, IntegrationRegistry

# Task Queue Integrations
from .celery import CeleryIntegration
from .django import DjangoIntegration
from .fastapi import FastAPIIntegration
from .flask import FlaskIntegration

# Logging Integrations
from .logging import LoggingIntegration

# AI/ML Integrations
from .openai import OpenAIIntegration
from .quart import QuartIntegration
from .redis import RedisIntegration

# HTTP Client Integrations
from .requests import RequestsIntegration
from .sanic import SanicIntegration

# Database Integrations
from .sqlalchemy import SQLAlchemyIntegration
from .starlette import StarletteIntegration
from .tornado import TornadoIntegration

__all__ = [
    # Web Frameworks
    "DjangoIntegration",
    "FlaskIntegration",
    "FastAPIIntegration",
    "StarletteIntegration",
    "QuartIntegration",
    "SanicIntegration",
    "TornadoIntegration",
    # Async Frameworks
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
]
