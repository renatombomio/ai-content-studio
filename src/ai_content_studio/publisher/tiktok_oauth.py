# Official docs: https://developers.tiktok.com/doc/oauth-user-access-token-management
# Base URL: https://open.tiktokapis.com/v2/oauth
# Endpoints: POST /token/ (exchange code, refresh token)
# Authentication: client_key + client_secret in request body

from datetime import UTC, datetime, timedelta

import httpx

from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import PublisherError
from ai_content_studio.publisher.auth import OAuthProvider, OAuthToken

_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


class TikTokOAuth(OAuthProvider):
    """TikTok OAuth 2.0 provider using the official token endpoint."""

    def exchange_code(self, code: str) -> OAuthToken:
        """Exchange an authorization code for an OAuthToken."""
        settings = get_settings()
        data = {
            "client_key": settings.tiktok_client_id or "",
            "client_secret": settings.tiktok_client_secret or "",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.tiktok_redirect_uri or "",
        }
        return self._post(data)

    def refresh(self, refresh_token: str) -> OAuthToken:
        """Exchange a refresh token for a new OAuthToken."""
        settings = get_settings()
        data = {
            "client_key": settings.tiktok_client_id or "",
            "client_secret": settings.tiktok_client_secret or "",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        return self._post(data)

    def _post(self, data: dict[str, str]) -> OAuthToken:
        try:
            response = httpx.post(
                _TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PublisherError(f"TikTok OAuth request failed: {exc}") from exc

        body = response.json()
        if "error" in body and body["error"]:
            raise PublisherError(
                f"TikTok OAuth error: {body.get('error')} — {body.get('error_description', '')}"
            )

        try:
            expires_at = datetime.now(UTC) + timedelta(seconds=int(body["expires_in"]))
            return OAuthToken(
                access_token=body["access_token"],
                refresh_token=body["refresh_token"],
                expires_at=expires_at,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PublisherError(f"TikTok OAuth response malformed: {exc}") from exc
