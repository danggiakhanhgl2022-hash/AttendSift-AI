import io
import json
import pytest
from openpyxl import Workbook
from src.models.database import ConfigRepository, MessageRepository
from src.services.import_service import ImportService


def test_message_log_is_atomic_and_preserves_existing_sources(temp_db):
    repo=MessageRepository(temp_db)
    service=ImportService(temp_db,repo,ConfigRepository(temp_db))
    row={'message_id':'m','room_id':'r','sender_name':'Invented A','raw_body':'OT 2h',
         'send_datetime':'2026-09-05 18:00:00'}
    raw=json.dumps([row]).encode()
    assert service.import_file('log.json',raw)['added']==1
    assert service.import_file('log.json',raw)['skipped']==1
    assert service.import_file('log.json',json.dumps([{**row,'raw_body':'Changed'}]).encode())['skipped']==1
    assert repo.get_by_id('m')['body']=='OT 2h'
    with pytest.raises(ValueError):
        service.import_file('log.json',json.dumps([{**row,'message_id':'new'}, {**row,'send_datetime':'bad'}]).encode())
    assert repo.get_by_id('new') is None


def test_original_excel_import_uses_distinct_source_ids(temp_db):
    from datetime import datetime
    config=ConfigRepository(temp_db);config.set('chatwork_room_id','r')
    repo=MessageRepository(temp_db);service=ImportService(temp_db,repo,config)
    w=Workbook();s=w.active;s.title='1_TIN_NHAN_GOC'
    s.append(['Title']);s.append([]);s.append([])
    s.append(['Source ID','Ngày','Giờ','Người','Nội dung'])
    s.append(['MSG001',datetime(2026,9,5),'7:03','Invented A','Text'])
    stream=io.BytesIO();w.save(stream)
    result=service.import_file('reference.xlsx',stream.getvalue())
    assert result['added']==1 and result['imported_from_report']
    message=repo.get_by_room('r')[0]
    assert message['message_id'].startswith('excel:')
    assert message['send_time']=='2026-09-05T07:03:00+07:00'
    assert service.import_file('reference.xlsx',stream.getvalue())['skipped']==1


def test_rejects_workflow_and_employee_only_input(temp_db):
    service=ImportService(temp_db,MessageRepository(temp_db),ConfigRepository(temp_db))
    for data in [{'nodes':[]},{'Employees':[]}]:
        with pytest.raises(ValueError):
            service.import_file('data.json',json.dumps(data).encode())


def test_n8n_locale_unix_and_datetime_spacing(temp_db):
    repo=MessageRepository(temp_db)
    service=ImportService(temp_db,repo,ConfigRepository(temp_db))
    rows=[{'message_id':'n1','room_id':'r','raw_body':'raw','send_time_unix':'1.786.344.485,00'},
          {'message_id':'n2','room_id':'r','raw_body':'raw','send_datetime':'2026-09-05     08:01:02'}]
    assert service.import_file('data.json',json.dumps(rows).encode())['added']==2
    assert repo.get_by_id('n2')['send_time']=='2026-09-05T08:01:02+07:00'
