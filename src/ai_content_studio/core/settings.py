"""Application settings definition."""

from pydantic import BaseModel


class Settings(BaseModel):
    """Top-level application settings."""

    app_name: str = "AI Content Studio"
    version: str = "0.1.0"
    debug: bool = False
