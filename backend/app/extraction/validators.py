"""Cheap deterministic cross-checks on what the model extracted.

Anything that fails here is flagged in the UI as "please confirm with the
original letter" rather than silently trusted.
"""

from __future__ import annotations

import re
from datetime import date

from app.extraction.schemas import LetterExtraction


def parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def iban_is_valid(iban: str) -> bool:
    s = re.sub(r"\s+", "", iban).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", s):
        return False
    if s.startswith("DE") and len(s) != 22:
        return False
    rearranged = s[4:] + s[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


def format_iban(iban: str) -> str:
    s = re.sub(r"\s+", "", iban).upper()
    return " ".join(s[i : i + 4] for i in range(0, len(s), 4))


def check_extraction(ex: LetterExtraction, today: date | None = None) -> list[str]:
    """Return human-readable warnings about fields the user should confirm."""
    today = today or date.today()
    warnings: list[str] = []

    letter_date = parse_iso(ex.letter_date)
    if ex.letter_date and not letter_date:
        warnings.append(f"Couldn't read the letter date ('{ex.letter_date}'). Please enter it.")
    elif not ex.letter_date:
        warnings.append("No letter date found. Deadlines can't be computed until you enter it.")
    elif letter_date and letter_date > today:
        warnings.append("The letter date is in the future. Please check it.")
    elif letter_date and (today - letter_date).days > 400:
        warnings.append("The letter is more than a year old. Please check the date.")

    if ex.payment and ex.payment.iban and not iban_is_valid(ex.payment.iban):
        warnings.append("The IBAN failed its checksum. Copy it from the original letter.")

    for d in ex.explicit_deadlines:
        if not parse_iso(d.date):
            warnings.append(f"Couldn't read the date for '{d.description}'.")

    for a in ex.amounts:
        if a.amount_eur < 0 or a.amount_eur > 1_000_000:
            warnings.append(f"The amount for '{a.label}' looks wrong. Please check it.")

    if ex.confidence < 0.7:
        warnings.append("The letter was hard to read. Please check every field against the original.")
    for f in ex.uncertain_fields:
        warnings.append(f"Uncertain: {f}")
    return warnings
