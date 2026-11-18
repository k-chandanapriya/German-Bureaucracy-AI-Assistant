"""Read a letter (photo or PDF) with Claude vision and return structured data."""

from __future__ import annotations

import base64
import logging

import anthropic

from app.config import settings
from app.extraction.schemas import LetterExtraction
from app.knowledge.taxonomy import LETTER_TYPES

log = logging.getLogger(__name__)

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PDF_TYPE = "application/pdf"


class ExtractionError(RuntimeError):
    pass


def _taxonomy_text() -> str:
    return "\n".join(
        f"- {t.id}: {t.name_de} ({t.name_en}), sender={t.sender}" for t in LETTER_TYPES.values()
    )


SYSTEM_PROMPT = f"""You read official German letters (Amtspost) for people who don't speak German well.
Extract the facts exactly as printed and explain them in plain English.

Rules:
- Copy dates as printed, converted to ISO format (YYYY-MM-DD). Do not calculate any deadline yourself:
  a separate engine computes deadlines from the letter date and the appeal period.
- appeal_period: fill it only from the Rechtsbehelfsbelehrung (e.g. "innerhalb eines Monats nach Bekanntgabe").
- explicit_deadlines: only dates that are printed in the letter ("bis zum 15.12.2026").
- Copy IBAN, reference numbers and Verwendungszweck character for character.
- Amounts: positive euro numbers; set direction from the reader's point of view.
- Don't give legal advice or tell the reader whether to appeal. Describe what the letter says and what
  happens if they do nothing.
- If something is unreadable, leave it empty, lower the confidence and list it in uncertain_fields.

Letter types (pick the closest id, or "other"):
{_taxonomy_text()}
"""


def _content_block(data: bytes, media_type: str) -> dict:
    b64 = base64.standard_b64encode(data).decode("utf-8")
    if media_type == PDF_TYPE:
        return {"type": "document", "source": {"type": "base64", "media_type": PDF_TYPE, "data": b64}}
    if media_type in IMAGE_TYPES:
        return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}}
    raise ExtractionError(f"Unsupported file type: {media_type}. Upload a JPG, PNG, WEBP or PDF.")


def _call(client: anthropic.Anthropic, model: str, files: list[tuple[bytes, str]]) -> LetterExtraction:
    content = [_content_block(d, m) for d, m in files]
    content.append(
        {
            "type": "text",
            "text": "Here is the letter (all pages, in order). Extract it into the schema.",
        }
    )
    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": content}],
        output_format=LetterExtraction,
    )
    if response.stop_reason == "refusal":
        raise ExtractionError("The model declined to read this document.")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        raise ExtractionError("The model's answer was incomplete. Please try again.")
    return response.parsed_output


def extract_letter(files: list[tuple[bytes, str]]) -> tuple[LetterExtraction, str]:
    """Return the extraction and the model that produced it.

    The fast model reads most letters; if it reports low confidence the
    letter is re-read with the stronger model.
    """
    try:
        client = anthropic.Anthropic()
        result = _call(client, settings.extraction_model, files)
        model = settings.extraction_model
        if result.confidence < settings.escalation_threshold and settings.escalation_model:
            log.info("Low confidence %.2f, escalating to %s", result.confidence, settings.escalation_model)
            result = _call(client, settings.escalation_model, files)
            model = settings.escalation_model
        return result, model
    except anthropic.AuthenticationError as e:
        raise ExtractionError("Anthropic API key is missing or invalid. Set ANTHROPIC_API_KEY in backend/.env.") from e
    except anthropic.RateLimitError as e:
        raise ExtractionError("The AI service is busy (rate limit). Try again in a minute.") from e
    except anthropic.BadRequestError as e:
        raise ExtractionError(f"The AI service rejected the request: {e.message}") from e
    except anthropic.APIStatusError as e:
        raise ExtractionError(f"AI service error ({e.status_code}). Try again.") from e
    except anthropic.APIConnectionError as e:
        raise ExtractionError("Could not reach the AI service. Check your connection.") from e
    except anthropic.AnthropicError as e:
        raise ExtractionError(f"AI service error: {e}") from e
    except TypeError as e:
        # The SDK raises TypeError when no credentials are configured at all.
        if "authentication" in str(e):
            raise ExtractionError(
                "No Anthropic API key configured. Add ANTHROPIC_API_KEY to backend/.env and restart "
                "the backend, or try one of the sample letters."
            ) from e
        raise
