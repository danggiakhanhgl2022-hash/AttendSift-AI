"""Local validation is authoritative; model confidence cannot bypass it."""
from datetime import date, time
import math
import re
from .identity_context import unique_short_name_evidence
from .paid_break_policy import (PAID_BREAK_MINUTES, PAID_BREAK_SUBTYPE,
                                is_paid_break_event)

EVENT_TYPES = {'Tăng ca', 'OT', 'Nghỉ', 'Đi trễ', 'Về sớm', 'Nghỉ bù OT', 'Làm bù', 'Nghỉ ngắn', 'Nghỉ sớm'}
NUMBERS = ['minutes_not_compensated', 'minutes_compensated', 'ot_minutes', 'ot_used_minutes',
           'paid_break_minutes']


def validate(event, snapshot, month, year):
    errors = []
    warnings = []
    for field in ('person_id','employee_name','event_date','event_type','identity_evidence'):
        if not isinstance(event.get(field),str):
            errors.append(field+': phải là chuỗi hợp lệ')
    if errors:return errors,warnings
    sources = {m['message_id']: m for m in snapshot}
    ids = event.get('source_message_ids')
    if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in sources for i in ids):
        errors.append('source_message_ids: nguồn không tồn tại trong snapshot')
        ids = []
    name = event.get('employee_name')
    if not isinstance(name, str) or not name.strip():
        errors.append('employee_name: thiếu tên người được chấm công')
    if not isinstance(event.get('person_id'), str) or not event['person_id'].strip():
        errors.append('person_id: thiếu nhận diện theo phiên')
    evidence = event.get('identity_evidence')
    source_text = '\n'.join(str(sources[i].get('body', '')) + '\n' + str(sources[i].get('name', '')) for i in ids)
    if not isinstance(evidence, str) or not evidence.strip() or evidence not in source_text:
        errors.append('identity_evidence: cần trích dẫn bằng chứng nhận diện từ nguồn')
    elif not event.get('employee_match_verified') and isinstance(name, str) and name.casefold().replace(' (ctv)', '') not in source_text.casefold() and not unique_short_name_evidence(name,source_text,snapshot):
        warnings.append('Tên chuẩn hóa chưa xuất hiện đầy đủ trong nguồn; cần đối chiếu nhận diện.')
    try:
        day = date.fromisoformat(event.get('event_date', ''))
        if (day.month, day.year) != (month, year):
            errors.append('event_date: ngoài tháng xuất; chỉ giữ làm ngữ cảnh hoặc loại dòng')
    except (ValueError, TypeError):
        errors.append('event_date: ngày không hợp lệ')
    if not isinstance(event.get('event_type'), str) or event.get('event_type') not in EVENT_TYPES:
        errors.append('event_type: loại sự kiện không hỗ trợ')
    for field in NUMBERS:
        number = event.get(field, 0)
        if isinstance(number, bool) or not isinstance(number, (float, int)) or not math.isfinite(number) or not 0 <= number <= 1440 or int(number) != number:
            errors.append(field + ': số phút phải là số nguyên từ 0 đến 1440')
    if not any(e.split(':')[0] in NUMBERS for e in errors):
        if event.get('ot_used_minutes', 0) > event.get('ot_minutes', 0) and str(event.get('event_type')) in {'Tăng ca', 'OT'}:
            errors.append('ot_used_minutes: vượt OT thực tế')
        if event.get('minutes_compensated', 0) + event.get('minutes_not_compensated', 0) > 1440:
            errors.append('minutes_compensated: tổng thời gian vượt một ngày')
        if str(event.get('event_type')) in {'Tăng ca','OT'} and event.get('ot_minutes', 0) <= 0:
            errors.append('ot_minutes: cần số phút OT thực tế')
    if event.get('event_type') == 'Nghỉ':
        if type(event.get('leave_days')) not in (int,float) or event.get('leave_days') not in (0.5, 1):
            errors.append('leave_days: cần xác định nghỉ nửa ngày hoặc cả ngày')
        if not (event.get('leave_source_verified') and event.get('event_subtype') is None) and event.get('event_subtype') not in {'Phép năm', 'Không lương', 'Nghỉ không lương'}:
            errors.append('event_subtype: cần xác nhận loại nghỉ có căn cứ')
    if event.get('paid_break_minutes') or event.get('event_subtype') == PAID_BREAK_SUBTYPE:
        if not is_paid_break_event(event) or any(event.get(field, 0) for field in (
                'minutes_not_compensated', 'minutes_compensated', 'ot_minutes',
                'ot_used_minutes', 'leave_days')):
            errors.append('paid_break_minutes: nghỉ có lương chỉ được ghi 30 phút, không cộng phút trừ lương/OT.')
        else:
            # The only evidence is an explicit self-reported Chatwork request,
            # verified by its date, sender and literal company phrase.
            from .source_reconciliation import extract_explicit_claims
            paid_verified = False
            for source_id in ids:
                source = sources[source_id]
                claims = extract_explicit_claims(source, [source], month, year, roster_policy=True)
                if any(c.get('paid_break_minutes') == PAID_BREAK_MINUTES and
                       c['event_date'] == event.get('event_date') and
                       c['event_type'] == 'Về sớm' and
                       c['identity_evidence'] == str(event.get('identity_evidence') or '')
                       for c in claims):
                    paid_verified = True
                    break
            if not paid_verified:
                errors.append('paid_break_minutes: thiếu tin báo của chính nhân viên về sớm 30 phút không làm bù.')
    if event.get('classification') == 'unresolved':
        errors.append('classification: cần xác nhận người và nhóm nhân sự.')
    if event.get('ot_used_minutes',0) and str(event.get('event_type')) not in {'Tăng ca','OT'}:
        try:date.fromisoformat(event.get('ot_credit_date',''))
        except (TypeError,ValueError):errors.append('ot_credit_date: cần xác định ngày OT nguồn, không tự trừ tháng hiện tại')
    start, end = event.get('start_time'), event.get('end_time')
    if start or end:
        try:
            a=time.fromisoformat(start) if start else None
            b=time.fromisoformat(end) if end else None
            if a and b:
                delta = (b.hour*60+b.minute) - (a.hour*60+a.minute)
                minutes = (event.get('ot_minutes', 0) if str(event.get('event_type')) in {'Tăng ca','OT'}
                           else event.get('paid_break_minutes', 0) or
                           (event.get('minutes_compensated', 0)+event.get('minutes_not_compensated', 0)))
                if delta <= 0 or delta != minutes:
                    errors.append('start_time: khoảng giờ không khớp số phút; ca qua đêm cần tách ngày')
        except (TypeError, ValueError):
            errors.append('start_time: giờ bắt đầu/kết thúc không hợp lệ')
    confidence = event.get('confidence')
    if isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        errors.append('confidence: phải là số từ 0 đến 1')
    elif confidence < 0.85:
        warnings.append('Độ tin cậy thấp; cần đối chiếu nguồn.')
    if event.get('identity_uncertain'):
        warnings.append('Nhận diện người chưa rõ.')
    if event.get('needs_review'):
        warnings.append(str(event.get('review_reason') or 'AI yêu cầu kiểm tra.'))
    return errors, warnings


def validate_set(events, snapshot, month, year):
    seen = set()
    identities = {}
    for event in events:
        errors, warnings = validate(event, snapshot, month, year)
        key = tuple(str(event.get(k)) for k in ('person_id','event_date','event_type'))
        if key in seen:
            errors.append('event_id: trùng người/ngày/loại; cần gộp có đối chiếu hoặc loại dòng')
        seen.add(key)
        identity = str(event.get('person_id'))
        name = event.get('employee_name')
        # '(CTV)' is a classification annotation, not a different person.
        # Keep tone marks: Cầm and Cẩm remain distinct identities.
        identity_name = (re.sub(r'\s*\(\s*CTV\s*\)', '', name, flags=re.I).strip()
                         if isinstance(name, str) and event.get('classification') == 'contractor'
                         else name)
        if identity in identities and identities[identity] != identity_name:
            errors.append('person_id: nhận diện không nhất quán giữa các lô')
        identities[identity] = identity_name
        event['validation_errors'] = errors
        event['validation_warnings'] = warnings
    for event in events:
        # A model can split one person into two IDs as easily as merge namesakes.
        # Keep the IDs separate and require a human to establish the distinction.
        if any(str(other.get('person_id')) != str(event.get('person_id')) and
               other.get('employee_name') == event.get('employee_name') for other in events):
            event['validation_warnings'].append('Tên trùng giữa các mã nhận diện; cần xác nhận đây là những người khác nhau.')
    for event in events:
        if str(event.get('event_type')) in {'OT','Tăng ca'} and not event['validation_errors']:
            uses=[e for e in events if e.get('person_id')==event.get('person_id') and e.get('ot_credit_date')==event.get('event_date') and str(e.get('event_type')) not in {'OT','Tăng ca'}]
            if any(e['validation_errors'] for e in uses):
                event['validation_errors'].append('ot_used_minutes: khoản nghỉ bù liên quan chưa hợp lệ')
            elif sum(e.get('ot_used_minutes',0) for e in uses)!=event.get('ot_used_minutes',0):
                event['validation_errors'].append('ot_used_minutes: phần OT trừ lương phải khớp khoản nghỉ bù có nguồn cùng ngày')
        if event.get('ot_credit_date','') and str(event['ot_credit_date']).startswith(f'{year}-{month:02d}') and str(event.get('event_type')) not in {'OT','Tăng ca'}:
            matches=[e for e in events if e.get('person_id')==event.get('person_id') and e.get('event_date')==event['ot_credit_date'] and str(e.get('event_type')) in {'OT','Tăng ca'}]
            if len(matches)!=1:event['validation_errors'].append('ot_credit_date: thiếu hoặc trùng khoản OT nguồn trong tháng')
    return events
