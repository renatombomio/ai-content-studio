"""Abstract publisher interface."""

from abc import ABC, abstractmethod

from ai_content_studio.shared.models import Publication


class Publisher(ABC):
    """Abstract contract for any publishing platform."""

    @abstractmethod
    def publish(self, publication: Publication) -> Publication:
        """Upload publication to the platform and return the updated Publication."""
