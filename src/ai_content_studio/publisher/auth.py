"""OAuth authentication contracts."""

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel


class OAuthToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime


class OAuthProvider(ABC):
    """Abstract contract for OAuth 2.0 authentication providers."""

    @abstractmethod
    def exchange_code(self, code: str) -> OAuthToken:
        """Exchange an authorization code for an OAuthToken."""

    @abstractmethod
    def refresh(self, refresh_token: str) -> OAuthToken:
        """Exchange a refresh token for a new OAuthToken."""
