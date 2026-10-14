"""Regression scenarios extracted from user-provided screenshots (offline fixtures)."""
from copy import deepcopy

from src.services.source_reconciliation import reconcile_explicit_records, extract_explicit_claims
from src.services.identity_context import align_event_identities, repair_identity_evidence
from src.services.validation import validate_set


def msg(mid, sender, body, day, account):
    return {'message_id': mid, 'account_id': account, 'name': sender, 'body': body,
            'send_time': day + 'T12:00:00+07:00'}


def row(mid, name, day, typ, minute=0, **other):
    record = {'person_id': 'MODEL-' + name, 'employee_name': name, 'identity_evidence': name,
              'identity_uncertain': False, 'event_date': day, 'event_type': typ,
              'event_subtype': 'Phép năm' if typ == 'Nghỉ' else None,
              'reason':'', 'hours_compensation':'', 'minutes_not_compensated': 30 if typ == 'Về sớm' else 0,
              'minutes_compensated': 0, 'ot_minutes':minute, 'ot_used_minutes':0,
              'ot_credit_date':None, 'leave_days': 1 if typ == 'Nghỉ' else None,
              'start_time':None, 'end_time':None,'source_message_ids':[mid],
              'confidence': 0.96, 'needs_review':False,'review_reason':None}
    record.update(other)
    return record


def reconcile(events, sources):
    originals = deepcopy(events)
    reconcile_explicit_records(events, sources, 10, 2026)
    for ev in events:
        repair_identity_evidence(ev, sources)
    align_event_identities(events, sources)
    validate_set(events, sources, 10, 2026)
    return originals


def test_annual_leave_from_september_message_is_preserved_only_as_source():
    source = msg('leave', 'クイン (Đặng Như Quỳnh)',
                 'Em xin phép nghỉ ngày thứ 5,6 ngày 1-2/10( phép năm)\nEm đã xin phép chị Dung ạ',
                 '2026-09-30', 1)
    rows = [row('leave','Đặng Như Quỳnh','2026-10-01','Nghỉ')]
    originals = reconcile(rows,[source])
    assert len(originals) == 1 and len(rows) == 1
    assert rows[0]['is_excluded'] and rows[0]['source_only']
    assert extract_explicit_claims(source, [source], 10, 2026) == []


def test_sender_uyens_wrong_name_and_wrong_date_fixed():
    source = msg('uy', 'ウェン (Phạm Gia Uyên)', 'Em xin phép về sớm 30 phút không làm bù (./.)\nEm xin cảm ơn!', '2026-10-14', 44)
    rows = [row('uy','Bùi Ngân Hoa','2026-10-13','Về sớm', identity_evidence='Ngân Hoa')]
    original = reconcile(rows,[source])
    assert original[0]['employee_name'] == 'Bùi Ngân Hoa'
    assert rows[0]['employee_name'] == 'Phạm Gia Uyên'
    assert rows[0]['event_date'] == '2026-10-14'
    assert rows[0]['identity_evidence'] == 'Phạm Gia Uyên'
    assert rows[0]['needs_review'] and not rows[0]['validation_errors']


def test_overtime_message_has_two_dates_and_minutes():
    source = msg('ot', 'クイン (Đặng Như Quỳnh)',
                 'Team BPO đã tăng ca:\n10/10Như Quỳnh tăng ca 3.5h\n11/10 Như Quỳnh tăng ca 3h', '2026-10-11', 1)
    rows = [row('ot','Đặng Như Quỳnh','2026-10-10','Tăng ca',210)]
    reconcile(rows,[source])
    assert len(rows) == 2
    assert {(r['event_date'],r['ot_minutes']) for r in rows} == {('2026-10-10',210),('2026-10-11',180)}
    assert all(not r['validation_errors'] for r in rows)
    assert rows[0]['person_id'] == rows[1]['person_id']


def test_overtime_groups_split_each_person():
    report = msg('grp', 'キム・タン (Lê Minh Tân)',
                 'Team DemoAlpha: ngày 01/10\nTân, Hao, Quỳnh Anh OT 30 phút\nAn (CTV) OT 30 phút\nHỗ trợ dự án DemoAlpha',
                 '2026-10-02', 101)
    sources = [report, msg('h','ハオ (Tran Thi Minh Hao)','', '2026-10-03',102)]
    rows = [row('grp','Tran Thi Minh Hao','2026-10-01','Tăng ca',30)]
    reconcile(rows,sources)
    assert len(rows) == 3
    assert {'Lê Minh Tân', 'Tran Thi Minh Hao', 'Quỳnh Anh'} == {r['employee_name'] for r in rows}
    assert all(r['ot_minutes'] == 30 and not r['validation_errors'] for r in rows)


def test_demobeta_report_six_people_and_no_invented_fullname():
    report = msg('demobeta','Thư (Trần An Thư)',
                 'Team DemoBeta: ngày 8/10\nThư OT 4h: đối ứng khách ClientSix\nanh Tâm OT 30ph: đối ứng khách ClientOne\nĐăng, Bảo, Quân, Việt OT 4h: đối ứng ClientOne',
                 '2026-10-09', 500)
    rows = [row('demobeta','Quân','2026-10-08','Tăng ca',240)]
    reconcile(rows,[report])
    assert len(rows) == 6
    assert {(r['employee_name'],r['ot_minutes']) for r in rows} == {
        ('Trần An Thư', 240),('Tâm', 30),('Đăng',240),('Bảo',240),('Quân',240),('Việt',240)}
    assert all(not r['validation_errors'] for r in rows)


def test_first_person_matching_sender_keeps_current_date():
    source = msg('hao','ハオ (Tran Thi Minh Hao)', 'Em xin phép về sớm 30 phút không làm bù (./.)', '2026-10-14', 202)
    rows = [row('hao','Tran Thi Minh Hao','2026-10-14','Về sớm')]
    reconcile(rows,[source])
    assert len(rows) == 1 and not rows[0]['needs_review']


def test_a_missing_first_person_claim_is_added_for_review():
    source = msg('hao', 'ハオ (Tran Thi Minh Hao)', 'Em xin phép về sớm 30 phút không làm bù (./.)', '2026-10-14', 202)
    rows = []
    reconcile(rows,[source])
    assert len(rows)==1 and rows[0]['minutes_not_compensated']==30
    assert not rows[0]['needs_review'] and not rows[0]['validation_errors']


def test_no_unsupported_work_schedule_as_overtime():
    source = msg('info','Người Giả Lập','Team dự kiến OT 4h tuần sau; ngày 01/10 có lịch họp.', '2026-10-01', 88)
    assert extract_explicit_claims(source,[source],10,2026) == []


def test_same_employee_wrong_overtime_minutes_mark_pending():
    source=msg('ot','Đặng Như Quỳnh','Team BPO đã tăng ca:\n10/10 Như Quỳnh tăng ca 3.5h','2026-10-11',1)
    rows=[row('ot','Đặng Như Quỳnh','2026-10-10','Tăng ca',180)]
    reconcile(rows,[source])
    assert len(rows)==1 and rows[0]['ot_minutes']==210 and not rows[0]['needs_review']


def test_tomorrow_does_not_get_overwritten_by_send_date():
    source = msg('tomorrow','Người Giả Lập','Em xin phép về sớm 30 phút không làm bù ngày mai.', '2026-10-14', 123)
    rows = [row('tomorrow','Người Giả Lập','2026-10-15','Về sớm')]
    reconcile(rows,[source])
    assert len(rows) == 1 and rows[0]['event_date'] == '2026-10-15'


def test_ambiguous_date_not_forced_to_send_day():
    source = msg('unknown','Người Giả Lập','Em xin phép về sớm 30 phút không làm bù ngày 16.', '2026-10-14', 123)
    rows = [row('unknown','Người Giả Lập','2026-10-16','Về sớm')]
    reconcile(rows,[source])
    assert len(rows) == 1 and rows[0]['event_date'] == '2026-10-16'


def test_second_person_claim_blocks_naive_first_person_takeover():
    source = msg('two','Người Báo','Em xin phép về sớm 30 phút không làm bù. Hoa về sớm 30 phút.', '2026-10-14', 555)
    rows = [row('two','Hoa','2026-10-14','Về sớm')]
    reconcile(rows,[source])
    assert rows[0]['employee_name'] == 'Hoa'


def test_wrong_overtime_date_marked_pending_instead_of_silent_double_count():
    source = msg('ot', 'Đặng Như Quỳnh',
                 'Team BPO đã tăng ca:\n10/10 Như Quỳnh tăng ca 3.5h\n11/10 Như Quỳnh tăng ca 3h',
                 '2026-10-11', 1)
    rows = [row('ot', 'Đặng Như Quỳnh', '2026-10-09', 'Tăng ca', 210)]
    reconcile(rows,[source])
    assert len(rows) == 3
    assert rows[0]['is_excluded']
    assert {r['event_date'] for r in rows[1:]} == {'2026-10-10','2026-10-11'}


def test_first_person_wrong_event_type_is_not_trusted():
    source = msg('ev','Người Giả Lập','Em xin phép về sớm 30 phút không làm bù.', '2026-10-14',12)
    rows = [row('ev','Người Giả Lập','2026-10-14','Nghỉ')]
    reconcile(rows,[source])
    assert rows[0]['needs_review']
    assert any(r['event_type']=='Về sớm' and r['minutes_not_compensated']==30 for r in rows)


def test_explicit_date_on_overtime_line_overrides_team_header():
    source = msg('ot','Người Báo','Team A: ngày 01/10\nThư OT 30 phút ngày 02/10', '2026-10-03', 19)
    claims=extract_explicit_claims(source,[source],10,2026)
    assert len(claims)==1 and claims[0]['event_date']=='2026-10-02'


def test_chatwork_quote_cannot_generate_or_reassign_event():
    source = msg('q','Người Báo','[qt][qtmeta aid=88 time=123]Em xin phép về sớm 30 phút không làm bù.[/qt]\nĐã nhận.', '2026-10-14', 19)
    assert extract_explicit_claims(source,[source],10,2026)==[]
    events=[row('q','Người Khác','2026-10-14','Về sớm')]
    reconcile(events,[source])
    assert events[0]['employee_name']=='Người Khác'
