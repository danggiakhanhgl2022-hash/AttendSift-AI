"""Regression: first-person no-compensation requests must not remain pending.

All identifiers, names and Chatwork texts here are entirely synthetic.
"""
from datetime import date

from src.services.source_reconciliation import reconcile_explicit_records, extract_explicit_claims, _supplement
from src.services.personnel_policy import classify
from src.services.validation import validate_set


def roster(account='101'):
    return {'initialized': True, 'employees': [
        dict(full_name='Nguyễn Thu Bình', id='STAFF-1', employee_code='STAFF-1',
             active=True, chatwork_account_id=account, aliases=[]),
        dict(full_name='Võ Minh Quân', id='STAFF-2', employee_code='STAFF-2',
             active=True, chatwork_account_id='', aliases=[]),
        dict(full_name='Lê Đức Quân', id='STAFF-3', employee_code='STAFF-3',
             active=True, chatwork_account_id='', aliases=[]),
    ]}


def message(day, body='Em xin phép về sớm 30 phút không làm bù (./.)\nEm xin cảm ơn!'):
    return dict(message_id=f'SRC-DEMO-{day}', name='Bạn (Nguyễn Thu Bình)',
                account_id='101', body=body,
                send_time=f'2026-10-{day:02d}T13:00:00+07:00')


def fake_ai(msg, *, kind='Về sớm', minutes=0):
    claims = extract_explicit_claims(msg, [msg], 10, 2026, roster_policy=True)
    assert len(claims) == 1
    event = _supplement(claims[0])
    event.update(person_id='MODEL-WRONG', employee_name='Người Khác',
                 identity_evidence='Người Khác', event_type=kind,
                 minutes_not_compensated=minutes,
                 needs_review=True, review_reason='AI không chắc người gửi')
    return event


def pipeline(msgs, directory=None):
    events = [fake_ai(m) for m in msgs]
    reconcile_explicit_records(events, msgs, 10, 2026, roster_policy=True)
    for i, event in enumerate(events):
        event['event_id'] = f'EVT{i+1:04d}'
        classify(event, directory or roster(), msgs)
    validate_set(events, msgs, 10, 2026)
    return events


def test_three_days_first_person_cleared_after_source_verification():
    events = pipeline([message(d) for d in (14, 15, 16)])
    assert len(events) == 3
    for e, day in zip(events, (14, 15, 16)):
        assert e['event_date'] == date(2026, 10, day).isoformat()
        assert e['employee_name'] == 'Nguyễn Thu Bình'
        assert e['classification'] == 'official'
        assert e['employee_id'] == 'STAFF-1'
        assert (e['minutes_not_compensated'], e['paid_break_minutes'], e['ot_minutes']) == (0, 30, 0)
        assert e['event_subtype'] == 'Nghỉ 30 phút có lương - không làm bù'
        assert not e['needs_review']
        assert not e['validation_errors'], e['validation_errors']
        assert not e['validation_warnings'], e['validation_warnings']


def test_conflicting_sender_account_still_requires_review():
    rows = pipeline([message(14)], directory=roster(account='999'))
    assert rows[0]['classification'] == 'official'
    assert rows[0]['needs_review']
    assert rows[0]['validation_warnings']


def test_no_explicit_non_compensation_keeps_review():
    msg = message(14, 'Em xin phép về sớm 30 phút. Em xin cảm ơn!')
    fake = fake_ai(message(14))
    fake['source_message_ids'] = [msg['message_id']]
    events = [fake]
    reconcile_explicit_records(events, [msg], 10, 2026, roster_policy=True)
    assert events[0]['needs_review']


def test_group_report_quan_requires_roster_id():
    msg = dict(message(14), message_id='SRC-OT',
               body='Team Demo: ngày 14/10\nQuân OT 4h')
    rows = []
    reconcile_explicit_records(rows, [msg], 10, 2026, roster_policy=True)
    assert len(rows) == 1
    assert classify(rows[0], roster(), [msg]) == 'unresolved'
    assert rows[0]['needs_review']


def test_no_ai_row_still_creates_source_verified_request():
    msg = message(14)
    rows = []
    reconcile_explicit_records(rows, [msg], 10, 2026, roster_policy=True)
    assert len(rows) == 1
    assert classify(rows[0], roster(), [msg]) == 'official'
    assert rows[0]['minutes_not_compensated'] == 0
    assert rows[0]['paid_break_minutes'] == 30
    assert not rows[0]['needs_review']


def test_other_person_compensation_line_cannot_validate_own_request():
    msg = message(14, 'Em xin phép về sớm 30 phút.\nBình khác không làm bù.')
    e = fake_ai(message(14))
    reconcile_explicit_records([e], [msg], 10, 2026, roster_policy=True)
    assert e['needs_review']
