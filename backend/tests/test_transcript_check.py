from app.extraction.samples import sample_extraction
from app.extraction.transcript_check import (
    apply_transcript,
    find_appeal_period,
    find_letter_date,
    find_payment_schedule,
)

LETTER = """Finanzamt Hamburg-Nord
Steuernummer: 43/123/45678
Datum: 09.11.2026

Bescheid über Vorauszahlungen zur Einkommensteuer
10.03.2027 1.150,00 €
10.06.2027 1.150,00 €

Empfänger: Finanzkasse Hamburg
IBAN: DE89 3704 0044 0532 0130 00
BIC: COBADEFFXXX
Verwendungszweck: 43/123/45678 ESt-VZ 2027

Rechtsbehelfsbelehrung
Dieser Bescheid kann mit dem Einspruch angefochten werden. Die Frist für die Einlegung
des Einspruchs beträgt einen Monat.
"""


def test_find_letter_date_variants():
    assert find_letter_date("Datum: 09.11.2026") == "2026-11-09"
    assert find_letter_date("Köln, den 2.11.2026") == "2026-11-02"
    assert find_letter_date("Datum: 31.02.2026") is None
    assert find_letter_date("nothing here") is None


def test_find_appeal_period():
    p = find_appeal_period(LETTER)
    assert (p.length, p.unit, p.remedy) == (1, "months", "Einspruch")
    p = find_appeal_period("Rechtsbehelfsbelehrung: Widerspruch innerhalb von zwei Wochen")
    assert (p.length, p.unit, p.remedy) == (2, "weeks", "Widerspruch")
    assert find_appeal_period("Bitte zahlen Sie bis zum 01.12.2026.") is None


def test_payment_schedule():
    s = find_payment_schedule(LETTER)
    assert [(a.due_date, a.amount_eur) for a in s] == [("2027-03-10", 1150.0), ("2027-06-10", 1150.0)]


def test_apply_fills_missing_fields():
    ex = sample_extraction("steuerbescheid")
    ex.letter_date = None
    ex.reference_numbers = []
    ex.appeal_period = None
    ex.payment = None
    ex.amounts = []
    changes = apply_transcript(ex, LETTER)
    assert ex.letter_date == "2026-11-09"
    assert ex.reference_numbers[0].value == "43/123/45678"
    assert ex.payment.iban == "DE89370400440532013000"
    assert ex.payment.bic == "COBADEFFXXX"
    assert ex.payment.recipient == "Finanzkasse Hamburg"
    assert ex.appeal_period.remedy == "Einspruch"
    assert len(ex.amounts) == 2
    assert changes


def test_apply_corrects_garbled_iban_and_keeps_good_data():
    ex = sample_extraction("rundfunk")
    ex.payment.iban = "DE02120300000000202099"  # model misread digits
    apply_transcript(ex, "Datum: 02.11.2026\nIBAN: DE02 1203 0000 0000 2020 51")
    assert ex.payment.iban == "DE02120300000000202051"
    assert ex.letter_date == "2026-11-02"
    assert len([a for a in ex.amounts if a.due_date]) == 1  # existing schedule untouched
