from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # Claude Sonnet reads most letters; Claude Opus re-reads low-confidence ones.
    extraction_model: str = "claude-sonnet-5-5"
    escalation_model: str = "claude-opus-5-5"
    escalation_threshold: float = 0.7

    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'amtspost.db'}"
    default_bundesland: str = "BE"
    cors_origins: str = "http://localhost:3000"
    max_upload_mb: int = 20


settings = Settings()
