from src.services.identity_context import identity_hints,unique_short_name_evidence


def test_unique_short_name_uses_full_sender_from_another_batch():
    snapshot=[{'message_id':'1','name':'ユーザー (Người giả lập Tân)','body':'test'}]
    assert identity_hints(snapshot)[0]['employee_name']=='Người giả lập Tân'
    assert unique_short_name_evidence('Người giả lập Tân','Tân OT 30 phút',snapshot)


def test_namesake_or_team_alone_cannot_establish_identity():
    snapshot=[{'message_id':'1','name':'Người giả lập Tân','body':''},
              {'message_id':'2','name':'Một người khác Tân','body':''}]
    assert not unique_short_name_evidence('Người giả lập Tân','Tân OT 30 phút',snapshot)
    assert not unique_short_name_evidence('Người giả lập Tân','Team DemoBeta tăng ca',snapshot)
    assert not unique_short_name_evidence('Người giả lập Tâm','Tâm OT 30 phút',snapshot)
