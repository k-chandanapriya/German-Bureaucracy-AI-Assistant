"""Deterministic deadline engine for German official letters.

The LLM never computes dates. It only extracts the *inputs* (letter date,
period length, explicit due dates). This module turns those inputs into a
deadline and records every step so the user can see how it was reached.

Rules implemented
-----------------
* Notification fiction for postal letters
  - § 122 Abs. 2 Nr. 1 AO (tax), § 41 Abs. 2 VwVfG (general administration),
    § 37 Abs. 2 SGB X (social law).
  - Letters posted on or after 1 Jan 2025 count as received on the
    **4th day** after posting (Postrechtsmodernisierungsgesetz), before that
    on the 3rd day.
  - For tax letters (AO) the fictional notification day itself moves to the
    next working day if it is a weekend or public holiday (BFH, IX R 68/98).
    For VwVfG / SGB X the courts are split, so we do *not* move it: that gives
    the earlier, conservative date.
* Period calculation (§§ 187-193 BGB, § 108 AO, § 31 VwVfG, § 26 SGB X)
  - The day of the triggering event is not counted (§ 187 Abs. 1 BGB).
  - Month/week periods end on the day with the same number/weekday
    (§ 188 Abs. 2 BGB); if that day does not exist in the end month, on the
    last day of that month (§ 188 Abs. 3 BGB).
  - If the last day is a Saturday, Sunday or public holiday at the place
    where the act has to be done, the period ends on the next working day
    (§ 193 BGB, § 108 Abs. 3 AO, § 31 Abs. 3 VwVfG).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from functools import lru_cache

import holidays
from dateutil.relativedelta import relativedelta

FOUR_DAY_RULE_START = date(2025, 1, 1)

BUNDESLAENDER: dict[str, str] = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen",
}

WEEKDAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class LegalBasis(str, Enum):
    AO = "AO"  # Abgabenordnung: Finanzamt, Familienkasse (partly)
    VWVFG = "VwVfG"  # general administrative law: Ausländerbehörde, Beitragsservice
    SGB_X = "SGB X"  # social law: Jobcenter, Krankenkasse, Elterngeld
    NONE = "none"  # private letters, plain payment dates


class Delivery(str, Enum):
    POST = "post"  # ordinary letter: notification fiction applies
    ELECTRONIC = "electronic"  # ELSTER / e-mail: same fiction (§ 122 Abs. 2a AO)
    KNOWN = "known"  # user knows the actual receipt date (hand delivery, PZU)


class PeriodUnit(str, Enum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


@dataclass
class DeadlineInput:
    bundesland: str
    letter_date: date | None = None
    legal_basis: LegalBasis = LegalBasis.VWVFG
    delivery: Delivery = Delivery.POST
    received_date: date | None = None
    period_length: int | None = None
    period_unit: PeriodUnit | None = None
    explicit_due_date: date | None = None
    label: str = "Deadline"


@dataclass
class DeadlineResult:
    label: str
    due_date: date
    notification_date: date | None
    steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    kind: str = "period"  # "period" | "explicit"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "due_date": self.due_date.isoformat(),
            "due_date_display": fmt(self.due_date),
            "notification_date": self.notification_date.isoformat()
            if self.notification_date
            else None,
            "steps": self.steps,
            "warnings": self.warnings,
            "kind": self.kind,
            "days_left": (self.due_date - date.today()).days,
        }


def fmt(d: date) -> str:
    return f"{WEEKDAYS_EN[d.weekday()]} {d.day} {d.strftime('%b %Y')}"


@lru_cache(maxsize=64)
def _holidays_for(bundesland: str, year: int) -> holidays.HolidayBase:
    if bundesland not in BUNDESLAENDER:
        raise ValueError(f"Unknown Bundesland code: {bundesland}")
    return holidays.Germany(subdiv=bundesland, years=year, language="en_US")


def holiday_name(d: date, bundesland: str) -> str | None:
    return _holidays_for(bundesland, d.year).get(d)


def is_working_day(d: date, bundesland: str) -> bool:
    return d.weekday() < 5 and holiday_name(d, bundesland) is None


def _non_working_reason(d: date, bundesland: str) -> str:
    if d.weekday() == 5:
        return "Saturday"
    if d.weekday() == 6:
        return "Sunday"
    return f"public holiday ({holiday_name(d, bundesland)}) in {BUNDESLAENDER[bundesland]}"


def roll_forward(d: date, bundesland: str, steps: list[str], why: str) -> date:
    """Move to the next working day, logging each skipped day."""
    while not is_working_day(d, bundesland):
        nxt = d + timedelta(days=1)
        steps.append(f"{fmt(d)} is a {_non_working_reason(d, bundesland)} → {why}: {fmt(nxt)}")
        d = nxt
    return d


def notification_days(posting_date: date) -> int:
    return 4 if posting_date >= FOUR_DAY_RULE_START else 3


def notification_date(inp: DeadlineInput, steps: list[str], warnings: list[str]) -> date:
    if inp.delivery == Delivery.KNOWN:
        if not inp.received_date:
            raise ValueError("received_date is required when delivery is 'known'")
        steps.append(f"Letter received on {fmt(inp.received_date)} (date you entered)")
        return inp.received_date

    if not inp.letter_date:
        raise ValueError("letter_date is required to compute a notification date")

    n = notification_days(inp.letter_date)
    notified = inp.letter_date + timedelta(days=n)
    rule = "4-day rule since 2025" if n == 4 else "3-day rule (posted before 2025)"
    law = {
        LegalBasis.AO: "§ 122 (2) AO",
        LegalBasis.VWVFG: "§ 41 (2) VwVfG",
        LegalBasis.SGB_X: "§ 37 (2) SGB X",
        LegalBasis.NONE: "notification fiction",
    }[inp.legal_basis]
    steps.append(
        f"Letter dated {fmt(inp.letter_date)} + {n} days ({law}, {rule}) "
        f"= deemed received {fmt(notified)}"
    )
    warnings.append(
        "We assume the letter was posted on the date printed on it. If it reached you "
        "later than the deemed date, the deadline can be later, but don't rely on that "
        "without advice."
    )

    if inp.legal_basis == LegalBasis.AO and not is_working_day(notified, inp.bundesland):
        notified = roll_forward(
            notified, inp.bundesland, steps, "deemed receipt moves to next working day (BFH)"
        )
    return notified


def add_period(start: date, length: int, unit: PeriodUnit) -> tuple[date, str]:
    """§ 188 BGB: end of a period that started with an event on `start`."""
    if unit == PeriodUnit.DAYS:
        end = start + timedelta(days=length)
        return end, f"+ {length} day{'s' if length != 1 else ''}"
    if unit == PeriodUnit.WEEKS:
        end = start + timedelta(weeks=length)
        return end, f"+ {length} week{'s' if length != 1 else ''} (same weekday)"
    # relativedelta clamps to the last day of the month (§ 188 Abs. 3 BGB)
    end = start + relativedelta(months=length)
    note = f"+ {length} month{'s' if length != 1 else ''}"
    if end.day != start.day:
        note += " (end month is shorter → last day of that month, § 188 (3) BGB)"
    return end, note


def compute_deadline(inp: DeadlineInput) -> DeadlineResult:
    steps: list[str] = []
    warnings: list[str] = []

    if inp.explicit_due_date and not inp.period_length:
        steps.append(f"Date printed in the letter: {fmt(inp.explicit_due_date)}")
        if not is_working_day(inp.explicit_due_date, inp.bundesland):
            warnings.append(
                f"{fmt(inp.explicit_due_date)} is a {_non_working_reason(inp.explicit_due_date, inp.bundesland)}. "
                "Legally it may move to the next working day, but we show the printed date to be safe."
            )
        return DeadlineResult(
            label=inp.label,
            due_date=inp.explicit_due_date,
            notification_date=None,
            steps=steps,
            warnings=warnings,
            kind="explicit",
        )

    if not inp.period_length or not inp.period_unit:
        raise ValueError("Either explicit_due_date or period_length + period_unit is required")

    notified = notification_date(inp, steps, warnings)
    end, note = add_period(notified, inp.period_length, inp.period_unit)
    steps.append(f"{fmt(notified)} {note} = {fmt(end)}")

    law_193 = {
        LegalBasis.AO: "§ 108 (3) AO",
        LegalBasis.VWVFG: "§ 31 (3) VwVfG",
        LegalBasis.SGB_X: "§ 26 (3) SGB X",
        LegalBasis.NONE: "§ 193 BGB",
    }[inp.legal_basis]
    end = roll_forward(end, inp.bundesland, steps, f"deadline moves ({law_193})")
    steps.append(f"Deadline: {fmt(end)}, end of day (24:00)")

    if inp.explicit_due_date and inp.explicit_due_date < end:
        warnings.append(
            f"The letter also prints {fmt(inp.explicit_due_date)}. That is earlier, so we use it."
        )
        steps.append(f"Earlier printed date wins: {fmt(inp.explicit_due_date)}")
        end = inp.explicit_due_date

    return DeadlineResult(
        label=inp.label,
        due_date=end,
        notification_date=notified,
        steps=steps,
        warnings=warnings,
    )
