"""Public tests using fictional accounts, dates and names only.

A requested 30-minute PAID early departure is counted only on reported
working dates, and never mixed with the unpaid/deduction bucket.
"""
from io import BytesIO
from datetime import date
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from src.services.source_reconciliation import reconcile_explicit_records
from src.services.personnel_policy import classify
from src.services.validation import validate_set
from src.services.paid_break_policy import PAID_BREAK_SUBTYPE
from src.utils.excel_export import export_to_excel


def directory():
    return {'initialized': True, 'employees': [
        dict(id='STAFF1', employee_code='STAFF1', full_name='Trần Thu Bình',
             aliases=[], active=True, chatwork_account_id='101'),
        dict(id='STAFF2', employee_code='STAFF2', full_name='Lê Văn Tâm',
             aliases=[], active=True, chatwork_account_id='202'),
    ]}


def sample(day, *, body='Em xin phép về sớm 30 phút không làm bù. Em cảm ơn!', account='101'):
    return {'message_id':f'DEMO{day}', 'room_id':'demo', 'account_id':account,
            'name':'Bình (Trần Thu Bình)', 'body':body,
            'send_time':f'2026-10-{day:02d}T16:30:00+07:00'}


def analyze(messages, people=None):
    rows=[]
    reconcile_explicit_records(rows, messages, 10, 2026, roster_policy=True)
    for i,row in enumerate(rows):
        row['event_id']=f'EVT{i+1}'
        classify(row, people or directory(), messages)
    validate_set(rows, messages, 10, 2026)
    return rows


def workbook_xml(records, messages):
    out=BytesIO()
    export_to_excel(records, {'month':10,'year':2026,'snapshot':messages,
                              'ai_settings':{'employee_registry':directory()}},out)
    with ZipFile(BytesIO(out.getvalue())) as z:
        return {name:z.read(name).decode('utf-8')
                for name in ('xl/workbook.xml', 'xl/worksheets/sheet2.xml',
                             'xl/worksheets/sheet3.xml', 'xl/worksheets/sheet5.xml')}


def cell_value(xml, address):
    root = ET.fromstring(xml)
    cells = [el for el in root.iter() if el.tag.endswith('}c') and el.get('r') == address]
    assert len(cells) == 1, (address, len(cells))
    return next((el.text for el in cells[0].iter() if el.tag.endswith('}v')), None)


def test_one_or_two_reported_days_are_paid_without_fabricating_missing_day():
    # 12 Oct 2026 = Mon, 13 = Tue, 14 = Wed; user reported Mon and Wed only.
    messages=[sample(12),sample(14)]
    rows=analyze(messages)
    assert len(rows)==2
    assert [r['event_date'] for r in rows]==['2026-10-12','2026-10-14']
    assert all(r['classification']=='official' and not r['validation_errors']
               and not r['validation_warnings'] for r in rows)
    assert all((r['paid_break_minutes'], r['minutes_not_compensated'],
                r['minutes_compensated'], r['ot_minutes'], r['leave_days']) ==
               (30,0,0,0,None) for r in rows)
    assert all(r['event_subtype']==PAID_BREAK_SUBTYPE for r in rows)
    xml=workbook_xml(rows,messages)
    assert all(name in xml['xl/workbook.xml'] for name in
               ['1_TIN_NHAN_GOC','2_CHAM_CONG','3_TONG_KET','4_CAN_KIEM_TRA','5_CTV'])
    assert 'Nghỉ 30 phút có lương' in xml['xl/worksheets/sheet2.xml']
    assert 'Tổng phút nghỉ có lương' in xml['xl/worksheets/sheet3.xml']
    # AB5 / AB6 are the dedicated paid minutes; L5 / L6 are uncompensated=0
    assert cell_value(xml['xl/worksheets/sheet2.xml'], 'AB5') == '30'
    assert cell_value(xml['xl/worksheets/sheet2.xml'], 'AB6') == '30'
    assert cell_value(xml['xl/worksheets/sheet2.xml'], 'L5') == '0'
    assert cell_value(xml['xl/worksheets/sheet2.xml'], 'L6') == '0'
    assert cell_value(xml['xl/worksheets/sheet2.xml'], 'R5') == '0'
    assert cell_value(xml['xl/worksheets/sheet2.xml'], 'R6') == '0'
    assert cell_value(xml['xl/worksheets/sheet3.xml'], 'O5') == '60'


def test_a_friday_and_monday_are_independent_earned_days():
    # Oct 9 2026 Friday; 12 Monday. No Saturday/Sunday generated.
    rows=analyze([sample(9),sample(12)])
    assert {r['event_date'] for r in rows} == {'2026-10-09','2026-10-12'}
    assert sum(r['paid_break_minutes'] for r in rows)==60
    assert all(r['minutes_not_compensated']==0 for r in rows)


def test_non_paid_late_arrival_not_converted_to_paid_break():
    msg=sample(14,body='Em xin phép đi trễ 30 phút không làm bù.')
    rows=analyze([msg])
    assert len(rows)==1
    assert rows[0]['event_type']=='Đi trễ'
    assert rows[0].get('paid_break_minutes',0)==0
    assert rows[0]['minutes_not_compensated']==30


def test_previous_generic_non_compensation_detection_remains_available():
    # Preserve earlier parser behavior: the general compensation statement
    # may appear on the next line; this does NOT earn the new paid category.
    from src.services.source_reconciliation import extract_explicit_claims
    msg=sample(14,body='Em xin phép về sớm 45 phút.\nEm không làm bù.')
    claims=extract_explicit_claims(msg,[msg],10,2026,roster_policy=True)
    assert len(claims)==1
    assert claims[0]['minutes_not_compensated']==45
    assert 'paid_break_minutes' not in claims[0]


def test_wrong_duration_is_not_paid_30_minute_leave():
    msg=sample(14,body='Em xin phép về sớm 45 phút không làm bù.')
    rows=analyze([msg])
    assert len(rows)==1
    assert rows[0]['event_type']=='Về sớm'
    assert rows[0]['minutes_not_compensated']==45
    assert rows[0]['paid_break_minutes']==0


def test_no_source_request_never_creates_paid_entitlement():
    msg=sample(14,body='Em xin phép về sớm 30 phút. Em cảm ơn!')
    rows=analyze([msg])
    assert rows==[]  # The earlier AI event would be reviewed, not certified.


def test_other_persons_non_compensation_does_not_grant_paid_break():
    msg=sample(14,body='Em xin phép về sớm 30 phút, nhưng Lan không làm bù.')
    rows=analyze([msg])
    assert len(rows)==1
    assert rows[0]['paid_break_minutes']==0
    assert rows[0]['event_subtype'] is None


def test_untrusted_ai_paid_flag_requires_actual_matching_source():
    msg=sample(14,body='Em xin phép về sớm 30 phút không làm bù.')
    rows=analyze([msg]);assert len(rows)==1
    rows[0]['event_date']='2026-10-15'
    validate_set(rows,[msg],10,2026)
    assert any('paid_break_minutes:' in error for error in rows[0]['validation_errors'])


def test_chatwork_sender_account_conflict_stays_pending():
    rows=analyze([sample(14,account='404')])
    assert rows[0]['classification']=='official'
    assert rows[0]['needs_review']


def test_ot_group_logic_is_unchanged_and_five_sheet_ctv_still_present():
    msg=sample(15,body='Team demo ngày 15/10\nBình OT 2h\nTâm OT 1h\nLan OT 30p')
    rows=analyze([msg])
    assert len(rows)==3
    assert sorted((r['ot_minutes'],r.get('paid_break_minutes',0)) for r in rows)==[(30,0),(60,0),(120,0)]
    assert sorted(r['classification'] for r in rows)==['contractor','official','official']
    xml=workbook_xml(rows,[msg])
    assert '5_CTV' in xml['xl/workbook.xml']
    assert 'Lan' in xml['xl/worksheets/sheet5.xml']
