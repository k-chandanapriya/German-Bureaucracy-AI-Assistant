"""Turn a model extraction into the result card: deadlines, actions, glossary."""

from __future__ import annotations

from datetime import date

from app.deadlines.engine import (
    DeadlineInput,
    Delivery,
    LegalBasis,
    PeriodUnit,
    compute_deadline,
)
from app.extraction.schemas import LetterExtraction
from app.extraction.validators import check_extraction, format_iban, iban_is_valid, parse_iso
from app.knowledge.glossary import GLOSSARY
from app.knowledge.taxonomy import SENDERS, get_letter_type
from app.replies.templates import REPLY_TEMPLATES


def compute_deadlines(
    ex: LetterExtraction,
    bundesland: str,
    received_date: date | None = None,
) -> list[dict]:
    lt = get_letter_type(ex.letter_type)
    letter_date = parse_iso(ex.letter_date)
    results: list[dict] = []
    seen: set[str] = set()

    appeal = ex.appeal_period
    if appeal is None and lt.appeal_months:
        # The taxonomy knows this letter type is a Bescheid with a 1-month period.
        appeal_len, appeal_unit, remedy = lt.appeal_months, PeriodUnit.MONTHS, lt.appeal_name
    elif appeal is not None:
        appeal_len, appeal_unit, remedy = appeal.length, PeriodUnit(appeal.unit), appeal.remedy
    else:
        appeal_len = None

    if appeal_len and (letter_date or received_date):
        inp = DeadlineInput(
            bundesland=bundesland,
            letter_date=letter_date,
            legal_basis=lt.legal_basis,
            delivery=Delivery.KNOWN if received_date else Delivery.POST,
            received_date=received_date,
            period_length=appeal_len,
            period_unit=appeal_unit,
            label=f"Last day to file {remedy}" if remedy else "Last day to object",
        )
        r = compute_deadline(inp).to_dict()
        r["type"] = "appeal"
        results.append(r)

    def add_explicit(label: str, iso: str | None, kind: str) -> None:
        d = parse_iso(iso)
        if not d:
            return
        key = f"{d.isoformat()}:{kind}"
        if key in seen:
            return
        seen.add(key)
        r = compute_deadline(
            DeadlineInput(bundesland=bundesland, explicit_due_date=d, label=label, legal_basis=LegalBasis.NONE)
        ).to_dict()
        r["type"] = kind
        results.append(r)

    for d in ex.explicit_deadlines:
        kind = "appointment" if "appointment" in d.description.lower() else "action"
        add_explicit(d.description, d.date, kind)
    for a in ex.amounts:
        if a.direction == "you_pay" and a.due_date:
            add_explicit(f"Pay €{a.amount_eur:,.2f} ({a.label.lower()})", a.due_date, "payment")

    # Payments that duplicate an explicit action deadline on the same day: keep the payment one.
    by_date: dict[str, dict] = {}
    for r in results:
        prev = by_date.get(r["due_date"])
        if prev is None or (prev["type"] == "action" and r["type"] == "payment"):
            by_date[r["due_date"]] = r
    ordered = sorted(by_date.values(), key=lambda r: r["due_date"])
    return ordered


def build_card(ex: LetterExtraction, bundesland: str, received_date: date | None = None) -> dict:
    lt = get_letter_type(ex.letter_type)
    deadlines = compute_deadlines(ex, bundesland, received_date)
    warnings = check_extraction(ex)

    payment = None
    if ex.payment and ex.payment.iban:
        total = next(
            (a.amount_eur for a in reversed(ex.amounts) if a.direction == "you_pay"),
            None,
        )
        payment = {
            "recipient": ex.payment.recipient or ex.sender_name,
            "iban": format_iban(ex.payment.iban),
            "iban_valid": iban_is_valid(ex.payment.iban),
            "bic": ex.payment.bic,
            "reference": ex.payment.reference,
            "amount_eur": total,
        }

    terms = {t: GLOSSARY[t] for t in ex.glossary_terms if t in GLOSSARY}
    templates = [
        {"id": tid, "title": REPLY_TEMPLATES[tid].title_en, "channel": REPLY_TEMPLATES[tid].channel_note}
        for tid in lt.reply_templates
        if tid in REPLY_TEMPLATES
    ]

    return {
        "sender": {
            "name": ex.sender_name,
            "category": ex.sender_category,
            "label": SENDERS[ex.sender_category],
            "address": ex.sender_address,
        },
        "letter_type": lt.to_dict(),
        "title": ex.title,
        "letter_date": ex.letter_date,
        "severity": lt.severity,
        "tldr": ex.tldr,
        "details": ex.details,
        "what_it_is": lt.what_it_is,
        "if_ignored": lt.ignore_consequence,
        "check_this": ex.check_this,
        "required_actions": ex.required_actions,
        "reference_numbers": [r.model_dump() for r in ex.reference_numbers],
        "amounts": [a.model_dump() for a in ex.amounts],
        "payment": payment,
        "deadlines": deadlines,
        "checklist": list(lt.checklist),
        "reply_templates": templates,
        "line_by_line": [line.model_dump() for line in ex.line_by_line],
        "glossary": terms,
        "confidence": ex.confidence,
        "warnings": warnings,
        "bundesland": bundesland,
        "disclaimer": (
            "Information, not legal or tax advice. Always check dates and amounts against the "
            "original letter. For decisions such as whether to appeal, ask a Steuerberater, a "
            "Lohnsteuerhilfeverein or a lawyer."
        ),
    }
