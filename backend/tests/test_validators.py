from datetime import date

from app.extraction.samples import SAMPLES, sample_extraction
from app.extraction.validators import check_extraction, format_iban, iban_is_valid


def test_iban_checksum():
    assert iban_is_valid("DE89 3704 0044 0532 0130 00")
    assert iban_is_valid("DE02120300000000202051")
    assert not iban_is_valid("DE89370400440532013001")
    assert not iban_is_valid("DE8937040044053201300")  # too short for DE


def test_format_iban():
    assert format_iban("de89370400440532013000") == "DE89 3704 0044 0532 0130 00"


def test_samples_are_valid_and_clean():
    for sid in SAMPLES:
        ex = sample_extraction(sid)
        assert check_extraction(ex, today=date(2026, 11, 23)) == []


def test_bad_fields_are_flagged():
    ex = sample_extraction("rundfunk")
    ex.payment.iban = "DE02120300000000202052"
    ex.letter_date = "2027-01-01"
    ex.confidence = 0.4
    warnings = check_extraction(ex, today=date(2026, 11, 23))
    assert any("IBAN" in w for w in warnings)
    assert any("future" in w for w in warnings)
    assert any("hard to read" in w for w in warnings)
