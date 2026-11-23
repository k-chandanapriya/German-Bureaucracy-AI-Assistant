from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # Which model reads letters: "anthropic" (Claude API) or "ollama" (local, nothing leaves the computer)
    ai_provider: Literal["anthropic", "ollama"] = "anthropic"

    # Local model via Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5vl:7b"
    ollama_timeout_s: float = 300
    ollama_num_ctx: int = 16384

    # Claude Sonnet reads most letters; Claude Opus re-reads low-confidence ones.
    extraction_model: str = "claude-sonnet-5-5"
    escalation_model: str = "claude-opus-5-5"
    escalation_threshold: float = 0.7

    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'amtspost.db'}"
    default_bundesland: str = "BE"
    cors_origins: str = "http://localhost:3000"
    max_upload_mb: int = 20


settings = Settings()
