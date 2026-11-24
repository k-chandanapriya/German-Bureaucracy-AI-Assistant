"""Daily caps on letter reading, so a public server can't run up the AI bill."""

from __future__ import annotations

import threading
from collections import Counter
from datetime import date

from app.config import settings

_lock = threading.Lock()
_day = date.today()
_total = 0
_per_ip: Counter[str] = Counter()


class LimitReached(Exception):
    pass


def take(ip: str) -> None:
    """Count one read for this IP, or raise LimitReached if today's cap is used up."""
    global _day, _total
    with _lock:
        if date.today() != _day:
            _day, _total = date.today(), 0
            _per_ip.clear()
        if settings.max_reads_per_day and _total >= settings.max_reads_per_day:
            raise LimitReached("Today's reading limit for this demo is used up. Please try again tomorrow.")
        if settings.max_reads_per_ip_per_day and _per_ip[ip] >= settings.max_reads_per_ip_per_day:
            raise LimitReached("You've reached today's limit of letters for this demo. Please try again tomorrow.")
        _total += 1
        _per_ip[ip] += 1
