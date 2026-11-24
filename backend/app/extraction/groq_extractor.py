"""Read a letter with a free hosted model through an OpenAI-compatible API.

Default: Groq's free tier with the vision model qwen/qwen3.8-27b. Groq does
not keep inference inputs by default. Any other OpenAI-compatible server
works too: set GROQ_BASE_URL, GROQ_MODEL and GROQ_API_KEY.

Same three passes as the local Ollama reader:
1. transcribe each page (vision), unless the PDF already contains its text,
2. extract the JSON schema from that text (JSON mode; the schema is in the prompt),
3. cross-check dates, IBAN, reference numbers and the appeal period
   against the transcript with plain regular expressions.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import time
from collections.abc import Callable

import httpx
from pydantic import ValidationError

from app.config import settings
from app.extraction.claude_extractor import SYSTEM_PROMPT
from app.extraction.errors import ExtractionError
from app.extraction.images import Page, to_pages
from app.extraction.schemas import LetterExtraction
from app.extraction.transcript_check import apply_transcript

log = logging.getLogger(__name__)

Progress = Callable[[str], None]

# Compact JSON keeps the prompt well inside the free tier's tokens-per-minute limit.
SCHEMA_JSON = json.dumps(LetterExtraction.model_json_schema(), ensure_ascii=False, separators=(",", ":"))

HINTS = """
Answer with one JSON object that matches the JSON schema below, nothing else.
All explanations (title, tldr, details, check_this, required_actions, the "en" side of
line_by_line) must be in English. Keep German terms only where the schema asks for them.
Set confidence honestly: below 0.7 if any date, amount or IBAN was hard to read.
"""

TRANSCRIBE_PROMPT = (
    "Transcribe all text in this page of an official German letter exactly, line by line, "
    "keeping the original German spelling, numbers and punctuation. Output only the text."
)

MAX_RATE_LIMIT_WAITS = 3
MAX_WAIT_S = 65


def _no_progress(_: str) -> None:
    pass


def _strip_thinking(text: str) -> str:
    """Reasoning models may prepend <think>…</think>; only the answer matters."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def _chat(payload: dict, progress: Progress) -> str:
    """POST /chat/completions and return the answer text. Waits out free-tier rate limits."""
    if not settings.groq_api_key:
        raise ExtractionError(
            "No Groq API key configured. Create a free key at console.groq.com and set GROQ_API_KEY."
        )
    url = settings.groq_base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    payload = {"model": settings.groq_model, "temperature": 0, **payload}
    for attempt in range(MAX_RATE_LIMIT_WAITS + 1):
        try:
            r = httpx.post(url, json=payload, headers=headers, timeout=settings.groq_timeout_s)
        except httpx.TimeoutException as e:
            raise ExtractionError("The AI service took too long to answer. Please try again.") from e
        except httpx.HTTPError as e:
            raise ExtractionError("Can't reach the AI service right now. Please try again in a moment.") from e

        if r.status_code == 429 and attempt < MAX_RATE_LIMIT_WAITS:
            # Free tier: a few thousand tokens per minute. Wait as long as the server asks.
            try:
                wait = float(r.headers.get("retry-after", "20"))
            except ValueError:
                wait = 20.0
            wait = min(max(wait, 1.0), MAX_WAIT_S)
            progress(f"Free AI service is busy, waiting {round(wait)}s")
            time.sleep(wait)
            continue
        if r.status_code == 429:
            raise ExtractionError("The free AI service is busy (rate limit). Please try again in a few minutes.")
        if r.status_code in (401, 403):
            raise ExtractionError("The AI service rejected the API key. Check GROQ_API_KEY.")
        if r.status_code == 404:
            raise ExtractionError(f"The AI service doesn't offer the model '{settings.groq_model}'. Check GROQ_MODEL.")
        if r.status_code >= 400:
            try:
                detail = r.json().get("error", {}).get("message", r.text)
            except (ValueError, AttributeError):
                detail = r.text
            raise ExtractionError(f"AI service error: {detail}")
        try:
            return _strip_thinking(r.json()["choices"][0]["message"]["content"] or "")
        except (ValueError, KeyError, IndexError) as e:
            raise ExtractionError("The AI service sent an unexpected answer. Please try again.") from e
    raise AssertionError("unreachable")


def transcribe(pages: list[Page], progress: Progress = _no_progress) -> str:
    """Pass 1: text for every page. Digital PDF pages already have it; images go to the vision model."""
    to_read = sum(1 for p in pages if p.text is None)
    texts = []
    for i, page in enumerate(pages, 1):
        if page.text is not None:
            text = page.text
        else:
            progress(f"Reading page {i} of {len(pages)}" if to_read > 1 else "Reading the page")
            image = base64.b64encode(page.image or b"").decode("ascii")
            text = _chat(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": TRANSCRIBE_PROMPT},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}},
                            ],
                        }
                    ]
                },
                progress,
            )
        texts.append(f"--- Page {i} ---\n{text}" if len(pages) > 1 else text)
    transcript = "\n\n".join(texts)
    if len(transcript) < 40:
        raise ExtractionError("No readable text found. Take the photo in good light, straight from above.")
    return transcript


def extract_letter_groq(
    files: list[tuple[bytes, str]], progress: Progress = _no_progress
) -> tuple[LetterExtraction, str]:
    progress("Preparing pages")
    pages = to_pages(files)
    transcript = transcribe(pages, progress)
    progress("Understanding the letter")
    content = _chat(
        {
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + HINTS + "\nJSON schema:\n" + SCHEMA_JSON},
                {"role": "user", "content": "Here is the transcribed letter:\n\n" + transcript},
            ],
        },
        progress,
    )
    try:
        result = LetterExtraction.model_validate_json(content)
    except ValidationError as e:
        log.warning("AI service returned invalid JSON: %s", content[:500])
        raise ExtractionError("The AI's answer didn't match the expected format. Please try again.") from e

    # Pass 3: deterministic cross-check against the transcript.
    changes = apply_transcript(result, transcript)
    if changes:
        log.info("Transcript cross-check changed: %s", "; ".join(changes))
    result.confidence = min(result.confidence, 0.9)
    return result, f"groq:{settings.groq_model}"
