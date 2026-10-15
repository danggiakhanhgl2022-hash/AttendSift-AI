"""Rolling three-calendar-month retention in Vietnam time."""
from calendar import monthrange
from datetime import datetime, timedelta, timezone

VIETNAM = timezone(timedelta(hours=7))


def retention_cutoff(now=None):
    current = (now or datetime.now(VIETNAM)).astimezone(VIETNAM)
    month_index = current.year * 12 + current.month - 1 - 3
    year, month = divmod(month_index, 12)
    month += 1
    return current.replace(year=year, month=month,
                           day=min(current.day, monthrange(year, month)[1]))
