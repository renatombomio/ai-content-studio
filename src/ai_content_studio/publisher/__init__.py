"""Publisher module — platform publishing abstractions."""

from ai_content_studio.publisher.auth import OAuthProvider, OAuthToken
from ai_content_studio.publisher.interface import Publisher
from ai_content_studio.publisher.service import PublicationService
from ai_content_studio.publisher.tiktok import TikTokPublisher
from ai_content_studio.publisher.tiktok_oauth import TikTokOAuth

__all__ = [
    "OAuthProvider",
    "OAuthToken",
    "PublicationService",
    "Publisher",
    "TikTokOAuth",
    "TikTokPublisher",
]
