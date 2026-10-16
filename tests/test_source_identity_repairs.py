from src.services.identity_context import repair_identity_evidence,sender_name


def test_ctv_and_short_name_need_no_registered_roster():
    snapshot=[{'message_id':'m','name':'Người báo hộ','body':'Bạn An (CTV) OT 30 phút. Cầm OT 1h.'}]
    for name in ['An (CTV)','Cầm']:
        event={'employee_name':name,'source_message_ids':['m'],'identity_evidence':'fabricated','person_id':'',
               'needs_review':True,'identity_uncertain':True,'review_reason':'Person not registered in registry'}
        repair_identity_evidence(event,snapshot)
        assert event['identity_evidence']==name
        assert event['person_id'].startswith('SRC-')
        assert not event['needs_review'] and not event['identity_uncertain']


def test_no_invented_full_name_and_no_clearing_real_uncertainty():
    snapshot=[{'message_id':'m','name':'Người báo hộ','body':'Tâm OT 30 phút'}]
    event={'employee_name':'Người giả lập Tâm','source_message_ids':['m'],'identity_evidence':'fabricated','needs_review':True,
           'review_reason':'not registered in registry'}
    repair_identity_evidence(event,snapshot)
    assert event['employee_name']=='Tâm' and event['identity_evidence']=='Tâm'
    assert not event['needs_review']
    event.update(employee_name='Tâm',needs_review=True,review_reason='registry, unclear duration')
    repair_identity_evidence(event,snapshot)
    assert event['needs_review']


def test_ctv_parentheses_do_not_replace_real_sender_name():
    assert sender_name('テスト (Tên giả lập) (CTV)')=='Tên giả lập'


def test_full_name_without_accents_is_corrected_only_with_unique_source_support():
    snapshot=[{'message_id':'m','name':'Người báo hộ','body':'Lập OT 30 phút'},
              {'message_id':'n','name':'Đặng Thị Giả Lập','body':'Tin khác'}]
    event={'employee_name':'Dang Thi Gia Lap','source_message_ids':['m'],'identity_evidence':'wrong','person_id':'p'}
    repair_identity_evidence(event,snapshot)
    assert event['employee_name']=='Đặng Thị Giả Lập'
    assert event['identity_evidence']=='Lập'
