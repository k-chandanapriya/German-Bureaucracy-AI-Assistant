"""Pick the letter reader configured in AI_PROVIDER."""

from __future__ import annotations

from collections.abc import Callable

from app.config import settings
from app.extraction.schemas import LetterExtraction


def extract_letter(
    files: list[tuple[bytes, str]], progress: Callable[[str], None] = lambda _: None
) -> tuple[LetterExtraction, str]:
    """progress(stage) is called with short human-readable stages while reading."""
    if settings.ai_provider == "ollama":
        from app.extraction.ollama_extractor import extract_letter_ollama

        return extract_letter_ollama(files, progress)
    if settings.ai_provider == "groq":
        from app.extraction.groq_extractor import extract_letter_groq

        return extract_letter_groq(files, progress)

    from app.extraction.claude_extractor import extract_letter as extract_letter_claude

    progress("Reading the letter")
    return extract_letter_claude(files)
