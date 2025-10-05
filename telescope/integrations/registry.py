"""
Integration registry and auto-discovery system for Telescope.

This module provides automatic integration discovery and setup,
following Sentry's proven integration patterns.
"""

import logging
from typing import Dict, List, Optional, Type, Union

from .base import DidNotEnable, Integration

logger = logging.getLogger(__name__)

# Default integrations that are always available
_DEFAULT_INTEGRATIONS = [
    "telescope.integrations.logging.LoggingIntegration",
]

# Auto-enabling integrations that are enabled when their dependencies are available
_AUTO_ENABLING_INTEGRATIONS = [
    # Web Frameworks
    "telescope.integrations.django.DjangoIntegration",
    "telescope.integrations.flask.FlaskIntegration",
    "telescope.integrations.fastapi.FastAPIIntegration",
    "telescope.integrations.starlette.StarletteIntegration",
    "telescope.integrations.quart.QuartIntegration",
    "telescope.integrations.sanic.SanicIntegration",
    "telescope.integrations.tornado.TornadoIntegration",
    "telescope.integrations.aiohttp.AioHttpIntegration",
    # Database Integrations
    "telescope.integrations.sqlalchemy.SQLAlchemyIntegration",
    "telescope.integrations.redis.RedisIntegration",
    # Task Queue Integrations
    "telescope.integrations.celery.CeleryIntegration",
    # AI/ML Integrations
    "telescope.integrations.openai.OpenAIIntegration",
    # HTTP Client Integrations
    "telescope.integrations.requests.RequestsIntegration",
]

# Minimum version requirements for integrations
_MIN_VERSIONS = {
    "django": (1, 8),
    "flask": (1, 1, 4),
    "fastapi": (0, 79, 0),
    "starlette": (0, 16),
    "quart": (0, 16, 0),
    "sanic": (0, 8),
    "tornado": (6, 0),
    "aiohttp": (3, 4),
    "sqlalchemy": (1, 2),
    "redis": (3, 0),
    "celery": (4, 4, 7),
    "openai": (1, 0, 0),
    "requests": (2, 0, 0),
}


def _generate_default_integrations_iterator(
    integrations: List[str],
    auto_enabling_integrations: List[str],
):
    """Generate iterator for default integrations."""

    def iter_default_integrations(with_auto_enabling_integrations: bool):
        """Returns an iterator of the default integration classes."""
        from importlib import import_module

        if with_auto_enabling_integrations:
            all_import_strings = integrations + auto_enabling_integrations
        else:
            all_import_strings = integrations

        for import_string in all_import_strings:
            try:
                module, cls = import_string.rsplit(".", 1)
                yield getattr(import_module(module), cls)
            except (DidNotEnable, SyntaxError) as e:
                logger.debug(
                    "Did not import default integration %s: %s", import_string, e
                )

    return iter_default_integrations


def _check_minimum_version(
    integration: Type[Integration],
    version: Optional[tuple],
    package: Optional[str] = None,
):
    """Check if integration meets minimum version requirements."""
    package = package or integration.identifier

    if version is None:
        raise DidNotEnable(f"Unparsable {package} version.")

    min_version = _MIN_VERSIONS.get(integration.identifier)
    if min_version is None:
        return

    if version < min_version:
        raise DidNotEnable(
            f"Integration only supports {package} {'.'.join(map(str, min_version))} or newer."
        )


def setup_integrations(
    integrations: Optional[List[Integration]] = None,
    with_defaults: bool = True,
    with_auto_enabling_integrations: bool = False,
    disabled_integrations: Optional[List[Union[Type[Integration], Integration]]] = None,
) -> Dict[str, Integration]:
    """
    Setup integrations with Telescope client.

    Args:
        integrations: List of integration instances
        with_defaults: Whether to include default integrations
        with_auto_enabling_integrations: Whether to include auto-enabling integrations
        disabled_integrations: List of integrations to disable

    Returns:
        Dictionary of enabled integrations
    """

    # Convert integrations to dict
    integrations_dict = {
        integration.identifier: integration for integration in integrations or []
    }

    logger.debug("Setting up integrations (with default = %s)", with_defaults)

    # Integrations that will not be enabled
    disabled_integrations = [
        integration if isinstance(integration, type) else type(integration)
        for integration in disabled_integrations or []
    ]

    # Integrations that are not explicitly set up by the user
    used_as_default_integration = set()

    if with_defaults:
        iter_default_integrations = _generate_default_integrations_iterator(
            _DEFAULT_INTEGRATIONS,
            _AUTO_ENABLING_INTEGRATIONS if with_auto_enabling_integrations else [],
        )

        for integration_cls in iter_default_integrations(
            with_auto_enabling_integrations
        ):
            if integration_cls.identifier not in integrations_dict:
                instance = integration_cls()
                integrations_dict[instance.identifier] = instance
                used_as_default_integration.add(instance.identifier)

    # Setup integrations
    enabled_integrations = {}

    for identifier, integration in integrations_dict.items():
        if type(integration) in disabled_integrations:
            logger.debug("Ignoring integration %s", identifier)
        else:
            try:
                # Check version requirements
                _check_minimum_version(type(integration), None)

                # Setup integration
                integration.setup_once()
                enabled_integrations[identifier] = integration
                logger.debug("Enabled integration %s", identifier)

            except DidNotEnable as e:
                if identifier not in used_as_default_integration:
                    raise
                logger.debug("Did not enable default integration %s: %s", identifier, e)
            except Exception as e:
                logger.error("Error setting up integration %s: %s", identifier, e)

    return enabled_integrations


def get_available_integrations() -> List[str]:
    """Get list of available integration identifiers."""
    return list(_MIN_VERSIONS.keys())


def get_integration_info(identifier: str) -> Dict[str, any]:
    """Get information about a specific integration."""
    return {
        "identifier": identifier,
        "min_version": _MIN_VERSIONS.get(identifier),
        "auto_enabling": identifier
        in [
            imp.split(".")[-1].replace("Integration", "").lower()
            for imp in _AUTO_ENABLING_INTEGRATIONS
        ],
    }
