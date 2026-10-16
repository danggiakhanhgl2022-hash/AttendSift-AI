"""Roster-based classification and source-backed leave durations."""
import re
import unicodedata
from datetime import date
from .employee_registry import name_key
from .identity_context import sender_name
from .event_policy import is_ctv_text_only

REVIEW_FIELDS = {'classification', 'employee_id'}


def bare_name(value):
    return re.sub(r'\s*\(\s*CTV\s*\)', '', str(value or ''), flags=re.I).strip()


def unaccented_key(value):
    """Conservative no-tone fallback for a name written WITHOUT Vietnamese marks.

    Do not fold an already-accented source token such as Đăng to Dang: tone
    marks often distinguish real coworkers (Bảo/Báo, Cẩm/Cầm).
    """
    name = name_key(bare_name(value)).replace('đ', 'd')
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', name)
                            if not unicodedata.combining(c)).split())


def _has_vietnamese_marks(value):
    raw = name_key(bare_name(value))
    return raw != unaccented_key(raw)


def _suffix_match(label, query):
    return bool(query) and (label == query or label.endswith(' ' + query))


def candidates(name, people):
    """Find employees by exact/full last-name suffix or their registered aliases.

    An unaccented query can represent multiple Vietnamese names (Hien could
    mean Hiền or Hiên). It must compare against ALL folded names, including
    exact-unaccented ones, and remain ambiguous if more than one matches.
    An already-toned query never matches a *different* toned label.
    """
    key = name_key(bare_name(name))
    if not key:
        return []
    if not _has_vietnamese_marks(key):
        folded = unaccented_key(key)
        return [person for person in people if any(
            _suffix_match(unaccented_key(label), folded)
            for label in [person['full_name'], *(person.get('aliases') or [])])]
    # A fully written, accent-marked roster name is stronger than a partial
    # suffix of a DIFFERENT official's longer name. Keep duplicate exact full
    # names ambiguous for employee-code/Chatwork-ID verification.
    if len(key.split()) >= 2:
        full_matches = [person for person in people
                        if name_key(person['full_name']) == key]
        if full_matches:
            return full_matches
    exact = [person for person in people if any(
        _suffix_match(name_key(label), key)
        for label in [person['full_name'], *(person.get('aliases') or [])])]
    if exact:
        return exact
    # Roster may itself omit accents. That does not license matching Đăng
    # to the beginning of the full name Le Thi Nhu Hanh.
    return [person for person in people if any(
        not _has_vietnamese_marks(label) and
        _suffix_match(unaccented_key(label), unaccented_key(key))
        for label in [person['full_name'], *(person.get('aliases') or [])])]


def _ot_name_claimed_in_body(name, linked_messages):
    """A name in background/context text is not evidence of that person's OT."""
    key = name_key(name)
    if not key:
        return False
    name_pattern = r'(?<!\w)' + r'\s+'.join(re.escape(part) for part in key.split()) + r'(?!\w)'
    ot_pattern = re.compile(r'(?:\bot\b|tăng\s+ca|làm\s+thêm)\s*:?[ ]*\d', re.I)
    for message in linked_messages:
        for raw_line in str(message.get('body') or '').splitlines():
            line = unicodedata.normalize('NFC', raw_line).casefold()
            name_match = re.search(name_pattern, line)
            # Source spelling may omit tone marks. Only apply the fallback
            # when the identity quote itself is unaccented; candidate selection
            # must independently establish a unique registered employee.
            if name_match is None and not _has_vietnamese_marks(key):
                folded = unaccented_key(line)
                folded_pattern = r'(?<!\w)' + r'\s+'.join(
                    re.escape(part) for part in unaccented_key(key).split()) + r'(?!\w)'
                name_match = re.search(folded_pattern, folded)
                line = folded
            if line != unicodedata.normalize('NFC', raw_line).casefold():
                ot_match = re.search(r'(?:\bot\b|tang\s+ca|lam\s+them)\s*:?[ ]*\d', line, re.I)
            else:
                ot_match = ot_pattern.search(line)
            if name_match and ot_match and name_match.end() <= ot_match.start():
                between = line[name_match.end():ot_match.start()]
                if not re.search(r'\b(?:hỗ\s+trợ|đối\s+ứng|lý\s+do|nhờ|ho\s+tro|doi\s+ung|ly\s+do|nho)\b', between):
                    return True
    return False


def _verified_ot_claim_for_roster(event, person, linked_messages, people):
    """Verify the exact reported alias, event date and OT duration against text.

    Source extraction is the authority for whether a group-report clause is
    OT, including a contextual line such as "Bao 30ph" following explicit OT.
    The employee registry *only* maps that literal alias to a full name. A
    model-written full name or the group reporter's account is never proof.
    """
    if str(event.get('event_type') or '').casefold() not in {'tăng ca', 'ot'}:
        return False
    day = str(event.get('event_date') or '')
    if not re.fullmatch(r'20\d{2}-\d{2}-\d{2}', day):
        return False
    minutes = event.get('ot_minutes')
    if not isinstance(minutes, (int, float)) or minutes <= 0:
        return False
    evidence = name_key(bare_name(event.get('identity_evidence')))
    literal = name_key(bare_name(event.get('_literal_claim_name')))
    original = name_key(bare_name(event.get('source_employee_name') or event.get('employee_name')))
    from .source_reconciliation import extract_explicit_claims
    for message in linked_messages:
        claims = extract_explicit_claims(message, linked_messages, int(day[5:7]),
                                         int(day[:4]), roster_policy=True)
        for claim in claims:
            if (claim['event_type'] != 'Tăng ca' or claim['event_date'] != day or
                    claim['ot_minutes'] != minutes):
                continue
            short = name_key(bare_name(claim['identity_evidence']))
            # The reported alias must be quoted by the event or be its
            # source-identical name, not a random different OT worker's name.
            if short not in {evidence, literal, original}:
                continue
            owners = candidates(claim['employee_name'], people)
            if len(owners) == 1 and owners[0]['id'] == person['id']:
                return True
    return False


def _sender_self_reported_ot(event, person, linked_messages, people):
    """Verify a full-name sender who describes their own OT using a shorter name.

    A sender label alone must NOT turn a group report into an identity proof.
    Require (1) the unique full-name sender, (2) a matching account ID when
    registered, and (3) an explicit short-name OT clause in that message.
    A shared short alias is ambiguous even if one of the people is the sender.
    """
    if str(event.get('event_type') or '').casefold() not in {'tăng ca', 'ot'}:
        return False
    full = name_key(person['full_name'])
    words = person['full_name'].split()
    phrases = [person['full_name'], *(person.get('aliases') or [])]
    if len(words) >= 2:
        phrases.append(' '.join(words[-2:]))
    phrases = list(dict.fromkeys(name_key(p) for p in phrases if p and len(p.split()) >= 2))

    for message in linked_messages:
        sender = sender_name(message.get('name'))
        if name_key(sender) != full and not (
                (not _has_vietnamese_marks(sender) or
                 not _has_vietnamese_marks(person['full_name'])) and
                unaccented_key(sender) == unaccented_key(person['full_name'])):
            continue
        account = str(person.get('chatwork_account_id') or '')
        if account and account != str(message.get('account_id') or ''):
            continue
        body = unicodedata.normalize('NFC', str(message.get('body') or ''))
        for phrase in phrases:
            # Never infer which employee a shared two-word alias refers to.
            owners = [other for other in people if any(
                phrase == name_key(label) or name_key(label).endswith(' ' + phrase)
                for label in [other['full_name'], *(other.get('aliases') or [])])]
            if len(owners) != 1 or owners[0]['id'] != person['id']:
                continue
            words_pattern = r'\s+'.join(re.escape(w) for w in phrase.split())
            pattern = r'^\s*(?:(?:anh|chị|bạn)\s+)?' + words_pattern + r'\s+(?:ot|tăng\s+ca|làm\s+thêm)\b'
            if re.search(pattern, body.casefold(), re.M | re.I):
                return True
    return False


def _self_report_by_account_id(event, matched_people, linked_messages):
    """Disambiguate namesakes by Chatwork Account ID *only* for own OT report.

    Source authorship is NOT an identity claim in team/group reports. Never
    accept IDs supplied by an AI event as proof of a person's identity.
    """
    if str(event.get('event_type') or '').casefold() not in {'tăng ca', 'ot'}:
        return None
    target = bare_name(event.get('identity_evidence') or event.get('source_employee_name') or
                       event.get('employee_name'))
    if not target:
        return None
    own_claim = re.compile(r'^\s*(?:(?:anh|chị|bạn)\s+)?' +
                           r'\s+'.join(re.escape(part) for part in name_key(target).split()) +
                           r'\s+(?:ot|tăng\s+ca|làm\s+thêm)\b', re.I | re.M)
    for message in linked_messages:
        account = str(message.get('account_id') or '').strip()
        if not account:
            continue
        owners = [person for person in matched_people if
                  str(person.get('chatwork_account_id') or '') == account]
        if len(owners) != 1:
            continue
        selected = owners[0]
        sender = sender_name(message.get('name'))
        if name_key(sender) != name_key(selected['full_name']) and not (
                (not _has_vietnamese_marks(sender) or
                 not _has_vietnamese_marks(selected['full_name'])) and
                unaccented_key(sender) == unaccented_key(selected['full_name'])):
            continue
        body = unicodedata.normalize('NFC', str(message.get('body') or '')).casefold()
        # A reporter may have their own Account ID but report several workers.
        # Such messages are not proof of which namesake is mentioned.
        if re.search(r'\b(?:team|nhóm|báo\s+cáo\s+nhóm)\b', body, re.I):
            continue
        if not own_claim.search(body):
            continue
        # Multiple OT claims in a report are not a self-report.
        count_ot = len(re.findall(r'\b(?:ot|tăng\s+ca|làm\s+thêm)\b', body, re.I))
        if count_ot != 1:
            continue
        # A comma/plus-separated group is also a report, not self-identity proof.
        ot_line = next(line for line in body.splitlines() if
                       re.search(r'\b(?:ot|tăng\s+ca|làm\s+thêm)\b', line, re.I))
        prefix = re.split(r'\b(?:ot|tăng\s+ca|làm\s+thêm)\b', ot_line, maxsplit=1, flags=re.I)[0]
        if ',' in prefix or '+' in prefix or '、' in prefix:
            continue
        return selected
    return None


def classify(event, roster, snapshot, override=None):
    if event.get('is_excluded'):
        return
    people = [p for p in roster['employees'] if p['active']]
    event.setdefault('source_person_id', event.get('person_id'))
    original = event.setdefault('source_employee_name', event.get('employee_name', ''))
    key = name_key(bare_name(original))
    # A unique short name/alias from the employee registry is an official
    # employee candidate.  Never infer a surname from Chatwork sender accounts.
    matches = candidates(original, people)
    # A full name invented by the model is not a verified registry match.
    linked_messages = [m for m in snapshot if m['message_id'] in (event.get('source_message_ids') or [])]
    id_verified = False
    if len(matches) > 1:
        person_by_id = _self_report_by_account_id(event, matches, linked_messages)
        if person_by_id is not None:
            matches = [person_by_id]
            id_verified = True
    evidence_key = name_key(bare_name(event.get('identity_evidence')))
    evidence_matches = candidates(evidence_key, people)
    quoted_ot = _ot_name_claimed_in_body(evidence_key, linked_messages)
    literal_in_source = (_ot_name_claimed_in_body(original, linked_messages)
                         if str(event.get('event_type') or '').casefold() in {'tăng ca', 'ot'}
                         else any(key and re.search(r'(?<!\w)' + re.escape(key) + r'(?!\w)',
                                              name_key(m.get('body'))) for m in linked_messages))
    # Self-request evidence is valid when sender matches one roster identity;
    # generic user labels from other people cannot make a report official.
    first_person_sender = bool(len(matches) == 1 and any(
        re.search(r'\b(?:em|mình|tôi)\s+xin\s+phép\b', m.get('body', ''), re.I)
        and (name_key(sender_name(m.get('name'))) == name_key(matches[0]['full_name']) or
             (not _has_vietnamese_marks(sender_name(m.get('name'))) or
              not _has_vietnamese_marks(matches[0]['full_name'])) and
             unaccented_key(sender_name(m.get('name'))) == unaccented_key(matches[0]['full_name']))
        for m in linked_messages))
    sender_self_report = (len(matches) == 1 and _sender_self_reported_ot(
        event, matches[0], linked_messages, people))
    verified_source_ot = (len(matches) == 1 and _verified_ot_claim_for_roster(
        event, matches[0], linked_messages, people))
    # A model-supplied full name is not proof by itself. For an OT line,
    # explicitly quoted, unique short-name evidence must also appear next to
    # an OT duration in the original source.
    verified_quote = (quoted_ot and len(evidence_matches) == 1 and
                      len(matches) == 1 and evidence_matches[0]['id'] == matches[0]['id'])
    supported = (literal_in_source or first_person_sender or sender_self_report or
                 verified_quote or verified_source_ot or id_verified)
    # A first-person Chatwork profile with a conflicting registered account ID
    # must not be silently accepted, even when the sender spells their name.
    sender_account_conflict = bool(len(matches) == 1 and any(
        (name_key(sender_name(m.get('name'))) == name_key(matches[0]['full_name']) or
         ((not _has_vietnamese_marks(sender_name(m.get('name'))) or
           not _has_vietnamese_marks(matches[0]['full_name'])) and
          unaccented_key(sender_name(m.get('name'))) == unaccented_key(matches[0]['full_name']))) and
        matches[0].get('chatwork_account_id') and
        str(matches[0]['chatwork_account_id']) != str(m.get('account_id') or '')
        for m in linked_messages
    ))
    # Staff membership is decided ONLY by the active employee registry.  Missing
    # source evidence / sender-account conflicts affect whether the EVENT is
    # safe for payroll; they must not reclassify a roster member as a CTV or
    # make their personnel group unresolved.  Unverified events go to sheet 4.
    unsupported_name = bool(len(matches) == 1 and (not supported or sender_account_conflict))
    explicit = is_ctv_text_only({**event, 'employee_name': original}, snapshot)
    linked = None
    # Roster is the SINGLE authority for classification. The reporter's
    # account cannot manufacture official status for a name that is absent
    # from the employee list. Account ID is for resolving registered namesakes.
    if len(matches) == 1:
        linked = matches[0]
        group, reason = 'official', ('Khớp Chatwork Account ID từ báo cáo OT của chính nhân viên.'
                                     if id_verified else 'Khớp danh sách nhân viên chính thức.')
    elif len(matches) > 1:
        group, reason = 'unresolved', 'Tên trùng trong danh sách nhân viên chính thức: cần chọn đúng ID.'
    elif not key:
        group, reason = 'unresolved', 'Không có tên để đối chiếu danh sách nhân viên.'
    else:
        group, reason = 'contractor', 'Tên không có trong danh sách nhân viên chính thức: xếp CTV.'
    if override is not None:
        group = override.get('classification', group)
        if group not in {'official', 'contractor'}:
            raise ValueError('Cần chọn Chính thức hoặc CTV trước khi xác nhận.')
        linked = next((p for p in people if p['id'] == override.get('employee_id')), None)
        if group == 'official' and linked is None:
            raise ValueError('Cần chọn nhân viên chính thức thuộc danh sách của phiên.')
        reason = 'Người phụ trách xác nhận phân loại.'
        event['classification_confirmed'] = True
    reviewed = bool(event.get('classification_confirmed'))
    # Keep personnel membership separate from whether an AI-produced event is
    # trustworthy enough to count toward payroll / OT totals.
    evidence_conflict = bool(group == 'official' and not reviewed and
                             (unsupported_name or explicit))
    event.update(classification=group, classification_reason=reason,
                 employee_id=linked['id'] if linked and group == 'official' else None,
                 employee_match_verified=bool(linked and group == 'official' and
                                              not evidence_conflict))
    if linked and group == 'official':
        event.update(employee_name=linked['full_name'], person_id=linked['id'],
                     identity_uncertain=False)
        # A parser's generic identity uncertainty has been resolved by the
        # uniquely identified registry member and literal source statement.
        # Never clear a distinct warning about conflicting OT durations.
        if evidence_conflict:
            event.update(needs_review=True, review_reason=(
                'Tên khớp nhân viên chính thức nhưng tin nguồn ghi CTV; cần đối chiếu.'
                if explicit else
                'Tên khớp danh sách chính thức nhưng bằng chứng nguồn hoặc Chatwork ID mâu thuẫn; cần đối chiếu.'
            ))
        elif str(event.get('review_reason') or '').strip() in {
            'Nội dung nguồn không xác định được người được báo cáo.',
            'Nhận diện người chưa rõ.',
            'Tên thiếu hoặc có khả năng thuộc nhân viên chính thức; cần chọn đúng người.',
        }:
            event.update(needs_review=False, review_reason=None)
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
