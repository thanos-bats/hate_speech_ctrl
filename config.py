from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_secret: str | None = Field(default=None, validation_alias="HATE_SPEECH_JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="HATE_SPEECH_JWT_ALGORITHM")
    access_token_minutes: int = Field(default=30, validation_alias="HATE_SPEECH_ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=7, validation_alias="HATE_SPEECH_REFRESH_TOKEN_DAYS")
    auth_client_id: str | None = Field(default=None, validation_alias="HATE_SPEECH_AUTH_CLIENT_ID")
    auth_client_secret: str | None = Field(default=None, validation_alias="HATE_SPEECH_AUTH_CLIENT_SECRET")
    hate_speech_api_url: str | None = Field(default=None, validation_alias="HATE_SPEECH_API_URL")


settings = Settings()

# Keep existing constant names for compatibility with other modules.
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
REQUIRED_SCOPE = "hate_speech:predict"
ACCESS_TOKEN_MINUTES = settings.access_token_minutes
REFRESH_TOKEN_DAYS = settings.refresh_token_days
AUTH_CLIENT_ID = settings.auth_client_id
AUTH_CLIENT_SECRET = settings.auth_client_secret
HATE_SPEECH_API_URL = settings.hate_speech_api_url
