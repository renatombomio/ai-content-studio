"""Tests for OAuth authentication contracts."""

from datetime import UTC, datetime

import pytest

from ai_content_studio.publisher.auth import OAuthProvider, OAuthToken


def _make_token(**kwargs: object) -> OAuthToken:
    defaults: dict[str, object] = {
        "access_token": "act-abc123",
        "refresh_token": "rft-xyz789",
        "expires_at": datetime(2026, 8, 4, 10, 0, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return OAuthToken(**defaults)  # type: ignore[arg-type]


# --- OAuthToken ---


def test_oauth_token_creation() -> None:
    token = _make_token()
    assert token.access_token == "act-abc123"
    assert token.refresh_token == "rft-xyz789"


def test_oauth_token_expires_at_stored() -> None:
    dt = datetime(2026, 8, 4, 10, 0, tzinfo=UTC)
    token = _make_token(expires_at=dt)
    assert token.expires_at == dt


def test_oauth_token_model_dump() -> None:
    token = _make_token()
    data = token.model_dump()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_at" in data


# --- OAuthProvider ---


def test_oauth_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        OAuthProvider()  # type: ignore[abstract]


def test_exchange_code_must_be_implemented() -> None:
    class IncompleteProvider(OAuthProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()  # type: ignore[abstract]


def test_refresh_must_be_implemented() -> None:
    class PartialProvider(OAuthProvider):
        def exchange_code(self, code: str) -> OAuthToken:
            return _make_token()

    with pytest.raises(TypeError):
        PartialProvider()  # type: ignore[abstract]


def test_concrete_provider_is_instantiable() -> None:
    class ConcreteProvider(OAuthProvider):
        def exchange_code(self, code: str) -> OAuthToken:
            return _make_token()

        def refresh(self, refresh_token: str) -> OAuthToken:
            return _make_token()

    provider = ConcreteProvider()
    assert isinstance(provider, OAuthProvider)


def test_exchange_code_returns_oauth_token() -> None:
    class ConcreteProvider(OAuthProvider):
        def exchange_code(self, code: str) -> OAuthToken:
            return _make_token(access_token=f"act-{code}")

        def refresh(self, refresh_token: str) -> OAuthToken:
            return _make_token()

    result = ConcreteProvider().exchange_code("mycode")
    assert isinstance(result, OAuthToken)
    assert result.access_token == "act-mycode"


def test_refresh_returns_oauth_token() -> None:
    class ConcreteProvider(OAuthProvider):
        def exchange_code(self, code: str) -> OAuthToken:
            return _make_token()

        def refresh(self, refresh_token: str) -> OAuthToken:
            return _make_token(refresh_token=refresh_token)

    result = ConcreteProvider().refresh("rft-new")
    assert isinstance(result, OAuthToken)
    assert result.refresh_token == "rft-new"
