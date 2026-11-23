"""Generate .ics calendar files (RFC 5545) that work with every calendar app."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

REMINDER_DAYS = (7, 3, 1)


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold lines longer than 75 octets (RFC 5545 § 3.1)."""
    out, current = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(current) + len(b) > (75 if not out else 74):
            out.append(current.decode("utf-8"))
            current = b""
        current += b
    out.append(current.decode("utf-8"))
    return "\r\n ".join(out)


def build_ics(events: list[dict], calendar_name: str = "Briefly deadlines") -> str:
    """events: [{"title", "date": date, "description"}] → all-day events with reminders."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Briefly//German Bureaucracy AI Assistant//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    for ev in events:
        d: date = ev["date"]
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uuid4()}@briefly.local",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{_escape(ev['title'])}",
            f"DESCRIPTION:{_escape(ev.get('description', ''))}",
            "TRANSP:TRANSPARENT",
        ]
        for days in REMINDER_DAYS:
            lines += [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{_escape(ev['title'])} in {days} day{'s' if days > 1 else ''}",
                f"TRIGGER:-P{days}D",
                "END:VALARM",
            ]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
