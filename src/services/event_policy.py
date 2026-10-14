"""Exclude unsupported attendance interpretations while retaining original Chatwork evidence.

Only a clear attendance statement may become an attendance row. The AI's event type,
review reason or invented duration are not evidence. Exclusions are reversible/audited:
the original model row is stored separately, and the Chatwork message is never deleted.
"""
import re
import os
import json

def configured_ctv_aliases():
    """Optional explicit contractor labels; never infer CTV status from a bare short name.

    CHAMCONG_CTV_ALIASES must be a JSON list, e.g. ["An"]. Default is [];
    names written as '(CTV)' in the source need no configuration.
    """
    raw = os.getenv('CHAMCONG_CTV_ALIASES', '[]')
    try:
        values = json.loads(raw)
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError()
        return frozenset(name.strip().casefold() for name in values)
    except (ValueError, TypeError):
        raise ValueError('CHAMCONG_CTV_ALIASES phải là mảng JSON tên CTV đã xác nhận.') from None



def reason_from_source(event, snapshot):
    """Replace a generic provenance label with an explicitly stated reason."""
    current = str(event.get('reason') or '').strip()
    if current and current != 'Trích từ thông báo Chatwork':
        return current
    ids = event.get('source_message_ids') or []
    if not isinstance(ids, list):
        return current
    evidence = str(event.get('identity_evidence') or event.get('employee_name') or '').strip()
    for message in snapshot:
        if message['message_id'] not in ids:
            continue
        body = re.sub(r'\[qt\][\s\S]*?\[/qt\]', ' ', str(message.get('body') or ''), flags=re.I)
        explicit = re.search(r'(?:lý|lí)\s*do\s*[:：]\s*([^\n]+)', body, re.I)
        if explicit:
            return explicit[1].strip()
        for line in body.splitlines():
            if evidence and re.search(r'(?<!\w)' + re.escape(evidence) + r'(?!\w)', line, re.I):
                detail = re.search(r'(?:OT|tăng\s+ca)[^:：\n]*[:：]\s*(.+)', line, re.I)
                if detail:
                    return detail[1].strip()
        shared = re.search(r'^\s*(Hỗ trợ[^\n]+)', body, re.I | re.M)
        if shared:
            return shared[1].strip()
    return current


def is_ctv_text_only(event, snapshot):
    """Match CTV to this person, never suppress coworkers in a mixed report."""
    marker = r'\s*\(\s*CTV\s*\)'
    names = [str(event.get(k) or '').strip() for k in ('employee_name', 'identity_evidence')]
    # User-confirmed CTV identity, even when a report omits the suffix.
    if any(re.sub(marker, '', name, flags=re.I).strip().casefold() in configured_ctv_aliases() for name in names):
        return True
    if any(re.search(marker, name, re.I) for name in names):
        return True
    ids = event.get('source_message_ids') or []
    if not isinstance(ids, list):
        return False
    for message in snapshot:
        if message['message_id'] not in ids:
            continue
        body = re.sub(r'\[qt\][\s\S]*?\[/qt\]', ' ', str(message.get('body') or ''), flags=re.I)
        for name in names:
            if name and re.search(r'(?<!\w)' + re.escape(name) + marker, body, re.I):
                return True
    return False


def mark_ctv_source_only(event, snapshot):
    if not is_ctv_text_only(event, snapshot):
        return False
    event.update(is_excluded=True, source_only=True, needs_review=False,
                 identity_uncertain=False, review_state='excluded',
                 review_reason='CTV: chỉ xuất nội dung tin nhắn gốc, không tính công/OT vào bảng lương.',
                 validation_errors=[], validation_warnings=[])
    return True

# These phrases actually assert an employee's time/leave/overtime. Do not treat
# check-in/out instructions, school schedules or being out on company business as
# claims that paid working time has been lost.
ATTENDANCE = re.compile(
    r"(?<!\w)ot(?=\W|\d|$)|tăng\s*ca|làm\s+thêm\s*giờ"
    r"|(?:đi|đến|tới|vào)\s+(?:trễ|muộn)"
    r"|(?:về|ra|nghỉ)\s+sớm"
    r"|\bnghỉ\b|\boff\b|làm\s*bù|bù\s*giờ|bù\s*công",
    re.I,
)
# Mere negations/ordinary break times are not a compensating-work or leave claim.
NON_CLAIMS = [
    re.compile(r"\b(?:không|chưa)\s+(?:có\s+)?(?:làm\s+)?bù(?:\s+(?:giờ|công|lương))?\b", re.I),
    re.compile(r"\b(?:sẽ|dự\s+kiến|hứa)\s+(?:làm\s*bù|bù\s+(?:giờ|công))\b", re.I),
    re.compile(r"\b(?:chưa|không)\s+(?:thực\s+hiện|tiến\s+hành)\s+(?:làm\s*)?bù(?:\s+(?:giờ|công))?\b", re.I),
    re.compile(r"\b(?:không|chưa)\s+(?:có\s+)?nghỉ\b", re.I),
    re.compile(r"\b(?:nghỉ\s+(?:trưa|giải\s+lao|giữa\s+giờ)|giờ\s+nghỉ\s+trưa)\b", re.I),
    re.compile(r"\b(?:lịch\s+nghỉ\s+lễ|ngày\s+nghỉ\s+lễ)\b", re.I),
]


def has_attendance_claim(text):
    """Determine from source words, not an AI-provided explanation, if a claim exists."""
    for expression in NON_CLAIMS:
        text = expression.sub(" ", text)
    return bool(ATTENDANCE.search(text))


def is_information_only(event, snapshot):
    """True only if ALL linked, verifiable source messages lack attendance claims.

    A mismatched/invalid source ID must still go through manual validation.
    Dates/people are intentionally NOT requirements for rejecting an unsupported
    claim: there is no basis for a payroll row if the source never mentions one,
    regardless of what day or person the AI invented.
    """
    ids = event.get("source_message_ids")
    sources = {m["message_id"]: m for m in snapshot}
    if not isinstance(ids, list) or not ids or any(
        not isinstance(i, str) or i not in sources for i in ids
    ):
        return False
    return not any(has_attendance_claim(str(sources[i].get("body", ""))) for i in ids)


def mark_information_only(event, snapshot):
    if not is_information_only(event, snapshot):
        return False
    event.update(
        source_only=True,
        is_excluded=True,
        needs_review=False,
        review_state="excluded",
        review_reason="Tin nguồn không xác nhận sự kiện chấm công; chỉ lưu nội dung tin nhắn.",
        validation_errors=[],
        validation_warnings=[],
        leave_days=None,
    )
    for field in (
        "minutes_not_compensated",
        "minutes_compensated",
        "ot_minutes",
        "ot_used_minutes",
    ):
        event[field] = 0
    return True


# Business policy: annual leave is documented verbatim, not calculated.
# A direct request to take annual leave belongs only to the raw message sheet;
# an unrelated OT report elsewhere must not be swallowed by this policy.
ANNUAL_LEAVE = re.compile(r"\bphép\s*năm\b", re.IGNORECASE)
LEAVE_REQUEST = re.compile(r"\b(?:xin\s+phép\s+)?(?:nghỉ|off)\b", re.IGNORECASE)


def is_annual_leave_text_only(body):
    body = re.sub(r"\[qt\][\s\S]*?\[/qt\]", " ", str(body or ""), flags=re.IGNORECASE)
    return bool(ANNUAL_LEAVE.search(body) and LEAVE_REQUEST.search(body) and
                not re.search(r"(?<!\w)(?:OT|tăng\s+ca)\s*\d", body, re.IGNORECASE))


def mark_annual_leave_source_only(event, snapshot):
    ids = event.get('source_message_ids')
    sources = {m['message_id']: m for m in snapshot}
    if not isinstance(ids, list) or not ids or any(i not in sources for i in ids if isinstance(i,str)):
        return False
    if any(not isinstance(i, str) or i not in sources for i in ids):
        return False
    if not all(is_annual_leave_text_only(sources[i].get('body')) for i in ids):
        return False
    event.update(is_excluded=True, source_only=True, needs_review=False,
                 identity_uncertain=False, review_state='excluded',
                 review_reason='Phép năm: chỉ xuất nguyên văn tin Chatwork, không tính ngày/phút công.',
                 validation_errors=[], validation_warnings=[])
    return True
