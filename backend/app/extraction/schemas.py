"""Structured-output schema the vision model fills in for every letter.

Dates are ISO strings (YYYY-MM-DD) so the model copies them rather than
reasons about them; the deadline engine parses and computes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.knowledge.taxonomy import LETTER_TYPES

LetterTypeId = Literal[tuple(LETTER_TYPES.keys())]  # type: ignore[valid-type]


class ReferenceNumber(BaseModel):
    label: str = Field(description="e.g. Steuernummer, Aktenzeichen, Beitragsnummer, Steuer-ID")
    value: str = Field(description="Exactly as printed")


class Amount(BaseModel):
    label: str = Field(description="What the amount is, in English, e.g. 'Refund', 'Amount due'")
    amount_eur: float = Field(description="Positive number in euros")
    direction: Literal["you_receive", "you_pay", "info"]
    due_date: str | None = Field(default=None, description="ISO date if a payment date is printed")


class Payment(BaseModel):
    recipient: str | None = None
    iban: str | None = Field(default=None, description="IBAN without spaces")
    bic: str | None = None
    reference: str | None = Field(default=None, description="Verwendungszweck exactly as printed")


class ExplicitDeadline(BaseModel):
    description: str = Field(description="In English: what must happen by this date")
    date: str = Field(description="ISO date as printed in the letter")


class AppealPeriod(BaseModel):
    length: int = Field(description="Number from the Rechtsbehelfsbelehrung, usually 1")
    unit: Literal["days", "weeks", "months"]
    remedy: str = Field(description="German name, e.g. Einspruch, Widerspruch, Klage")


class LineTranslation(BaseModel):
    de: str
    en: str


class LetterExtraction(BaseModel):
    sender_name: str = Field(description="Authority name as printed, e.g. 'Finanzamt Berlin-Mitte'")
    sender_category: Literal["finanzamt", "auslaenderbehoerde", "beitragsservice", "other"]
    letter_type: LetterTypeId = Field(description="Best matching id from the taxonomy")  # type: ignore[valid-type]
    title: str = Field(description="Short English title, e.g. 'Income tax assessment 2025'")
    letter_date: str | None = Field(default=None, description="Date printed on the letter (ISO)")
    sender_address: str | None = Field(default=None, description="Postal address for replies, lines separated by \\n")
    recipient_name: str | None = None
    reference_numbers: list[ReferenceNumber] = Field(default_factory=list)
    amounts: list[Amount] = Field(default_factory=list)
    payment: Payment | None = None
    explicit_deadlines: list[ExplicitDeadline] = Field(default_factory=list)
    appeal_period: AppealPeriod | None = Field(
        default=None, description="Only if the letter contains a Rechtsbehelfsbelehrung"
    )
    delivery: Literal["post", "electronic", "unknown"] = "post"
    tldr: str = Field(description="One or two plain-English sentences: what this is and what it means for the reader")
    details: str = Field(description="A short plain-English paragraph with the important details")
    check_this: list[str] = Field(
        default_factory=list,
        description="Things the reader should double-check, e.g. rejected deductions, wrong address",
    )
    required_actions: list[str] = Field(default_factory=list, description="Concrete actions in English")
    line_by_line: list[LineTranslation] = Field(
        default_factory=list, description="Key sentences: German original and English translation"
    )
    glossary_terms: list[str] = Field(default_factory=list, description="Amtsdeutsch terms used in the letter")
    confidence: float = Field(description="0.0-1.0: how sure you are about the extraction overall")
    uncertain_fields: list[str] = Field(
        default_factory=list, description="Names of fields that were hard to read or guessed"
    )
