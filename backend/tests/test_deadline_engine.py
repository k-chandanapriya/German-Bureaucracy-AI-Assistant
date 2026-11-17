from datetime import date

import pytest

from app.deadlines.engine import (
    DeadlineInput,
    Delivery,
    LegalBasis,
    PeriodUnit,
    compute_deadline,
    is_working_day,
    notification_days,
)


def tax_objection(letter_date: date, land: str = "BE") -> DeadlineInput:
    return DeadlineInput(
        bundesland=land,
        letter_date=letter_date,
        legal_basis=LegalBasis.AO,
        period_length=1,
        period_unit=PeriodUnit.MONTHS,
        label="Einspruch",
    )


def test_example_from_spec_1_dec_2025():
    # 1 Dec 2025 + 4 days = 5 Dec → + 1 month = Mon 5 Jan 2026
    res = compute_deadline(tax_objection(date(2025, 12, 1)))
    assert res.notification_date == date(2025, 12, 5)
    assert res.due_date == date(2026, 1, 5)


def test_three_day_rule_before_2025():
    assert notification_days(date(2024, 12, 31)) == 3
    assert notification_days(date(2025, 1, 1)) == 4


def test_ao_notification_day_on_weekend_moves():
    # Wed 3 Sep 2025 + 4 = Sun 7 Sep → Mon 8 Sep → + 1 month = Wed 8 Oct
    res = compute_deadline(tax_objection(date(2025, 9, 3)))
    assert res.notification_date == date(2025, 9, 8)
    assert res.due_date == date(2025, 10, 8)


def test_vwvfg_notification_day_does_not_move():
    inp = DeadlineInput(
        bundesland="BE",
        letter_date=date(2025, 9, 3),
        legal_basis=LegalBasis.VWVFG,
        period_length=1,
        period_unit=PeriodUnit.MONTHS,
    )
    res = compute_deadline(inp)
    assert res.notification_date == date(2025, 9, 7)
    assert res.due_date == date(2025, 10, 7)


def test_month_end_clamp():
    # posted 27 Jan 2026 + 4 = 31 Jan (Sat) → AO moves it to Mon 2 Feb → 2 Mar
    res = compute_deadline(tax_objection(date(2026, 1, 27)))
    assert res.notification_date == date(2026, 2, 2)
    assert res.due_date == date(2026, 3, 2)

    # VwVfG: 31 Jan stays → + 1 month = 28 Feb 2026 (Sat) → Mon 2 Mar
    inp = DeadlineInput(
        bundesland="BE",
        letter_date=date(2026, 1, 27),
        legal_basis=LegalBasis.VWVFG,
        period_length=1,
        period_unit=PeriodUnit.MONTHS,
    )
    res = compute_deadline(inp)
    assert res.notification_date == date(2026, 1, 31)
    assert any("Saturday" in s for s in res.steps)
    assert res.due_date == date(2026, 3, 2)


def test_state_specific_holiday():
    # Reformation Day (31 Oct) is a holiday in Brandenburg but not in Bavaria.
    assert not is_working_day(date(2025, 10, 31), "BB")
    assert is_working_day(date(2025, 10, 31), "BY")
    # International Women's Day: holiday in Berlin only
    assert not is_working_day(date(2027, 3, 8), "BE")
    assert is_working_day(date(2027, 3, 8), "HH")


def test_deadline_on_state_holiday_rolls_forward():
    # Letter 26 Aug 2025 + 4 = Sat 30 Aug → AO moves to Mon 1 Sep → + 2 months
    # = Sat 1 Nov (All Saints, holiday in BY) → Sun 2 Nov → Mon 3 Nov
    inp = tax_objection(date(2025, 8, 26), "BY")
    inp.period_length = 2
    res = compute_deadline(inp)
    assert res.due_date == date(2025, 11, 3)


def test_weeks_period():
    inp = DeadlineInput(
        bundesland="HH",
        letter_date=date(2026, 11, 2),
        legal_basis=LegalBasis.VWVFG,
        period_length=2,
        period_unit=PeriodUnit.WEEKS,
    )
    res = compute_deadline(inp)
    assert res.notification_date == date(2026, 11, 6)
    assert res.due_date == date(2026, 11, 20)


def test_known_receipt_date():
    inp = DeadlineInput(
        bundesland="BE",
        delivery=Delivery.KNOWN,
        received_date=date(2026, 11, 10),
        legal_basis=LegalBasis.VWVFG,
        period_length=1,
        period_unit=PeriodUnit.MONTHS,
    )
    assert compute_deadline(inp).due_date == date(2026, 12, 10)


def test_explicit_due_date_is_kept_conservative():
    inp = DeadlineInput(bundesland="BE", explicit_due_date=date(2026, 11, 28))  # Saturday
    res = compute_deadline(inp)
    assert res.due_date == date(2026, 11, 28)
    assert res.kind == "explicit"
    assert res.warnings


def test_earlier_explicit_date_wins_over_period():
    inp = tax_objection(date(2025, 12, 1))
    inp.explicit_due_date = date(2025, 12, 20)
    assert compute_deadline(inp).due_date == date(2025, 12, 20)


def test_unknown_bundesland():
    with pytest.raises(ValueError):
        compute_deadline(tax_objection(date(2025, 12, 1), "XX"))


def test_missing_inputs():
    with pytest.raises(ValueError):
        compute_deadline(DeadlineInput(bundesland="BE", letter_date=date(2025, 1, 1)))
