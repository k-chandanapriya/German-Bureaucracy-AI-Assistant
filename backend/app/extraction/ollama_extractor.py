"""Read a letter with a local vision model through Ollama.

Nothing leaves the computer: the photo goes to the Ollama server on
localhost. Small local models are excellent at transcribing a page but weak
at filling a large schema from pixels, so reading happens in three passes:

1. transcribe each page to plain text (vision), unless the PDF already
   contains its text,
2. extract the JSON schema from that text (Ollama constrains the output to
   the same schema the Claude extractor uses),
3. cross-check dates, IBAN, reference numbers and the appeal period against
   the transcript with plain regular expressions.
"""

from __future__ import annotations

import base64
import json
import logging
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


def _no_progress(_: str) -> None:
    pass

SCHEMA = LetterExtraction.model_json_schema()

LOCAL_HINTS = """
Answer with one JSON object that matches the given schema, nothing else.
All explanations (title, tldr, details, check_this, required_actions, the "en" side of
line_by_line) must be in English. Keep German terms only where the schema asks for them.
Set confidence honestly: below 0.7 if any date, amount or IBAN was hard to read.
"""


def _post(payload: dict) -> dict:
    url = settings.ollama_url.rstrip("/") + "/api/chat"
    try:
        r = httpx.post(url, json=payload, timeout=settings.ollama_timeout_s)
    except httpx.ConnectError as e:
        raise ExtractionError(
            f"Can't reach Ollama at {settings.ollama_url}. Start the Ollama app (or run 'ollama serve') and try again."
        ) from e
    except httpx.TimeoutException as e:
        raise ExtractionError(
            "The local model took too long. Try fewer pages, or raise OLLAMA_TIMEOUT_S in backend/.env."
        ) from e
    except httpx.HTTPError as e:
        # e.g. Ollama was restarted while it was reading
        raise ExtractionError("The connection to Ollama was interrupted. Please try again.") from e
    if r.status_code == 404:
        raise ExtractionError(
            f"The model '{settings.ollama_model}' isn't downloaded yet. Run: ollama pull {settings.ollama_model}"
        )
    if r.status_code >= 400:
        try:
            detail = r.json().get("error", r.text)
        except ValueError:
            detail = r.text
        raise ExtractionError(f"Ollama error: {detail}")
    return r.json()


TRANSCRIBE_PROMPT = (
    "Transcribe all text in this page of an official German letter exactly, line by line, "
    "keeping the original German spelling, numbers and punctuation. Output only the text."
)


def transcribe(pages: list[Page], progress: Progress = _no_progress) -> str:
    """Pass 1: text for every page. Digital PDF pages already have it; images go to the vision model."""
    to_read = sum(1 for p in pages if p.text is None)
    done = 0
    texts = []
    for i, page in enumerate(pages, 1):
        if page.text is not None:
            text = page.text
        else:
            done += 1
            progress(f"Reading page {i} of {len(pages)}" if to_read > 1 else "Reading the page")
            data = _post(
                {
                    "model": settings.ollama_model,
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": settings.ollama_num_ctx},
                    "messages": [
                        {
                            "role": "user",
                            "content": TRANSCRIBE_PROMPT,
                            "images": [base64.b64encode(page.image or b"").decode("ascii")],
                        }
                    ],
                }
            )
            text = (data.get("message") or {}).get("content", "").strip()
        texts.append(f"--- Page {i} ---\n{text}" if len(pages) > 1 else text)
    transcript = "\n\n".join(texts)
    if len(transcript) < 40:
        raise ExtractionError("No readable text found. Take the photo in good light, straight from above.")
    return transcript


def extract_letter_ollama(
    files: list[tuple[bytes, str]], progress: Progress = _no_progress
) -> tuple[LetterExtraction, str]:
    progress("Preparing pages")
    pages = to_pages(files)
    transcript = transcribe(pages, progress)
    progress("Understanding the letter")
    # Pass 2: structured extraction from the text, constrained to the JSON schema.
    data = _post(
        {
            "model": settings.ollama_model,
            "stream": False,
            "format": SCHEMA,
            "options": {"temperature": 0, "num_ctx": settings.ollama_num_ctx},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + LOCAL_HINTS},
                {
                    "role": "user",
                    "content": "Here is the transcribed letter:\n\n"
                    + transcript
                    + "\n\nExtract it into this JSON schema:\n"
                    + json.dumps(SCHEMA, ensure_ascii=False),
                },
            ],
        }
    )
    content = (data.get("message") or {}).get("content", "")
    try:
        result = LetterExtraction.model_validate_json(content)
    except ValidationError as e:
        log.warning("Ollama returned invalid JSON: %s", content[:500])
        raise ExtractionError("The local model's answer didn't match the expected format. Please try again.") from e

    # Pass 3: deterministic cross-check of dates, IBAN and reference numbers against the transcript.
    changes = apply_transcript(result, transcript)
    if changes:
        log.info("Transcript cross-check changed: %s", "; ".join(changes))
    # Small local models tend to be over-confident; never let them claim more than 0.9.
    result.confidence = min(result.confidence, 0.9)
    return result, f"ollama:{settings.ollama_model}"
