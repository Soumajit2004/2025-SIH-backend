from __future__ import annotations

"""Application configuration using Pydantic BaseSettings.

This centralizes environment variable parsing & validation and replaces scattered
os.getenv lookups. It also codifies the credential sourcing priority for Firebase.

Priority for Firebase credentials (same as previous implementation):
1. FIREBASE_CREDENTIALS (path to json file) -> must exist
2. FIREBASE_CREDENTIALS_B64 (base64 encoded JSON)
3. FIREBASE_CREDENTIALS_JSON (raw json string)

Only one of the three is required. If multiple are provided simultaneously the first
in the above priority order takes effect. We still keep the raw values so firebase
module can decide how to construct credentials.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional
import os


class Settings(BaseSettings):
    # Core web config
    PORT: int = Field(default=8000, description="Port FastAPI/uvicorn should bind to")
    HOST: str = Field(default="0.0.0.0", description="Host interface to bind")
    RELOAD: bool = Field(default=False, description="Enable autoreload (dev only)")

    # Firebase credential sources (mirror previous implementation)
    FIREBASE_CREDENTIALS: Optional[str] = Field(
        default=None, description="Path to Firebase service account JSON file"
    )
    FIREBASE_CREDENTIALS_B64: Optional[str] = Field(
        default=None, description="Base64 encoded service account JSON"
    )
    FIREBASE_CREDENTIALS_JSON: Optional[str] = Field(
        default=None, description="Raw JSON string for service account"
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def validate_firebase_sources(self):  # type: ignore[override]
        if not any([
            self.FIREBASE_CREDENTIALS,
            self.FIREBASE_CREDENTIALS_B64,
            self.FIREBASE_CREDENTIALS_JSON,
        ]):
            # Allow missing credentials at startup; firebase utility will raise if used.
            return self
        if self.FIREBASE_CREDENTIALS and not os.path.isfile(self.FIREBASE_CREDENTIALS):
            raise ValueError(f"FIREBASE_CREDENTIALS file not found: {self.FIREBASE_CREDENTIALS}")
        return self


settings = Settings()  # singleton-style importable instance

__all__ = ["settings", "Settings"]
