"""Cases from screenshots: one Chatwork message may report many people and days."""
from copy import deepcopy

import pytest

from src.services.source_reconciliation import extract_explicit_claims, reconcile_explicit_records
from src.services.identity_context import align_event_identities, repair_identity_evidence
from src.services.validation import validate_set
from tests.test_source_reconciliation import msg, row


def parse(body, sent='2026-10-02', author='Trần An Thư', other_sources=None):
    source = msg('report', author, body, sent, 700)
    snapshot = [source] + (other_sources or [])
    claims = extract_explicit_claims(source, snapshot, 10, 2026)
    return snapshot, claims


@pytest.mark.parametrize('text,expected', [
    ('Team DemoAlpha: ngày 01/10\nTân, Hao, Quỳnh Anh OT 30 phút\nAn (CTV) OT 30 phút\nHỗ trợ dự án DemoAlpha',
     {('Tân','2026-10-01',30),('Hao','2026-10-01',30),('Quỳnh Anh','2026-10-01',30),('An (CTV)','2026-10-01',30)}),
    ('Team DemoBeta: ngày 1/10\nThư OT 1h: đối ứng khách ClientSix\nCẩm OT 1h: đối ứng ClientSix',
     {('Thư','2026-10-01',60),('Cẩm','2026-10-01',60)}),
    ('Team DemoBeta: ngày 2/10\nThư OT 2h30: đối ứng khách ClientEight, ClientOne\nCẩm OT 2h30: đối ứng ClientEight\nBảo 30ph đối ứng curious',
     {('Thư','2026-10-02',150),('Cẩm','2026-10-02',150),('Bảo','2026-10-02',30)}),
    ('Team DemoBeta: ngày 8/10\nThư OT 4h: đối ứng khách ClientSix\nanh Tâm OT 30ph: đối ứng khách ClientOne\nĐăng, Bảo, Quân, Việt OT 4h: đối ứng ClientOne',
     {('Thư','2026-10-08',240),('Tâm','2026-10-08',30),('Đăng','2026-10-08',240),('Bảo','2026-10-08',240),('Quân','2026-10-08',240),('Việt','2026-10-08',240)}),
    ('Team DemoBeta: ngày 9/10\nanh Tâm OT 30ph: đối ứng khách ClientOne\n\nNgày 10/10:\nBảo OT 8h: đối ứng THREE\nViệt OT 4h: đối ứng ClientTwo.\n\nNgày 12/10:\nThư OT 1h: đối ứng khách Memory\nanh Tâm OT 1h: đối ứng khách ClientOne\nViệt OT 1h: đối ứng ClientTwo\nTrắng OT 30ph: đối ứng ClientOne',
     {('Tâm','2026-10-09',30),('Bảo','2026-10-10',480),('Việt','2026-10-10',240),('Thư','2026-10-12',60),('Tâm','2026-10-12',60),('Việt','2026-10-12',60),('Trắng','2026-10-12',30)}),
    ('Team DemoBeta: ngày 9/10\nNgày 10/10: Bảo OT 8h',
     {('Bảo','2026-10-10',480)}),
])
def test_report_split_into_exact_person_day_duration_claims(text, expected):
    _, claims = parse(text, author='Một người báo hộ')
    actual = {(c['employee_name'],c['event_date'],c['ot_minutes']) for c in claims}
    assert actual == expected


def test_bad_model_names_get_excluded_but_actual_group_rows_are_created():
    snapshot, _ = parse('Team DemoBeta: ngày 1/10\nThư OT 1h: đối ứng khách ClientSix\nCẩm OT 1h: đối ứng ClientSix',
                        author='Người báo hộ')
    ai = row('report', 'Nghĩa', '2026-10-01', 'Tăng ca', 60)
    events = [ai]
    raw = deepcopy(ai)
    reconcile_explicit_records(events, snapshot, 10, 2026)
    assert events[0]['is_excluded'] and events[0]['source_only']
    assert raw['employee_name'] == events[0]['employee_name'] == 'Nghĩa'
    active = [r for r in events if not r.get('is_excluded')]
    assert {e['employee_name'] for e in active} == {'Thư','Cẩm'}
    for event in active:
        repair_identity_evidence(event, snapshot)
    align_event_identities(active,snapshot)
    validate_set(active,snapshot,10,2026)
    assert all(not r['validation_errors'] and not r['validation_warnings'] for r in active)


def test_group_name_ctv_is_not_substituted_and_reporter_is_not_credited():
    snapshot, claims = parse('Team DemoAlpha: ngày 01/10\nTân, Hao, Quỳnh Anh OT 30 phút\nAn (CTV) OT 30 phút',
                             author='Lê Minh Tân')
    events = [row('report','Thanh (CTV)','2026-10-01','Tăng ca',30)]
    reconcile_explicit_records(events, snapshot, 10, 2026)
    assert events[0]['is_excluded']
    active = [e for e in events if not e.get('is_excluded')]
    assert {e['employee_name'] for e in active} == {'Lê Minh Tân','Hao','Quỳnh Anh'}
    assert not any(e['employee_name'] in {'Thanh (CTV)', 'An (CTV)'} for e in active)
    assert all(e['source_message_ids']==['report'] for e in active)


def test_annual_leave_dates_are_not_payroll_claims():
    body = ('Em xin phép nghỉ ngày 7-9/10 (thứ tư-thứ sáu) và ngày 12/10 (thứ hai) (phép năm)\n'
            'Lý do: Em có việc cá nhân.\nEm đã xin phép Aso.')
    snapshot, claims = parse(body, sent='2026-09-25', author='Võ Ngọc Quỳnh')
    assert claims == []
    events = [row('report', 'Võ Ngọc Quỳnh', '2026-10-12', 'Nghỉ')]
    reconcile_explicit_records(events, snapshot, 10, 2026)
    assert len(events) == 1
    assert events[0]['is_excluded'] and events[0]['source_only']
    assert snapshot[0]['body'] == body


def test_duplicate_ai_row_for_one_person_day_is_excluded():
    snapshot, _ = parse('Team A: ngày 01/10\nThư OT 1h', author='Người báo hộ')
    events = [row('report','Thư','2026-10-01','Tăng ca',60),
              row('report','Thư','2026-10-01','Tăng ca',60)]
    reconcile_explicit_records(events,snapshot,10,2026)
    active = [e for e in events if not e.get('is_excluded')]
    assert len(active) == 1 and events[1]['is_excluded']


def test_unparsable_second_overtime_clause_does_not_exclude_model_row():
    snapshot, _ = parse('Team A: ngày 01/10\nThư OT 1h\nCẩm OT thời gian sẽ báo sau',
                        author='Người báo hộ')
    events = [row('report','Cẩm','2026-10-01','Tăng ca',60)]
    reconcile_explicit_records(events,snapshot,10,2026)
    assert not events[0].get('is_excluded')


def test_repeated_identical_overtime_sentence_generates_one_claim():
    snapshot, claims = parse('Team A: ngày 01/10\nThư OT 1h\nThư OT 1h',author='Người báo hộ')
    assert len(claims)==1


def test_bao_is_not_the_same_person_as_reporter_named_bao_with_different_tone():
    snapshot, claims = parse('Team DemoBeta: ngày 2/10\nThư OT 1h\nBảo 30ph đối ứng curious',
                             author='Người Báo')
    bao = next(c for c in claims if c['employee_name']=='Bảo')
    assert not bao['identity_uncertain']  # Name is quoted; missing registry is not ambiguity.
    events=[]
    reconcile_explicit_records(events,snapshot,10,2026)
    align_event_identities(events,snapshot)
    reporter_account_id = next(e['person_id'] for e in events if e['employee_name']=='Bảo')
    assert reporter_account_id.startswith('SRC-N-')
    assert all(e['employee_name'] in {'Thư','Bảo'} for e in events)


def test_cam_with_different_tones_stays_separate():
    snapshot, _ = parse('Team DemoBeta: ngày 1/10\nThư OT 1h\nCầm OT 1h',
                        author='Người báo hộ')
    events=[row('report','Cẩm','2026-10-01','Tăng ca',60)]
    reconcile_explicit_records(events,snapshot,10,2026)
    assert events[0]['is_excluded']
    assert {e['employee_name'] for e in events if not e.get('is_excluded')} == {'Thư', 'Cầm'}

def test_my_ctv_source_only_even_when_ai_returns_a_correct_name_or_bad_date():
    body = 'Team DemoAlpha: ngày 01/10\nTân, Hào, Quỳnh Anh OT 30 phút\nAn (CTV) OT 30 phút'
    snapshot, _ = parse(body, author='Lê Minh Tân')
    events = [row('report', 'An (CTV)', '2026-10-04', 'Tăng ca', 30),
              row('report', 'An', '2026-10-01', 'Tăng ca', 30)]
    reconcile_explicit_records(events, snapshot, 10, 2026)
    assert len(events) == 5
    assert all(e.get('is_excluded') and e.get('source_only') for e in events[:2])
    assert {e['employee_name'] for e in events if not e.get('is_excluded')} == {
        'Lê Minh Tân','Hào','Quỳnh Anh'}
    assert all(e['ot_minutes'] == 30 for e in events[2:])


def test_ctv_policy_excludes_all_explicit_contractors():
    snapshot, _ = parse('Team DemoAlpha: ngày 01/10\nAn (CTV) OT 30 phút\nAn (CTV) OT 1h',
                        author='Người báo hộ')
    events = []
    reconcile_explicit_records(events, snapshot, 10, 2026)
    assert not [e for e in events if not e.get('is_excluded')]


def test_message_one_report_many_distinct_durations_keeps_exact_dates():
    text = ('Team DemoBeta: ngày 5/10\n'
            'Thư OT 1h, anh Tâm + Đăng OT 2h\n'
            'Ngày 7/10\n'
            'Thư OT 1h30\nanh Tâm OT 30ph\nViệt OT 1h')
    snapshot, _ = parse(text)
    events = []
    reconcile_explicit_records(events, snapshot, 10, 2026)
    assert {(e['employee_name'],e['event_date'],e['ot_minutes']) for e in events} == {
        ('Trần An Thư','2026-10-05',60), ('Tâm','2026-10-05',120),
        ('Đăng','2026-10-05',120),('Trần An Thư','2026-10-07',90),
        ('Tâm','2026-10-07',30),('Việt','2026-10-07',60)}


def test_annual_and_unpaid_leave_preserve_source_without_calculating_days():
    annual, claims = parse('Em xin phép nghỉ sáng ngày 5/10 (thứ 2) (1/2 ngày phép năm)',
                           sent='2026-10-01', author='Tran Thi Minh Hao')
    assert claims == []
    rows = [row('report', 'Tran Thi Minh Hao', '2026-10-05', 'Nghỉ', leave_days=0.5)]
    reconcile_explicit_records(rows, annual, 10, 2026)
    assert rows[0]['is_excluded']
    unpaid, claims = parse('Em xin phép nghỉ chiều thứ 5 ngày 8/10 (không lương)',
                           sent='2026-10-01', author='Tran Thi Minh Hao')
    assert claims == []
    rows = [row('report', 'Tran Thi Minh Hao', '2026-10-08', 'Nghỉ', leave_days=0.5)]
    reconcile_explicit_records(rows, unpaid, 10, 2026)
    assert rows[0]['is_excluded'] and rows[0]['source_only']
    # Original AI values may remain in the excluded audit record; none count.
    assert rows[0]['review_state']=='excluded'
