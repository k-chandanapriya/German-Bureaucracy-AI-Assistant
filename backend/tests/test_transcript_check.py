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


FIKTION = """Ausländerbehörde
Vorläufige Bescheinigung
(gilt nur bis zur Aushändigung des elektronischen Aufenthaltstitels)
Geburtsdatum: 01-02-1990
Pass: Y1234567 gültig bis 15-08-2029
... dem Antrag auf Erteilung einer Aufenthaltserlaubnis
(Arbeitsplatzsuche nach Studium in Deutschland) vom 01-10-2026 bis 30-09-2028 entsprochen wurde.
Ort, Datum
Datum
Musterstadt, LRA Musterkreis
05.11.2026
Unterschrift
"""


def test_dash_dates_and_date_on_next_line():
    assert find_letter_date(FIKTION) == "2026-11-05"  # not the Geburtsdatum


def test_validity_and_passport_deadlines():
    from app.extraction.transcript_check import find_validity_deadlines

    found = {(d.date, d.description.split(":")[0]) for d in find_validity_deadlines(FIKTION)}
    assert found == {("2029-08-15", "Your passport expires"), ("2028-09-30", "Valid until")}
    assert [d.date for d in find_validity_deadlines("Bitte zahlen Sie den Betrag bis zum 30.11.2026.")] == ["2026-11-30"]


def test_fiktion_card_gets_deadlines():
    from app.services.analysis import build_card

    ex = sample_extraction("abh_termin")
    ex.letter_type, ex.letter_date, ex.explicit_deadlines = "abh_fiktionsbescheinigung", None, []
    apply_transcript(ex, FIKTION)
    card = build_card(ex, "BW")
    assert [d["due_date"] for d in card["deadlines"]] == ["2028-09-30", "2029-08-15"]
    assert not any("No letter date" in w for w in card["warnings"])
