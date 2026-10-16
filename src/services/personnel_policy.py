"""Roster-based classification and source-backed leave durations."""
import re
import unicodedata
from datetime import date
from .employee_registry import name_key
from .event_policy import is_ctv_text_only

REVIEW_FIELDS = {'classification', 'employee_id'}


def bare_name(value):
    return re.sub(r'\s*\(\s*CTV\s*\)', '', str(value or ''), flags=re.I).strip()


def candidates(name, people):
    key = name_key(bare_name(name))
    if not key:
        return []
    def ascii_key(s):
        return ''.join(c for c in unicodedata.normalize('NFD', name_key(s)) if not unicodedata.combining(c)).replace('đ', 'd')
    return [p for p in people if any(
        name_key(n).endswith(' ' + key) or
        ascii_key(n) == ascii_key(key) or
        ascii_key(n).endswith(' ' + ascii_key(key))
        for n in [p['full_name'], *p['aliases']])]


def classify(event, roster, snapshot, override=None):
    if event.get('is_excluded'):
        return
    people = [p for p in roster['employees'] if p['active']]
    event.setdefault('source_person_id', event.get('person_id'))
    original = event.setdefault('source_employee_name', event.get('employee_name', ''))
    key = name_key(bare_name(original))
    matches = [p for p in people if key and key in {
        name_key(p['full_name']), *(name_key(a) for a in p['aliases'])}]
    # A full name invented by the model is not a verified registry match.
    linked_messages = [m for m in snapshot if m['message_id'] in (event.get('source_message_ids') or [])]
    evidence_key = name_key(bare_name(event.get('identity_evidence')))
    evidence_matches = [p for p in people if evidence_key and evidence_key in {
        name_key(p['full_name']), *(name_key(a) for a in p['aliases'])}]
    literal_in_source = any(key and re.search(r'(?<!\w)' + re.escape(key) + r'(?!\w)',
                            name_key(m.get('body'))) for m in linked_messages)
    first_person_sender = any(re.search(r'\b(?:em|mình|tôi)\s+xin\s+phép\b', m.get('body', ''), re.I)
                              and key in name_key(m.get('name')) for m in linked_messages) if key else False
    unsupported_name = bool(matches and not (literal_in_source or first_person_sender or
                                             (len(evidence_matches) == 1 and evidence_matches[0] in matches)))
    if unsupported_name:
        matches = []
    explicit = is_ctv_text_only({**event, 'employee_name': original}, snapshot)
    linked = None
    # Sender account can identify a first-person request, not a group report.
    if not matches:
        ids = event.get('source_message_ids') or []
        for message in snapshot:
            if message['message_id'] in ids and re.search(
                    r'\b(?:em|mình|tôi)\s+xin\s+phép\b', message.get('body', ''), re.I):
                if name_key(original) == name_key(message.get('name')) or original in str(message.get('name')):
                    matches = [p for p in people if p['chatwork_account_id'] and
                               p['chatwork_account_id'] == str(message.get('account_id'))]
    if len(matches) == 1 and not explicit:
        linked = matches[0]
        group, reason = 'official', 'Khớp danh sách nhân viên chính thức.'
    elif matches and explicit:
        group, reason = 'unresolved', 'Xung đột: có trong danh sách chính thức nhưng nguồn ghi CTV.'
    elif explicit and key:
        group, reason = 'contractor', 'Nguồn ghi rõ CTV cho người này.'
    elif unsupported_name or not key or len(matches) > 1 or candidates(original, people):
        group, reason = 'unresolved', 'Tên thiếu hoặc có khả năng thuộc nhân viên chính thức; cần chọn đúng người.'
    else:
        group, reason = 'contractor', 'Tự phân loại CTV vì không thuộc danh sách nhân viên chính thức.'
    if override is not None:
        group = override.get('classification', group)
        if group not in {'official', 'contractor'}:
            raise ValueError('Cần chọn Chính thức hoặc CTV trước khi xác nhận.')
        linked = next((p for p in people if p['id'] == override.get('employee_id')), None)
        if group == 'official' and linked is None:
            raise ValueError('Cần chọn nhân viên chính thức thuộc danh sách của phiên.')
        reason = 'Người phụ trách xác nhận phân loại.'
        event['classification_confirmed'] = True
    event.update(classification=group, classification_reason=reason,
                 employee_id=linked['id'] if linked and group == 'official' else None,
                 employee_match_verified=bool(linked and group == 'official'))
    if linked and group == 'official':
        event.update(employee_name=linked['full_name'], person_id=linked['id'],
                     identity_uncertain=False)
    if group == 'contractor':
        event['person_id'] = event.get('source_person_id') or event.get('person_id')
    if group == 'unresolved':
        event.update(needs_review=True, review_reason=reason)
    return group


def leave_claims(body, send_day):
    """Map each explicitly dated leave clause to duration and period."""
    request = re.search(r'\bnghỉ\b([^\n]*)', body, re.I)
    if not request:
        return {}
    line = request[1]
    if re.search(r'\d+(?:[.,]\d+)?\s*(?:giờ|phút|h|ph|p)\b', line, re.I):
        return {}  # Hour-based leave needs a separately agreed conversion.
    pattern = re.compile(r'(?<![\w/])(?:(\d{1,2})\s*[-–]\s*)?(\d{1,2})/(\d{1,2})(?:/(20\d{2}))?(?![\w/])')
    result = {}
    previous_end = 0
    for match in pattern.finditer(line):
        context = line[previous_end:match.start()]
        # Ignore weekday parentheses; the nearest clause determines this date.
        context = re.sub(r'\([^)]*\)', ' ', context)
        morning, afternoon = bool(re.search(r'\bsáng\b', context, re.I)), bool(re.search(r'\bchiều\b', context, re.I))
        period = 'full' if morning == afternoon else 'morning' if morning else 'afternoon'
        if re.search(r'\bnửa\s+ngày\b|1\s*/\s*2\s*ngày', context, re.I):
            period = 'half'
        first, last, month, year = int(match[1] or match[2]), int(match[2]), int(match[3]), int(match[4] or send_day.year)
        if 0 <= last-first <= 30:
            for number in range(first, last+1):
                try:
                    day = date(year, month, number).isoformat()
                except ValueError:
                    continue
                periods = result.setdefault(day, set())
                periods.add(period)
        previous_end = match.end()
    return {day: {'leave_days': 1 if 'full' in parts or {'morning','afternoon'} <= parts else .5,
                  'leave_period': 'full' if 'full' in parts or {'morning','afternoon'} <= parts else next(iter(parts))}
            for day, parts in result.items()}
