"""Conservative, auditable checks against explicit Chatwork attendance statements.

An AI may omit one of several people/days or mistakenly attribute an "Em ..."
message to a different sender. Only clear structured claims are reconstructed;
added/changed entries remain pending human approval, never silently payroll-ready.
"""
from datetime import date, datetime, timedelta, timezone
import hashlib
import re

from .identity_context import exact_name_key, identity_hints, name_key, sender_name, source_quote
from .event_policy import is_annual_leave_text_only, configured_ctv_aliases


DURATION = re.compile(
    r'(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>h|giờ|phút|ph|p)(?P<extra>\d{1,2})?(?!\w)',
    flags=re.IGNORECASE,
)
OT_LINE = re.compile(r'^(?P<people>.+?)\s+(?:OT|tăng\s+ca)\s*:?[ ]*(?P<duration>\d+(?:[.,]\d+)?\s*(?:h|giờ|phút|ph|p)(?:\d{1,2})?)(?=\W|$)', re.IGNORECASE)
CONTEXT_OT_LINE = re.compile(
    r'^(?P<people>.+?)\s+(?P<duration>\d+(?:[.,]\d+)?\s*'
    r'(?:h|giờ|phút|ph|p)(?:\d{1,2})?)(?=\W|$)', re.IGNORECASE,
)
DATE_AT_START = re.compile(r'^\s*(?P<day>\d{1,2})/(?P<month>\d{1,2})(?:/(?P<year>20\d{2}))?\s*')
DATE_HEADER = re.compile(r'\bngày\s+(?P<day>\d{1,2})/(?P<month>\d{1,2})(?:/(?P<year>20\d{2}))?\b', re.IGNORECASE)
LEAVE_RANGE = re.compile(r'\bnghỉ\b[\s\S]{0,90}?\bngày\s+(?:thứ\s+[\d,\s]+\s+ngày\s+)?(?P<start>\d{1,2})\s*[-–]\s*(?P<end>\d{1,2})/(?P<month>\d{1,2})(?:/(?P<year>20\d{2}))?', re.IGNORECASE)
LEAVE_DATE_TOKEN = re.compile(
    r'(?<![\w/])(?:(?P<start>\d{1,2})\s*[-–]\s*)?'
    r'(?P<end>\d{1,2})/(?P<month>\d{1,2})(?:/(?P<year>20\d{2}))?(?![\w/])'
)
FIRST_PERSON = re.compile(r'\b(?:em|mình|tôi)\s+xin\s+phép\s+(?:được\s+)?(?P<kind>về\s+sớm|đi\s+trễ|nghỉ)\b', re.IGNORECASE)
# All explicitly marked CTV people are text-only, including mixed staff reports.
MY_CTV = re.compile(r'^.+?\s*\(\s*ctv\s*\)$', re.IGNORECASE)
MY_CTV_OT = re.compile(r'(?P<name>[\wÀ-ỹ]+(?:[ \t]+[\wÀ-ỹ]+){0,4}\s*\(\s*ctv\s*\))\s*(?:OT|tăng\s+ca)\b', re.IGNORECASE)


def _is_my_ctv_claim(claim):
    if any(str(claim.get(k) or '').strip().casefold() in configured_ctv_aliases()
           for k in ('identity_evidence', 'employee_name')):
        return True
    return bool(MY_CTV.fullmatch(str(claim.get('identity_evidence') or '').strip())
                or MY_CTV.fullmatch(str(claim.get('employee_name') or '').strip()))


def _same_my_ctv_record(row, claim):
    if not _is_my_ctv_claim(claim):
        return False
    raw_name = str(row.get('employee_name') or '').strip()
    # Exclude My (CTV) irrespective of the wrong date/type AI may have given it.
    # If the model dropped '(CTV)', only match the bare alias on an OT row.
    claim_name = str(claim.get('identity_evidence') or claim.get('employee_name') or '')
    bare_claim = re.sub(r'\s*\(\s*ctv\s*\)', '', claim_name, flags=re.I)
    bare_row = re.sub(r'\s*\(\s*ctv\s*\)', '', raw_name, flags=re.I)
    return exact_name_key(bare_row) == exact_name_key(bare_claim)


def _date_for(day, month, year):
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except (ValueError, TypeError):
        return None


def _minutes(text):
    match = DURATION.search(text)
    if not match:
        return None
    number = float(match['number'].replace(',', '.'))
    if match['unit'].casefold() in {'h', 'giờ'}:
        result = number * 60
        if match['extra']:
            result += int(match['extra'])
    else:
        result = number
    return int(result) if 0 < result <= 1440 and result.is_integer() else None


def _vn_message_date(message):
    try:
        moment = datetime.fromisoformat(str(message['send_time']).replace('Z', '+00:00'))
        if moment.tzinfo:
            moment = moment.astimezone(timezone(timedelta(hours=7)))
        return moment.date()
    except (ValueError, TypeError, KeyError):
        return None



def _mentioned_date(body, sent):
    """Resolve an explicit Vietnamese day, or use send day only if no other day hint."""
    dated = DATE_HEADER.search(body) or DATE_AT_START.search(body)
    if dated:
        return _date_for(dated['day'], dated['month'], dated['year'] or sent.year)
    if re.search(r'\bngày\s+mai\b', body, re.IGNORECASE):
        return (sent + timedelta(days=1)).isoformat()
    if re.search(r'\bngày\s+kia\b', body, re.IGNORECASE):
        return (sent + timedelta(days=2)).isoformat()
    if re.search(r'\bhôm\s+qua\b', body, re.IGNORECASE):
        return (sent - timedelta(days=1)).isoformat()
    if re.search(r'\b(?:ngày\s+\d{1,2}(?![\d/])|thứ\s+[2-7])\b', body, re.IGNORECASE):
        return None  # Incomplete date; leave uncertain for a human.
    return sent.isoformat()


def _single_person_request(body):
    first = FIRST_PERSON.search(body)
    if not first or re.search(r'\b(?:OT|tăng\s+ca)\b', body, re.IGNORECASE):
        return None
    # One claimed attendance action by the first-person speaker, not a report
    # containing additional named people with their own attendance events.
    claims = re.findall(r'\b(?:về\s+sớm|đi\s+trễ|\bnghỉ\b)\s*', body, re.IGNORECASE)
    if len(claims) != 1:
        return None
    return first

def _mark_review(event, reason):
    event['needs_review'] = True
    previous = str(event.get('review_reason') or '').strip()
    if reason not in previous:
        event['review_reason'] = (previous + '\n' + reason).strip()


def _sender_identity(message):
    name = sender_name(message.get('name'))
    return name, name  # Name appears verbatim in Chatwork sender label.


def _resolve_alias(alias, snapshot):
    """Expand only a uniquely matching sender suffix, never guess a surname."""
    key = exact_name_key(alias)
    if not key:
        return alias, True
    matches = {hint['employee_name'] for hint in identity_hints(snapshot)
               if exact_name_key(hint['employee_name']) == key or
               exact_name_key(hint['employee_name']).endswith(' ' + key)}
    if len(matches) == 1:
        return next(iter(matches)), False
    # A report literally names this employee, even when several unrelated
    # sender accounts share the same short suffix. That is NOT a dispute over
    # who/when/how many minutes were reported. Keep the literal group alias
    # and team-scoped provisional ID, never guess a sender/account identity.
    # Official identity matching remains a separate HR task, not an OT block.
    return alias, False



def _identity_scope(message):
    """Stable team/room scope for a literal short name, not a claimed HR ID.

    Group names are aliases, not definitive personal IDs. Distinct aliases in
    different teams stay distinct unless source sender evidence links them.
    """
    match = re.search(r'\bTeam\s+([^\n:：]+)', str(message.get('body') or ''), re.IGNORECASE)
    if match:
        return 'team:' + exact_name_key(match.group(1).strip())
    return 'reporter:' + str(message.get('account_id') or message.get('name') or message['message_id'])


def _source_alias_id(claim):
    token = '|'.join((str(claim.get('identity_scope') or claim['source_id']),
                      exact_name_key(claim['employee_name'])))
    return 'SRC-N-' + hashlib.sha256(token.encode('utf-8')).hexdigest()[:16]

def _candidate(message, day, name, quote, kind, minutes=0, subtype=None, uncertain=False, leave_days=None):
    return dict(source_id=message['message_id'], event_date=day, employee_name=name,
                identity_evidence=quote, event_type=kind, ot_minutes=minutes,
                event_subtype=subtype, identity_uncertain=uncertain, leave_days=leave_days,
                identity_scope=_identity_scope(message))


def _leave_days_in_request(body, first, send_day, month, year):
    """Enumerate dates only in the leave request, not in a later unrelated note.

    E.g. "nghỉ ngày 7-9/10 ... và ngày 12/10" -> 7, 8, 9, 12.
    A span is intentionally capped to one sentence/line to avoid interpreting
    context about other employees as additional leave by the sender.
    """
    request_line = body[first.end():].splitlines()[0]
    days = []
    for match in LEAVE_DATE_TOKEN.finditer(request_line):
        end = int(match['end'])
        start = int(match['start'] or end)
        m = int(match['month'])
        y = int(match['year'] or send_day.year)
        if not (1 <= start <= end <= start + 30):
            continue
        for number in range(start, end + 1):
            value = _date_for(number, m, y)
            if value and (m, y) == (month, year) and value not in days:
                days.append(value)
    return days


def _split_inline_ot_clauses(text):
    """Split "Thư OT 1h, anh Tâm + Đăng OT 2h" into two exact OT clauses.

    Commas inside a *name list* are not boundaries unless a complete OT
    duration occurs before the separator and another explicit OT follows it.
    This avoids inventing durations for names sharing a single OT statement.
    """
    remainder = text.strip()
    clauses = []
    while remainder:
        first = OT_LINE.match(remainder)
        if first is None:
            return [text]  # Unknown syntax: leave it to manual review.
        tail = remainder[first.end():]
        next_clause = re.match(r'^\s*[,;]\s*(.+)$', tail, re.DOTALL)
        if next_clause and OT_LINE.match(next_clause.group(1)):
            clauses.append(remainder[:first.end()].strip())
            remainder = next_clause.group(1).strip()
            continue
        if clauses:
            # Final note or client context is not itself a new OT entry.
            clauses.append(remainder)
            return clauses
        return [text]
    return clauses or [text]


def _report_ot_line(line):
    """Remove an optional inline date header without removing employee names."""
    line = line.strip()
    dated = DATE_AT_START.match(line)
    if dated:
        return line[dated.end():].lstrip(' :;-'), dated
    header = re.match(
        r'^\s*ngày\s+(\d{1,2}/\d{1,2}(?:/20\d{2})?)\s*[:：-]?\s*',
        line, re.IGNORECASE,
    )
    if header:
        return line[header.end():].strip(), None
    return line, None


def _fully_explicit_overtime_report(message, claims):
    """True when *every* measurable OT statement has a parsed counterpart.

    Used only for excluding clearly unsupported AI rows in a single-message
    report. If a statement has nonstandard structure, keep the AI row for manual
    review instead of assuming the deterministic parser understood everything.
    """
    if not any(c['event_type'] == 'Tăng ca' for c in claims):
        return False
    statements = [line for line in _active_body(message).splitlines()
                  if re.search(r'\b(?:OT|tăng\s+ca)\s*:?[ ]*\d', line, re.IGNORECASE)]
    # An incomplete statement may describe a further person; treating a
    # partially parsed report as complete could suppress that person's row.
    if any(re.search(r'\bOT\b', line, re.IGNORECASE) and
           not re.search(r'\bOT\s*:?[ ]*\d', line, re.IGNORECASE)
           for line in _active_body(message).splitlines()):
        return False
    if not statements:
        return False
    # Confirm every explicitly measured clause has a literal corresponding
    # person, date and duration. A parseable OT line with unparseable names
    # must NOT make the entire report "fully parsed" and cause silent deletion.
    header_day = None
    sent = _vn_message_date(message)
    if not sent:
        return False
    for line in _active_body(message).splitlines():
        line = line.strip()
        if not line:
            continue
        header = DATE_HEADER.search(line)
        if header and not re.search(r'\b(?:OT|tăng\s+ca)\s*\d', line, re.IGNORECASE):
            header_day = _date_for(header['day'], header['month'], header['year'] or sent.year)
        if not re.search(r'\b(?:OT|tăng\s+ca)\s*:?[ ]*\d', line, re.IGNORECASE):
            continue
        stripped, dated = _report_ot_line(line)
        day = (_date_for(dated['day'], dated['month'], dated['year'] or sent.year) if dated else
               (_date_for(header['day'], header['month'], header['year'] or sent.year) if header else header_day))
        if not day:
            return False
        clauses = _split_inline_ot_clauses(stripped)
        if len(clauses) != len(re.findall(r'\b(?:OT|tăng\s+ca)\s*:?[ ]*\d', line, re.IGNORECASE)):
            return False
        for clause in clauses:
            record = OT_LINE.match(clause)
            if not record or not _minutes(record['duration']):
                return False
            names = re.split(r'\s*,\s*|\s+và\s+|\s*\+\s*', record['people'])
            for name in names:
                alias = re.sub(r'^(?:anh|chị|bạn)\s+', '', name, flags=re.IGNORECASE).strip()
                if not any(c['event_type'] == 'Tăng ca' and c['event_date'] == day and
                           c['ot_minutes'] == _minutes(record['duration']) and
                           exact_name_key(str(c['identity_evidence'])) == exact_name_key(alias)
                           for c in claims):
                    return False
    return True



def _active_body(message):
    # Chatwork [qt] blocks quote somebody else's old message and cannot create
    # another payroll event. Preserve the original message in the snapshot.
    body = str(message.get('body') or '')
    return re.sub(r'\[qt\][\s\S]*?\[/qt\]', ' ', body, flags=re.IGNORECASE)

def extract_explicit_claims(message, snapshot, month, year):
    """Only extract patterns where the day, person and duration are explicit."""
    body = _active_body(message)
    send_day = _vn_message_date(message)
    if not send_day:
        return []
    claims = []

    # "Em xin phép nghỉ ... ngày 7-9/10 ... và ngày 12/10" requires FOUR rows.
    first = _single_person_request(body)
    if first and first['kind'].casefold() == 'nghỉ' and not is_annual_leave_text_only(body):
        leave_days = _leave_days_in_request(body, first, send_day, month, year)
        if leave_days and ('phép năm' in body.casefold() or 'không lương' in body.casefold()):
            subtype = 'Phép năm' if 'phép năm' in body.casefold() else 'Không lương'
            name, quote = _sender_identity(message)
            # Half-day leave is explicit in the user's screenshots. Never
            # overwrite a stated 0.5 day with a default 1 day.
            request_line = body[first.end():].splitlines()[0]
            is_half_day = len(leave_days) == 1 and bool(re.search(
                r'\b(?:sáng|chiều|nửa\s+ngày|1\s*/\s*2\s*ngày)\b',
                request_line, re.IGNORECASE))
            for value in leave_days:
                claims.append(_candidate(message, value, name, quote, 'Nghỉ',
                                         subtype=subtype, leave_days=0.5 if is_half_day else 1))

    # One-person explicit "về sớm 30 phút không làm bù" on the send date.
    if first and first['kind'].casefold() in {'về sớm', 'đi trễ'}:
        inferred_date = _mentioned_date(body, send_day)
        duration_match = re.search(r'\b(?:về\s+sớm|đi\s+trễ)\s+(\d+(?:[.,]\d+)?\s*(?:phút|h|giờ))', body, re.IGNORECASE)
        minutes = _minutes(duration_match.group(1)) if duration_match else None
        if minutes and inferred_date and (int(inferred_date[5:7]), int(inferred_date[:4])) == (month, year):
            # An explicit compensation decision is necessary to populate its category.
            if re.search(r'không\s+(?:làm\s+)?bù', body, re.IGNORECASE):
                name, quote = _sender_identity(message)
                claim = _candidate(message, inferred_date, name, quote,
                                   'Về sớm' if first['kind'].casefold() == 'về sớm' else 'Đi trễ')
                claim['minutes_not_compensated'] = minutes
                claims.append(claim)

    # Report-style overtime: explicit date on line or a "Team ... ngày DD/MM" header.
    header_day = None
    # An OT report sometimes omits "OT" on later lines: "Bảo 30ph đối ứng..."
    # Interpret such lines only after at least one explicit OT on the same date.
    explicit_ot_days = set()
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        header = DATE_HEADER.search(line)
        if header and not re.search(r'\b(?:OT|tăng\s+ca)\s*\d', line, re.IGNORECASE):
            header_day = _date_for(header['day'], header['month'], header['year'] or send_day.year)
        people_line, dated = _report_ot_line(line)
        value = (_date_for(dated['day'], dated['month'], dated['year'] or send_day.year)
                 if dated else (_date_for(header['day'], header['month'], header['year'] or send_day.year) if header else header_day))
        if not value or (int(value[5:7]), int(value[:4])) != (month, year):
            continue
        for clause in _split_inline_ot_clauses(people_line):
            record = OT_LINE.match(clause)
            if not record and value in explicit_ot_days and not re.search(
                r'\b(?:nghỉ|đi\s+trễ|về\s+sớm|làm\s+bù|tổng|dự\s+kiến)\b',
                clause, re.IGNORECASE,
            ):
                record = CONTEXT_OT_LINE.match(clause)
            if not record:
                continue
            minutes = _minutes(record['duration'])
            if not minutes:
                continue
            names = re.split(r'\s*,\s*|\s+và\s+|\s*\+\s*', record['people'])
            if not 1 <= len(names) <= 10:
                continue
            cleaned = [re.sub(r'^(?:anh|chị|bạn)\s+', '', n, flags=re.IGNORECASE).strip() for n in names]
            if any(not re.fullmatch(r'[\wÀ-ỹ]+(?:\s+[\wÀ-ỹ]+){0,4}(?:\s*\(CTV\))?', n, re.UNICODE)
                   or re.search(r'\b(?:team|ngày|tháng|tổng|mọi|người)\b', n, re.IGNORECASE)
                   for n in cleaned):
                continue
            if OT_LINE.match(clause):
                explicit_ot_days.add(value)
            for alias in cleaned:
                full_name, uncertain = _resolve_alias(alias, snapshot)
                quote = alias if alias in line else source_quote(alias, line)
                if not quote:
                    continue
                claims.append(_candidate(message, value, full_name, quote, 'Tăng ca', minutes, uncertain=uncertain))

    # Repeated identical statements should not create duplicate payroll rows.
    unique = {}
    for claim in claims:
        key = (claim['event_type'], claim['event_date'], exact_name_key(claim['employee_name']))
        if key not in unique:
            unique[key] = claim
        elif claim['ot_minutes'] != unique[key]['ot_minutes']:
            # Conflicting durations require human review, not choosing one.
            unique[key]['conflicting_duration'] = True
    return list(unique.values())


def _same_person(row, claim):
    a = exact_name_key(str(row.get('employee_name') or ''))
    b = exact_name_key(claim['employee_name'])
    q = exact_name_key(claim['identity_evidence'])
    # A one-word quoted alias is not enough to merge different full names.
    return bool(a and b and (
        a == b or
        (not claim['identity_uncertain'] and a == q) or
        (len(a.split()) >= 2 and b.endswith(' ' + a)) or
        (len(b.split()) >= 2 and a.endswith(' ' + b))
    ))


def _supplement(claim):
    name = claim['employee_name']
    # Stable across messages of the same team, unlike source ID per message.
    # Account-backed identities are refined later by align_event_identities.
    uncertain = bool(claim['identity_uncertain'] or claim.get('conflicting_duration'))
    reason = ('Cùng tên và ngày có hai thời lượng OT khác nhau trong tin gốc; cần kiểm tra.'
              if claim.get('conflicting_duration') else
              'Nội dung nguồn không xác định được người được báo cáo.'
              if claim['identity_uncertain'] else None)
    event = {
        'person_id': _source_alias_id(claim),
        'employee_name': name, 'identity_evidence': claim['identity_evidence'],
        'identity_uncertain': bool(claim['identity_uncertain']),
        'event_date': claim['event_date'], 'event_type': claim['event_type'],
        'event_subtype': claim['event_subtype'], 'reason': 'Trích từ thông báo Chatwork',
        'hours_compensation': '', 'minutes_not_compensated': claim.get('minutes_not_compensated', 0),
        'minutes_compensated': 0, 'ot_minutes': claim['ot_minutes'],
        'ot_used_minutes': 0, 'ot_credit_date': None,
        'leave_days': claim.get('leave_days', 1) if claim['event_type'] == 'Nghỉ' else None,
        'start_time': None, 'end_time': None,
        'source_message_ids': [claim['source_id']], 'confidence': 0.96 if not uncertain else 0.85,
        'needs_review': uncertain,
        'review_reason': reason
    }
    return event


def _certify_source_claim(row, claim):
    """Trust directly verifiable OT figures over AI's speculative registry warning.

    This is safe only for a fully parsed source report and a source-identical
    person/day. Truly ambiguous competing sender accounts remain pending.
    """
    row.update(employee_name=claim['employee_name'], identity_evidence=claim['identity_evidence'],
               ot_minutes=claim['ot_minutes'], person_id=_source_alias_id(claim),
               identity_uncertain=bool(claim['identity_uncertain']),
               needs_review=bool(claim['identity_uncertain'] or claim.get('conflicting_duration')),
               review_reason=None, event_type='Tăng ca')
    row['confidence'] = 0.96 if not row['needs_review'] else 0.85
    if row['needs_review']:
        row['review_reason'] = ('Cùng tên và ngày có hai thời lượng OT khác nhau trong tin gốc; cần kiểm tra.'
                                if claim.get('conflicting_duration') else
                                'Nội dung nguồn không xác định được người được báo cáo.')
    # Never carry speculative deductions from the model into these source-backed
    # OT records. The specific person and minutes are stated directly in text.
    row['minutes_not_compensated'] = 0
    row['minutes_compensated'] = 0
    row['ot_used_minutes'] = 0
    row['ot_credit_date'] = None
    row['leave_days'] = None
    row['start_time'] = None
    row['end_time'] = None


def reconcile_explicit_records(events, snapshot, month, year):
    """Modify derived AI output; untouched original output must be saved separately."""
    sources = {m['message_id']: m for m in snapshot}

    # Sender is authoritative for an exclusively first-person attendance request.
    for row in events:
        ids = row.get('source_message_ids')
        if not isinstance(ids, list) or len(ids) != 1 or ids[0] not in sources:
            continue
        message = sources[ids[0]]
        body = _active_body(message)
        first = _single_person_request(body)
        if not first or str(row.get('event_type')) not in {'Về sớm', 'Đi trễ', 'Nghỉ'}:
            continue
        kind = {'về sớm': 'Về sớm', 'đi trễ': 'Đi trễ', 'nghỉ': 'Nghỉ'}[first['kind'].casefold()]
        if row['event_type'] != kind:
            _mark_review(row, 'Loại sự kiện AI gán không khớp lời xin phép của người gửi; cần sửa hoặc loại dòng.')
            continue
        name, quote = _sender_identity(message)
        if not name:
            continue
        if name_key(str(row.get('employee_name') or '')) != name_key(name):
            row['employee_name'] = name
            row['identity_evidence'] = quote
            _mark_review(row, 'AI gán nhầm người trong yêu cầu ngôi thứ nhất; đã đổi về người gửi Chatwork.')
        if kind in {'Về sớm', 'Đi trễ'}:
            sent = _vn_message_date(message)
            actual = _mentioned_date(body, sent) if sent else None
            if actual and row.get('event_date') != actual:
                row['event_date'] = actual
                _mark_review(row, 'AI gán ngày không khớp thông báo; đã đối chiếu ngày nêu rõ hoặc ngày gửi, cần xác nhận.')

    # Compare each explicit person/date claim; never silently fabricate completed payroll.
    for message in snapshot:
        if is_annual_leave_text_only(_active_body(message)):
            # Never count annual leave; keep the entire message in snapshot.
            # Even a hallucinated AI row (OT/late/leave) cannot create payroll
            # from an annual-leave-only request.
            for row in events:
                if row.get('source_message_ids') == [message['message_id']]:
                    row.update(is_excluded=True, source_only=True,
                               review_state='excluded', needs_review=False,
                               review_reason='Phép năm: chỉ xuất nội dung tin nhắn gốc; không tính công.')
            continue
        claims = extract_explicit_claims(message, snapshot, month, year)
        # The My (CTV) line remains in the original Chatwork message on sheet 1,
        # but does not become an attendance/OT record or require manual registry
        # matching. Keep any AI attempt in the audit trail as an excluded row.
        my_ctv_claims = [c for c in claims if _is_my_ctv_claim(c)]
        if MY_CTV_OT.search(_active_body(message)) and not my_ctv_claims:
            # No date header or unparseable message? Still do not turn the
            # explicitly marked My (CTV) into an employee/payroll row.
            my_ctv_claims = [{'identity_evidence':m['name'], 'employee_name':m['name']}
                             for m in MY_CTV_OT.finditer(_active_body(message))]
        for row in events:
            if row.get('is_excluded') or row.get('source_message_ids') != [message['message_id']]:
                continue
            if any(_same_my_ctv_record(row, claim) for claim in my_ctv_claims):
                row.update(is_excluded=True, source_only=True, review_state='excluded',
                           needs_review=False,
                           review_reason='CTV: chỉ xuất nguyên văn tin Chatwork, không tính công/OT.')
        fully_parsed = _fully_explicit_overtime_report(message, claims)
        if fully_parsed:
            # A model sometimes invents a name that is absent from a group
            # report (e.g. Nghĩa instead of Cẩm), or repeats an existing row.
            # Keep its original output for audit, but exclude the unsupported
            # derived row and add the literal source claims for review.
            assigned = set()
            for row in events:
                if (row.get('is_excluded') or str(row.get('event_type')) not in {'Tăng ca', 'OT'} or
                    row.get('source_message_ids') != [message['message_id']]):
                    continue
                choices = [(i, c) for i, c in enumerate(claims)
                           if c['event_type'] == 'Tăng ca' and
                           c['event_date'] == row.get('event_date') and _same_person(row, c)]
                unused = [i for i, c in choices if i not in assigned]
                if unused:
                    assigned.add(unused[0])
                    continue
                # A fully parsed dated report is authoritative: an AI event
                # for an unsupported date is not a second attendance event.
                row.update(is_excluded=True, source_only=True,
                           review_state='excluded', needs_review=False,
                           review_reason='Dòng AI trùng hoặc sai người/ngày so với báo cáo OT được trích đầy đủ; giữ kết quả AI để truy vết.')
        for row in events:
            if (row.get('is_excluded') or str(row.get('event_type')) not in {'Tăng ca', 'OT', 'Nghỉ'} or
                not isinstance(row.get('source_message_ids'), list) or
                message['message_id'] not in row['source_message_ids']):
                continue
            related = [c for c in claims if _same_person(row, c) and
                       (c['event_type'] == row.get('event_type') or
                        (c['event_type'] == 'Tăng ca' and row.get('event_type') == 'OT'))]
            if related and row.get('event_date') not in {c['event_date'] for c in related}:
                _mark_review(row, 'Ngày AI ghi không nằm trong các ngày có bằng chứng rõ trong tin nguồn; cần sửa hoặc loại dòng.')
        for claim in claims:
            if _is_my_ctv_claim(claim):
                # The snapshot already contains the complete unchanged message.
                # Do not synthesize a payroll row for this source-only alias.
                continue
            matches = [row for row in events
                       if not row.get('is_excluded')
                       and row.get('event_date') == claim['event_date']
                       and str(row.get('event_type')) in ({'OT', 'Tăng ca'} if claim['event_type'] == 'Tăng ca' else {claim['event_type']})
                       and isinstance(row.get('source_message_ids'), list)
                       and claim['source_id'] in row['source_message_ids']
                       and _same_person(row, claim)]
            if matches:
                if len(matches) == 1:
                    row = matches[0]
                    if claim['event_type'] == 'Tăng ca' and fully_parsed:
                        _certify_source_claim(row, claim)
                    elif claim['event_type'] == 'Tăng ca' and row.get('ot_minutes') != claim['ot_minutes']:
                        row['ot_minutes'] = claim['ot_minutes']
                        _mark_review(row, 'AI trích sai phút tăng ca; đã đối chiếu lại số giờ ghi rõ trong nguồn.')
                    if claim['event_type'] == 'Nghỉ' and (
                        row.get('leave_days') != claim['leave_days'] or
                        row.get('event_subtype') != claim['event_subtype']
                    ):
                        row['leave_days'] = claim['leave_days']
                        row['event_subtype'] = claim['event_subtype']
                        _mark_review(row, 'AI trích sai số ngày hoặc loại phép; đã đối chiếu nguồn.')
                    if 'minutes_not_compensated' in claim and row.get('minutes_not_compensated') != claim['minutes_not_compensated']:
                        row['minutes_not_compensated'] = claim['minutes_not_compensated']
                        row['minutes_compensated'] = 0
                        _mark_review(row, 'AI trích sai phút không bù; đã sửa theo thông báo.')
                continue
            events.append(_supplement(claim))
    return events
