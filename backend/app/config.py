from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # Which model reads letters:
    #   "ollama"    local model, nothing leaves the computer (free)
    #   "groq"      free hosted model via Groq (or any OpenAI-compatible API)
    #   "anthropic" Claude API (paid)
    ai_provider: Literal["anthropic", "ollama", "groq"] = "anthropic"

    # Free hosted model (OpenAI-compatible API). Key: console.groq.com
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "qwen/qwen3.8-27b"
    groq_timeout_s: float = 120
    # "none" switches the model's step-by-step thinking off (fewer tokens); "" leaves it on.
    groq_reasoning_effort: str = "none"

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

    # Public deployment safeguards. 0 = no limit (fine on your own computer).
    # Each read costs money with the Claude API, so cap it on a public server.
    max_reads_per_day: int = 0
    max_reads_per_ip_per_day: int = 0
    # Cases saved before cases had owners are handed to the first browser that
    # lists cases. Handy locally; switch off on a public server.
    adopt_unowned_cases: bool = True


settings = Settings()
