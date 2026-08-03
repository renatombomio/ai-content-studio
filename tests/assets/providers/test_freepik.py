"""Tests for FreepikProvider."""

from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.assets.providers.freepik import FreepikProvider, _parse_size
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Asset

_FAKE_RESOURCE = {
    "id": 15667327,
    "image": {
        "type": "photo",
        "source": {
            "url": "https://img.freepik.com/free-photo/sample_740.jpg",
            "size": "740x640",
        },
    },
    "author": {"name": "John Doe"},
    "licenses": [{"type": "freemium"}],
}

_FAKE_RESPONSE = {"data": [_FAKE_RESOURCE]}


def _mock_response(body: dict, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=MagicMock(status_code=status_code),
        )
    return response


def test_search_sends_auth_header() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        FreepikProvider().search("cocoa farm")
        call_kwargs = mock_get.call_args
        assert "x-magnific-api-key" in str(call_kwargs)


def test_search_sends_correct_query_param() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        FreepikProvider().search("cocoa farm")
        call_kwargs = mock_get.call_args
        assert "cocoa farm" in str(call_kwargs)


def test_search_sends_limit_param() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        FreepikProvider().search("harvest", limit=5)
        call_kwargs = mock_get.call_args
        assert "5" in str(call_kwargs)


def test_search_calls_correct_endpoint() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        FreepikProvider().search("cocoa")
        url_called = mock_get.call_args.args[0]
        assert "api.magnific.com" in url_called
        assert "/v1/resources" in url_called


def test_search_returns_list_of_assets() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        results = FreepikProvider().search("cocoa")
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], Asset)


def test_mapping_provider_id() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.provider_id == "15667327"


def test_mapping_source() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.source == "freepik"


def test_mapping_asset_type() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.asset_type == "photo"


def test_mapping_url_and_thumbnail() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.url == "https://img.freepik.com/free-photo/sample_740.jpg"
        assert asset.thumbnail_url == asset.url


def test_mapping_dimensions() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.width == 740
        assert asset.height == 640


def test_mapping_author() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.author == "John Doe"


def test_mapping_license() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.license == "freemium"


def test_mapping_duration_is_none() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.duration is None


def test_mapping_path_is_none() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_RESPONSE)
        asset = FreepikProvider().search("cocoa")[0]
        assert asset.path is None


def test_empty_results_returns_empty_list() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response({"data": []})
        results = FreepikProvider().search("cocoa")
        assert results == []


def test_api_failure_raises_asset_error() -> None:
    import httpx as httpx_module

    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.side_effect = httpx_module.ConnectError("connection refused")
        with pytest.raises(AssetError):
            FreepikProvider().search("cocoa")


def test_http_status_error_raises_asset_error() -> None:
    with patch("ai_content_studio.assets.providers.freepik.httpx.get") as mock_get:
        mock_get.return_value = _mock_response({}, status_code=401)
        with pytest.raises(AssetError):
            FreepikProvider().search("cocoa")


def test_parse_size_valid() -> None:
    assert _parse_size("740x640") == (740, 640)


def test_parse_size_empty() -> None:
    assert _parse_size("") == (None, None)


def test_parse_size_invalid() -> None:
    assert _parse_size("notasize") == (None, None)


def test_parse_size_non_numeric() -> None:
    assert _parse_size("axb") == (None, None)
