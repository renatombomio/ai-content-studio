"""Tests for TikTokOAuth provider."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ai_content_studio.core.exceptions import PublisherError
from ai_content_studio.publisher.auth import OAuthToken
from ai_content_studio.publisher.tiktok_oauth import _TOKEN_URL, TikTokOAuth

_VALID_RESPONSE = {
    "access_token": "act-abc123",
    "refresh_token": "rft-xyz789",
    "expires_in": 86400,
    "open_id": "uid-111",
    "scope": "video.publish",
}


def _ok(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _http_error() -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="HTTP 401", request=MagicMock(), response=MagicMock(status_code=401)
    )
    return resp


def _network_error() -> MagicMock:
    m = MagicMock(side_effect=httpx.RequestError("connection refused", request=MagicMock()))
    return m


# --- exchange_code ---


def test_exchange_code_returns_oauth_token() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)):
        token = TikTokOAuth().exchange_code("mycode")
    assert isinstance(token, OAuthToken)
    assert token.access_token == "act-abc123"
    assert token.refresh_token == "rft-xyz789"


def test_exchange_code_sends_correct_grant_type() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)) as mock_post:
        TikTokOAuth().exchange_code("mycode")
    _, kwargs = mock_post.call_args
    assert kwargs["data"]["grant_type"] == "authorization_code"
    assert kwargs["data"]["code"] == "mycode"


def test_exchange_code_posts_to_token_url() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)) as mock_post:
        TikTokOAuth().exchange_code("mycode")
    args, _ = mock_post.call_args
    assert args[0] == _TOKEN_URL


def test_exchange_code_maps_expires_at() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)):
        token = TikTokOAuth().exchange_code("mycode")
    assert token.expires_at is not None


# --- refresh ---


def test_refresh_returns_oauth_token() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)):
        token = TikTokOAuth().refresh("rft-old")
    assert isinstance(token, OAuthToken)
    assert token.access_token == "act-abc123"


def test_refresh_sends_correct_grant_type() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)) as mock_post:
        TikTokOAuth().refresh("rft-old")
    _, kwargs = mock_post.call_args
    assert kwargs["data"]["grant_type"] == "refresh_token"
    assert kwargs["data"]["refresh_token"] == "rft-old"


# --- error handling ---


def test_exchange_code_raises_publisher_error_on_http_error() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_http_error()), pytest.raises(PublisherError, match="TikTok OAuth request failed"):
        TikTokOAuth().exchange_code("bad-code")


def test_refresh_raises_publisher_error_on_http_error() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_http_error()), pytest.raises(PublisherError, match="TikTok OAuth request failed"):
        TikTokOAuth().refresh("bad-token")


def test_raises_publisher_error_on_network_failure() -> None:
    with (
        patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", side_effect=httpx.RequestError("connection refused", request=MagicMock())),
        pytest.raises(PublisherError, match="TikTok OAuth request failed"),
    ):
        TikTokOAuth().exchange_code("mycode")


def test_raises_publisher_error_on_api_error_body() -> None:
    error_body = {"error": "invalid_grant", "error_description": "Authorization code expired"}
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(error_body)), pytest.raises(PublisherError, match="TikTok OAuth error"):
        TikTokOAuth().exchange_code("expired-code")


def test_raises_publisher_error_on_malformed_response() -> None:
    malformed = {"unexpected": "fields"}
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(malformed)), pytest.raises(PublisherError, match="TikTok OAuth response malformed"):
        TikTokOAuth().exchange_code("mycode")


# --- OAuthToken mapping ---


def test_oauth_token_access_token_matches_response() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)):
        token = TikTokOAuth().exchange_code("mycode")
    assert token.access_token == _VALID_RESPONSE["access_token"]


def test_oauth_token_refresh_token_matches_response() -> None:
    with patch("ai_content_studio.publisher.tiktok_oauth.httpx.post", return_value=_ok(_VALID_RESPONSE)):
        token = TikTokOAuth().exchange_code("mycode")
    assert token.refresh_token == _VALID_RESPONSE["refresh_token"]
