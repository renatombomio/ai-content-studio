"""Abstract asset provider interface."""

from abc import ABC, abstractmethod

from ai_content_studio.shared.models import Asset


class AssetProvider(ABC):
    """Abstract contract for any visual asset provider."""

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[Asset]:
        """Search for assets matching a visual query and return domain models."""
