# Official docs: https://developers.tiktok.com/doc/content-posting-api-get-started
# Base URL: https://open.tiktokapis.com/v2/post/publish
# Endpoints: POST /creator_info/query/, POST /video/init/, PUT {upload_url}
# Authentication: Authorization: Bearer {access_token}

import math
from pathlib import Path

import httpx

from ai_content_studio.core.exceptions import PublisherError
from ai_content_studio.publisher.auth import OAuthToken
from ai_content_studio.publisher.tiktok_oauth import TikTokOAuth
from ai_content_studio.shared.models import Publication, PublicationStatus

_CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
_VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB


class TikTokPublisher:
    """TikTok Direct Post publisher using the official Content Posting API."""

    def __init__(self, oauth: TikTokOAuth) -> None:
        self._oauth = oauth

    def publish(self, publication: Publication, token: OAuthToken) -> Publication:
        """Upload a video to TikTok and return the updated Publication."""
        _validate(publication)
        privacy_level = self._get_creator_privacy(token)
        publish_id, upload_url = self._init_upload(publication, token, privacy_level)
        self._upload_video(publication.video_path, upload_url)
        return publication.model_copy(update={
            "status": PublicationStatus.PROCESSING,
            "publish_id": publish_id,
        })

    def _get_creator_privacy(self, token: OAuthToken) -> str:
        data = self._post(_CREATOR_INFO_URL, token, {})
        options = data.get("privacy_level_options")
        if not isinstance(options, list) or not options:
            raise PublisherError("TikTok creator_info returned no privacy_level_options")
        return str(options[0])

    def _init_upload(
        self, publication: Publication, token: OAuthToken, privacy_level: str
    ) -> tuple[str, str]:
        video_size = publication.video_path.stat().st_size
        effective_chunk_size = min(_CHUNK_SIZE, video_size)
        total_chunk_count = math.ceil(video_size / effective_chunk_size)

        caption = publication.caption
        if publication.hashtags:
            caption += " " + " ".join(publication.hashtags)

        payload: dict[str, object] = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": effective_chunk_size,
                "total_chunk_count": total_chunk_count,
            },
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
            },
        }

        data = self._post(_VIDEO_INIT_URL, token, payload)
        try:
            return str(data["publish_id"]), str(data["upload_url"])
        except KeyError as exc:
            raise PublisherError(f"TikTok video init response malformed: {exc}") from exc

    def _upload_video(self, video_path: Path, upload_url: str) -> None:
        video_size = video_path.stat().st_size
        offset = 0
        with open(video_path, "rb") as f:
            while True:
                chunk = f.read(_CHUNK_SIZE)
                if not chunk:
                    break
                end = offset + len(chunk) - 1
                try:
                    resp = httpx.put(
                        upload_url,
                        content=chunk,
                        headers={
                            "Content-Type": "video/mp4",
                            "Content-Range": f"bytes {offset}-{end}/{video_size}",
                            "Content-Length": str(len(chunk)),
                        },
                        timeout=300.0,
                    )
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    raise PublisherError(f"TikTok video upload failed: {exc}") from exc
                offset += len(chunk)

    def _post(self, url: str, token: OAuthToken, payload: dict[str, object]) -> dict[str, object]:
        try:
            resp = httpx.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token.access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise PublisherError(f"TikTok API request failed: {exc}") from exc

        body = resp.json()
        err = body.get("error", {})
        if isinstance(err, dict) and err.get("code", "ok") != "ok":
            raise PublisherError(
                f"TikTok API error: {err.get('code')} — {err.get('message', '')}"
            )

        data = body.get("data", {})
        assert isinstance(data, dict)
        return data


def _validate(publication: Publication) -> None:
    if not publication.video_path.exists():
        raise PublisherError(f"Video file not found: {publication.video_path}")
