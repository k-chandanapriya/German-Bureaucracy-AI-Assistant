"""Pick the letter reader configured in AI_PROVIDER."""

from __future__ import annotations

from app.config import settings
from app.extraction.schemas import LetterExtraction


def extract_letter(files: list[tuple[bytes, str]]) -> tuple[LetterExtraction, str]:
    if settings.ai_provider == "ollama":
        from app.extraction.ollama_extractor import extract_letter_ollama

        return extract_letter_ollama(files)

    from app.extraction.claude_extractor import extract_letter as extract_letter_claude

    return extract_letter_claude(files)
