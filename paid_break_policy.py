"""Narrow company policy for a paid 30-minute early departure.

The marker is sourced from an explicit *personal* request. It is not a
medical diagnosis, and it never implies missing or consecutive-day events.
Keep paid time separate from ordinary uncompensated minutes used by payroll.
"""
import re

PAID_BREAK_SUBTYPE = 'Nghỉ 30 phút có lương - không làm bù'
PAID_BREAK_MINUTES = 30

# Only the same request line may justify payment, not a copied quote or
# somebody else's later "không làm bù" explanation.
PAID_BREAK_PHRASE = re.compile(
    r'\bvề\s+sớm\s+30\s*(?:phút|ph)(?!\w)'
    r'[\s,;:()]*?(?:(?:em|mình|tôi)\s+)?không\s+(?:làm\s+)?bù\b',
    re.IGNORECASE,
)


def is_paid_break_request_line(line):
    text = str(line or '')
    return bool(PAID_BREAK_PHRASE.search(text) and not re.search(
        r'\b(?:dự\s+kiến|có\s+thể)\s+(?:về\s+sớm|nghỉ)\b',
        text, re.IGNORECASE))


def is_paid_break_event(event):
    return (event.get('event_type') == 'Về sớm' and
            event.get('event_subtype') == PAID_BREAK_SUBTYPE and
            event.get('paid_break_minutes') == PAID_BREAK_MINUTES)
