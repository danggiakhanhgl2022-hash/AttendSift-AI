from src.utils.message_cleaning import clean_message_body
import pytest


@pytest.mark.parametrize('name,label', [
    ('Nhân vật thử A', 'ユン（Nhân vật thử A）'),
    ('Nhân vật thử B', 'ダン（Nhân vật thử B）'),
    ('Nhân vật thử C', 'クアン (Nhân vật thử C)'),
    ('Nhân vật thử A', 'ユン（ Nhân  vật thử A ）'),
])
def test_all_senders_and_fullwidth_parentheses(name, label):
    body = label + '\n' + label + ' B PRODUCTIONS COMPANY LIMITED\nXin nghỉ 30 phút'
    assert clean_message_body(body, name) == label + '\nXin nghỉ 30 phút'


def test_removes_display_labels_and_reaction_pairs():
    body = 'クアン (Nhân vật thử C)\nクアン (Nhân vật thử C)B PRODUCTIONS COMPANY LIMITED\nTăng ca 2 giờ\nroger\n1\nbow\n1'
    assert clean_message_body(body, 'Nhân vật thử C') == 'クアン (Nhân vật thử C)\nTăng ca 2 giờ'


def test_company_label_alone_keeps_name_once():
    assert clean_message_body('TesterB PRODUCTIONS COMPANY LIMITED\nTester\nOT 2 hours', 'Tester') == 'Tester\nOT 2 hours'


def test_preserves_business_text_numbers_and_quotes():
    body = 'A và B tăng ca\n30\nroger\nTrích dẫn: xin về sớm\nXin về sớm'
    assert clean_message_body(body, 'A') == body


def test_does_not_remove_other_sender():
    assert clean_message_body('ユン (Nhân vật thử A)\nNội dung', 'A') == 'ユン (Nhân vật thử A)\nNội dung'
