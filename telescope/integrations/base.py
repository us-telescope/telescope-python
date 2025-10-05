"""
Base integration class for Telescope integrations.

This module provides the foundation for all Telescope integrations,
following Sentry's proven integration patterns.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Set

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..client import TelescopeClient


class DidNotEnable(Exception):
    """
    The integration could not be enabled due to a trivial user error like
    a required package not being installed.

    This exception is silently swallowed for default integrations, but reraised
    for explicitly enabled integrations.
    """

    pass


class Integration(ABC):
    """
    Base class for all Telescope integrations.

    To accept options for an integration, implement your own constructor that
    saves those options on `self`.
    """

    identifier: str = None
    """String unique ID of integration type"""

    def __init__(self, **options: Any):
        """Initialize integration with options."""
        self.options = options

    @abstractmethod
    def setup(self, client: "TelescopeClient") -> None:
        """
        Setup the integration with the Telescope client.

        Args:
            client: TelescopeClient instance
        """
        pass

    @abstractmethod
    def setup_once(self) -> None:
        """
        Initialize the integration.

        This function is only called once, ever. Configuration is not available
        at this point, so the only thing to do here is to hook into exception
        handlers, and perhaps do monkeypatches.
        """
        pass


class IntegrationRegistry:
    """Registry for managing Telescope integrations."""

    def __init__(self):
        self._integrations: Dict[str, Integration] = {}
        self._processed: Set[str] = set()
        self._installed: Set[str] = set()

    def register(self, integration: Integration) -> None:
        """Register an integration."""
        if integration.identifier:
            self._integrations[integration.identifier] = integration
            logger.debug("Registered integration: %s", integration.identifier)

    def setup(self, client: "TelescopeClient", integration: Integration) -> None:
        """Setup an integration with a client."""
        if integration.identifier and integration.identifier not in self._processed:
            try:
                integration.setup_once()
                integration.setup(client)
                self._installed.add(integration.identifier)
                logger.debug("Enabled integration: %s", integration.identifier)
            except DidNotEnable as e:
                logger.debug(
                    "Did not enable integration %s: %s", integration.identifier, e
                )
            except Exception as e:
                logger.error(
                    "Error setting up integration %s: %s", integration.identifier, e
                )

            self._processed.add(integration.identifier)

    def get_installed(self) -> Set[str]:
        """Get list of installed integration identifiers."""
        return self._installed.copy()

    def is_installed(self, identifier: str) -> bool:
        """Check if an integration is installed."""
        return identifier in self._installed


# Global registry instance
_integration_registry = IntegrationRegistry()


def get_integration_registry() -> IntegrationRegistry:
    """Get the global integration registry."""
    return _integration_registry
