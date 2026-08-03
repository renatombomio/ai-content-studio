# Official docs: https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status
# Endpoint: POST /v2/post/publish/status/fetch/
# Rate limit: 30 req/min per access token
# Terminal states: PUBLISH_COMPLETE, FAILED

import time
from datetime import UTC, datetime

import httpx

from ai_content_studio.core.exceptions import PublisherError
from ai_content_studio.publisher.auth import OAuthToken
from ai_content_studio.publisher.tiktok import TikTokPublisher
from ai_content_studio.publisher.tiktok_oauth import TikTokOAuth
from ai_content_studio.shared.models import Publication, PublicationStatus

_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

_TIKTOK_COMPLETE = "PUBLISH_COMPLETE"
_TIKTOK_FAILED = "FAILED"

_DEFAULT_POLL_INTERVAL = 5.0
_DEFAULT_POLL_TIMEOUT = 600.0


class PublicationService:
    """Orchestrates the full publication pipeline: OAuth → upload → poll."""

    def __init__(
        self,
        oauth: TikTokOAuth,
        publisher: TikTokPublisher,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        poll_timeout: float = _DEFAULT_POLL_TIMEOUT,
    ) -> None:
        self._oauth = oauth
        self._publisher = publisher
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout

    def publish(self, publication: Publication, authorization_code: str) -> Publication:
        """Exchange auth code, upload, poll until terminal state, return final Publication."""
        token = self._oauth.exchange_code(authorization_code)
        publication = self._publisher.publish(publication, token)
        return self._poll(publication, token)

    def _poll(self, publication: Publication, token: OAuthToken) -> Publication:
        if not publication.publish_id:
            raise PublisherError("publish_id missing — cannot poll status")

        deadline = time.monotonic() + self._poll_timeout

        while time.monotonic() < deadline:
            data = self._fetch_status(publication.publish_id, token)
            tiktok_status = data.get("status", "")

            if tiktok_status == _TIKTOK_COMPLETE:
                post_id_raw = data.get("publicaly_available_post_id")
                external_id = str(post_id_raw) if post_id_raw else None
                return publication.model_copy(update={
                    "status": PublicationStatus.PUBLISHED,
                    "external_id": external_id,
                    "published_at": datetime.now(UTC),
                })

            if tiktok_status == _TIKTOK_FAILED:
                return publication.model_copy(update={"status": PublicationStatus.FAILED})

            time.sleep(self._poll_interval)

        raise PublisherError(f"Publication polling timed out after {self._poll_timeout}s")

    def _fetch_status(self, publish_id: str, token: OAuthToken) -> dict[str, object]:
        try:
            resp = httpx.post(
                _STATUS_URL,
                json={"publish_id": publish_id},
                headers={
                    "Authorization": f"Bearer {token.access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise PublisherError(f"TikTok status fetch failed: {exc}") from exc

        body = resp.json()
        err = body.get("error", {})
        if isinstance(err, dict) and err.get("code", "ok") != "ok":
            raise PublisherError(
                f"TikTok status error: {err.get('code')} — {err.get('message', '')}"
            )

        data = body.get("data", {})
        assert isinstance(data, dict)
        return data
