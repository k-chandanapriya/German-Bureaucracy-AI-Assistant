"""Deterministic cross-check of an extraction against the letter's transcript.

Small local models sometimes leave critical fields empty or garble them,
while their plain transcription of the page is very reliable. These
patterns pull the fields that matter most for deadlines and payments
straight from the text, and fill or correct the extraction.
"""

from __future__ import annotations

import re
from datetime import date

from app.extraction.schemas import (
    Amount,
    AppealPeriod,
    ExplicitDeadline,
    LetterExtraction,
    Payment,
    ReferenceNumber,
)
from app.extraction.validators import iban_is_valid, parse_iso

# 12.11.2026, 12. 11. 2026, 12-11-2026, 12/11/2026
_DATE = r"(\d{1,2})[.\-/]\s?(\d{1,2})[.\-/]\s?(\d{4})"
_LETTER_DATE_PATTERNS = [
    # "Datum" as its own word (not Geburtsdatum); the date may be on the next line
    rf"(?:\bDatum|Ausgabedatum|Bescheiddatum|Ausstellungsdatum|[Aa]usgestellt am|Schreiben vom)\s*:?\s*{_DATE}",
    rf"^[A-ZÄÖÜ][\wäöüß\- ]+,\s*(?:den\s+)?{_DATE}\s*$",  # "Berlin, 12.11.2026"
    # Forms: a "Datum" label, then the place, then the date on its own line
    rf"^\s*Datum\s*:?\s*\n(?:[^\n]*\n){{0,2}}?\s*{_DATE}\s*$",
]
_IBAN = re.compile(r"\b(DE\d{2}(?:\s?\d{4}){4}\s?\d{2})\b")
_BIC = re.compile(r"\bBIC\s*:?\s*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b")
_REFERENCE = re.compile(r"Verwendungszweck\s*:?\s*(.+)")
_RECIPIENT = re.compile(r"(?:Empfänger|Kontoinhaber)\s*:?\s*(.+)")
_REF_NUMBERS = [
    ("Steuernummer", re.compile(r"Steuernummer\s*:?\s*(\d{2,3}/\d{3}/\d{4,5})")),
    ("Steuer-ID", re.compile(r"(?:Steuer-?ID|Identifikationsnummer)\s*:?\s*(\d{2}\s?\d{3}\s?\d{3}\s?\d{3})")),
    ("Beitragsnummer", re.compile(r"Beitragsnummer\s*:?\s*(\d{3}\s?\d{3}\s?\d{3})")),
    ("Aktenzeichen", re.compile(r"(?:Aktenzeichen|Az\.|Geschäftszeichen)\s*:?\s*([A-Z0-9][\w/\-. ]{3,30}?)(?:\s{2,}|$)", re.M)),
]
_PERIODS = {
    r"(?:einen|eines)\s+Monats?": (1, "months"),
    r"(?:zwei|2)\s+Wochen": (2, "weeks"),
    r"(?:vier|4)\s+Wochen": (4, "weeks"),
    r"(?:zwei|2)\s+Monaten?": (2, "months"),
}
_REMEDIES = ("Einspruch", "Widerspruch", "Klage")
# A payment schedule line: "10.03.2027   1.150,00 €" (date and euro amount on one line)
_SCHEDULE_LINE = re.compile(rf"^\s*(?:am\s+|bis\s+(?:zum\s+)?)?{_DATE}\s+(\d{{1,3}}(?:\.\d{{3}})*,\d{{2}})\s*(?:€|EUR)\s*$", re.M)


def _euro(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def find_payment_schedule(text: str) -> list[Amount]:
    out = []
    for m in _SCHEDULE_LINE.finditer(text):
        if iso := _iso(m):
            out.append(Amount(label="Instalment", amount_eur=_euro(m.group(4)), direction="you_pay", due_date=iso))
    return out


def _iso(m: re.Match) -> str | None:
    """ISO date from the first three groups (day, month, year) of a match."""
    d, mth, y = (int(x) for x in m.groups()[:3])
    try:
        return date(y, mth, d).isoformat()
    except ValueError:
        return None


def find_letter_date(text: str) -> str | None:
    for pat in _LETTER_DATE_PATTERNS:
        m = re.search(pat, text, re.M)
        if m and (iso := _iso(m)):
            return iso
    return None


def find_appeal_period(text: str) -> AppealPeriod | None:
    idx = text.find("Rechtsbehelfsbelehrung")
    section = text[idx:] if idx >= 0 else text
    remedy = next((r for r in _REMEDIES if r in section), None)
    if not remedy:
        return None
    for pat, (length, unit) in _PERIODS.items():
        if re.search(pat, section):
            return AppealPeriod(length=length, unit=unit, remedy=remedy)
    return None


# "gültig bis 31-12-2027", "vom 01.01.2026 bis 31.12.2027", "Pass … gültig bis …"
_VALID_UNTIL = re.compile(rf"(?:gültig\s+bis|vom\s+{_DATE}\s+bis)\s+(?:zum\s+)?{_DATE}", re.I)
_PAY_BY = re.compile(rf"(?:zahlbar|zahlen Sie|überweisen Sie)[^\n]*?bis\s+(?:zum\s+)?{_DATE}", re.I)


def find_validity_deadlines(text: str) -> list[ExplicitDeadline]:
    """End dates of permits, certificates and passports printed in the letter."""
    out: list[ExplicitDeadline] = []
    for line in text.splitlines():
        for m in _VALID_UNTIL.finditer(line):
            d, mth, y = m.groups()[-3:]
            try:
                iso = date(int(y), int(mth), int(d)).isoformat()
            except ValueError:
                continue
            if re.search(r"\bPass\b|Reisepass|Passport", line[: m.start()], re.I):
                desc = "Your passport expires: renew it in time (the immigration office needs a valid passport)"
            else:
                desc = "Valid until: apply for an extension before this date"
            out.append(ExplicitDeadline(description=desc, date=iso))
    for m in _PAY_BY.finditer(text):
        d, mth, y = m.groups()[-3:]
        try:
            out.append(ExplicitDeadline(description="Pay by this date", date=date(int(y), int(mth), int(d)).isoformat()))
        except ValueError:
            pass
    return out


def apply_transcript(ex: LetterExtraction, text: str) -> list[str]:
    """Fill or correct fields from the transcript. Returns a list of what changed."""
    changes: list[str] = []

    letter_date = find_letter_date(text)
    if letter_date and parse_iso(ex.letter_date) != parse_iso(letter_date):
        changes.append(f"letter_date {ex.letter_date!r} → {letter_date}")
        ex.letter_date = letter_date

    known = {r.value.replace(" ", "") for r in ex.reference_numbers}
    for label, pat in _REF_NUMBERS:
        m = pat.search(text)
        if m and m.group(1).replace(" ", "") not in known:
            ex.reference_numbers.append(ReferenceNumber(label=label, value=m.group(1).strip()))
            known.add(m.group(1).replace(" ", ""))
            changes.append(f"added {label}")

    m = _IBAN.search(text)
    if m and iban_is_valid(m.group(1)):
        iban = m.group(1).replace(" ", "")
        if ex.payment is None:
            ex.payment = Payment()
        if (ex.payment.iban or "").replace(" ", "") != iban:
            changes.append("iban from transcript")
            ex.payment.iban = iban
        if not ex.payment.bic and (b := _BIC.search(text)):
            ex.payment.bic = b.group(1)
        if not ex.payment.reference and (r := _REFERENCE.search(text)):
            ex.payment.reference = r.group(1).strip()
        if not ex.payment.recipient and (r := _RECIPIENT.search(text)):
            ex.payment.recipient = r.group(1).strip()

    known_dates = {d.date for d in ex.explicit_deadlines}
    for dl in find_validity_deadlines(text):
        if dl.date not in known_dates:
            ex.explicit_deadlines.append(dl)
            known_dates.add(dl.date)
            changes.append(f"deadline: {dl.description.split(':')[0]}")

    if not any(a.direction == "you_pay" and a.due_date for a in ex.amounts):
        schedule = find_payment_schedule(text)
        if schedule:
            ex.amounts.extend(schedule)
            changes.append(f"added {len(schedule)} scheduled payments")

    if ex.appeal_period is None and (period := find_appeal_period(text)):
        ex.appeal_period = period
        changes.append("appeal period from Rechtsbehelfsbelehrung")

    return changes
