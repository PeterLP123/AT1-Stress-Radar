"""Calendar-date helpers shared across schedule generation and pricing."""

from __future__ import annotations

import calendar
from datetime import date


def months_between(start: date, end: date) -> int:
    """Return the number of calendar months from ``start`` to ``end``.

    Only the year and month components are used; day-of-month is ignored.
    The result may be negative if ``end`` is before ``start``.
    """
    return (end.year - start.year) * 12 + (end.month - start.month)


def add_months(anchor: date, months: int) -> date:
    """Return ``anchor`` shifted by ``months`` calendar months.

    The day of month is clamped to the last valid day of the target month
    (e.g. 31 Jan + 1 month -> 28/29 Feb).
    """
    total = anchor.year * 12 + (anchor.month - 1) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
