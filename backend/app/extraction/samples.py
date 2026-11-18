"""Fictional sample letters so the app can be tried without an API key.

All names, numbers and IBANs are made up (the IBANs are public textbook
examples with valid checksums).
"""

from __future__ import annotations

from app.extraction.schemas import LetterExtraction

SAMPLES: dict[str, dict] = {
    "steuerbescheid": {
        "label": "Finanzamt: income tax assessment",
        "preview": (
            "Finanzamt Berlin-Mitte · Steuernummer 34/567/89012\n"
            "Bescheid für 2025 über Einkommensteuer … Erstattung 1.240,00 € …\n"
            "Rechtsbehelfsbelehrung: Der Bescheid kann mit dem Einspruch angefochten werden … "
            "innerhalb eines Monats nach Bekanntgabe …"
        ),
        "extraction": {
            "sender_name": "Finanzamt Berlin-Mitte",
            "sender_category": "finanzamt",
            "letter_type": "fa_einkommensteuerbescheid",
            "title": "Income tax assessment 2025",
            "letter_date": "2026-11-12",
            "sender_address": "Finanzamt Berlin-Mitte\nNeue Jakobstraße 6-7\n10179 Berlin",
            "recipient_name": "Alex Example",
            "reference_numbers": [
                {"label": "Steuernummer", "value": "34/567/89012"},
                {"label": "Steuer-ID", "value": "12 345 678 901"},
            ],
            "amounts": [
                {"label": "Refund", "amount_eur": 1240.00, "direction": "you_receive", "due_date": None},
                {"label": "Home-office costs not accepted", "amount_eur": 890.00, "direction": "info", "due_date": None},
            ],
            "payment": None,
            "explicit_deadlines": [],
            "appeal_period": {"length": 1, "unit": "months", "remedy": "Einspruch"},
            "delivery": "post",
            "tldr": "This is your final tax assessment for 2025. You get €1,240 back, paid to your account within about 1–2 weeks.",
            "details": "The tax office accepted most of your return but did not accept €890 of home-office costs (see 'Erläuterungen' on page 3). The assessment is 'vorläufig' for some points, which is normal.",
            "check_this": [
                "They did not accept your €890 home-office costs (see 'Erläuterungen', page 3).",
                "Check that the refund goes to your current IBAN.",
            ],
            "required_actions": [
                "If you agree: nothing to do, the refund arrives automatically.",
                "If you disagree with the home-office decision: file an Einspruch before the deadline.",
            ],
            "line_by_line": [
                {"de": "Bescheid für 2025 über Einkommensteuer", "en": "Assessment for 2025 of income tax"},
                {"de": "Erstattung: 1.240,00 €", "en": "Refund: €1,240.00"},
                {"de": "Die Aufwendungen für das häusliche Arbeitszimmer konnten nicht berücksichtigt werden.", "en": "The costs for the home office could not be taken into account."},
                {"de": "Der Bescheid kann mit dem Einspruch angefochten werden.", "en": "You can challenge this decision with an objection (Einspruch)."},
            ],
            "glossary_terms": ["Bescheid", "Einspruch", "Rechtsbehelfsbelehrung", "vorläufig", "Erstattung", "Steuernummer"],
            "confidence": 0.95,
            "uncertain_fields": [],
        },
    },
    "rundfunk": {
        "label": "Beitragsservice: fee assessment",
        "preview": (
            "ARD ZDF Deutschlandradio Beitragsservice · Beitragsnummer 123 456 789\n"
            "Festsetzungsbescheid … rückständige Rundfunkbeiträge 01.07.2026 – 30.09.2026 … 55,08 € "
            "zzgl. Säumniszuschlag 8,00 € … Widerspruch innerhalb eines Monats …"
        ),
        "extraction": {
            "sender_name": "ARD ZDF Deutschlandradio Beitragsservice",
            "sender_category": "beitragsservice",
            "letter_type": "rb_festsetzungsbescheid",
            "title": "Broadcasting fee assessment (Jul–Sep 2026)",
            "letter_date": "2026-11-02",
            "sender_address": "ARD ZDF Deutschlandradio Beitragsservice\n50656 Köln",
            "recipient_name": "Alex Example",
            "reference_numbers": [{"label": "Beitragsnummer", "value": "123 456 789"}],
            "amounts": [
                {"label": "Unpaid fees Jul–Sep 2026", "amount_eur": 55.08, "direction": "you_pay", "due_date": None},
                {"label": "Late fee (Säumniszuschlag)", "amount_eur": 8.00, "direction": "you_pay", "due_date": None},
                {"label": "Total to pay", "amount_eur": 63.08, "direction": "you_pay", "due_date": "2026-11-30"},
            ],
            "payment": {
                "recipient": "ARD ZDF Deutschlandradio Beitragsservice",
                "iban": "DE02120300000000202051",
                "bic": "BYLADEM1001",
                "reference": "123456789 Festsetzung",
            },
            "explicit_deadlines": [{"description": "Pay the total amount", "date": "2026-11-30"}],
            "appeal_period": {"length": 1, "unit": "months", "remedy": "Widerspruch"},
            "delivery": "post",
            "tldr": "You haven't paid the broadcasting fee for July–September 2026. They formally set €55.08 plus an €8 late fee: €63.08 in total.",
            "details": "This is a formal decision (Bescheid). If you don't pay or object, it becomes enforceable and the city can collect the money from your bank account.",
            "check_this": [
                "Does someone else in your flat already pay? Then you can deregister (one fee per household).",
                "Do you receive BAföG or Bürgergeld? You may be exempt.",
            ],
            "required_actions": ["Pay €63.08 by 30 Nov 2026, or object (Widerspruch) if the assessment is wrong."],
            "line_by_line": [
                {"de": "Festsetzungsbescheid", "en": "Formal assessment notice"},
                {"de": "Rückständige Rundfunkbeiträge: 55,08 €", "en": "Overdue broadcasting fees: €55.08"},
                {"de": "Säumniszuschlag: 8,00 €", "en": "Late-payment fee: €8.00"},
                {"de": "Gegen diesen Bescheid kann innerhalb eines Monats nach Bekanntgabe Widerspruch erhoben werden.", "en": "You can object to this decision within one month of notification."},
            ],
            "glossary_terms": ["Festsetzung", "Säumniszuschlag", "Widerspruch", "Beitragsnummer", "Vollstreckung"],
            "confidence": 0.93,
            "uncertain_fields": [],
        },
    },
    "abh_termin": {
        "label": "Ausländerbehörde: appointment",
        "preview": (
            "Landesamt für Einwanderung Berlin · Aktenzeichen B-2026-445566\n"
            "Einladung zur persönlichen Vorsprache am 08.12.2026 um 09:30 Uhr … "
            "Bitte bringen Sie folgende Unterlagen mit …"
        ),
        "extraction": {
            "sender_name": "Landesamt für Einwanderung Berlin",
            "sender_category": "auslaenderbehoerde",
            "letter_type": "abh_termin",
            "title": "Appointment for your residence permit",
            "letter_date": "2026-11-16",
            "sender_address": "Landesamt für Einwanderung\nFriedrich-Krause-Ufer 24\n13353 Berlin",
            "recipient_name": "Alex Example",
            "reference_numbers": [{"label": "Aktenzeichen", "value": "B-2026-445566"}],
            "amounts": [{"label": "Fee for the permit", "amount_eur": 100.0, "direction": "you_pay", "due_date": None}],
            "payment": None,
            "explicit_deadlines": [{"description": "Appointment at the immigration office, 09:30", "date": "2026-12-08"}],
            "appeal_period": None,
            "delivery": "post",
            "tldr": "You have an appointment on Tue 8 Dec 2026 at 09:30 to extend your residence permit. Bring all listed documents.",
            "details": "The appointment is for your Blue Card renewal. If you can't attend, ask for a new appointment in writing as early as possible, quoting the Aktenzeichen.",
            "check_this": ["Is your passport valid for at least the next 12 months?"],
            "required_actions": [
                "Put the appointment in your calendar.",
                "Collect the documents on the checklist.",
                "Bring about €100 for the fee (card payment is usually possible).",
            ],
            "line_by_line": [
                {"de": "Einladung zur persönlichen Vorsprache", "en": "Invitation to appear in person"},
                {"de": "Bitte bringen Sie folgende Unterlagen mit", "en": "Please bring the following documents"},
                {"de": "Sollten Sie den Termin nicht wahrnehmen können, teilen Sie uns dies bitte rechtzeitig mit.", "en": "If you can't attend, please let us know in good time."},
            ],
            "glossary_terms": ["Aktenzeichen", "Mitwirkungspflicht", "Fiktionsbescheinigung"],
            "confidence": 0.9,
            "uncertain_fields": [],
        },
    },
}


def sample_extraction(sample_id: str) -> LetterExtraction:
    if sample_id not in SAMPLES:
        raise KeyError(sample_id)
    return LetterExtraction.model_validate(SAMPLES[sample_id]["extraction"])
