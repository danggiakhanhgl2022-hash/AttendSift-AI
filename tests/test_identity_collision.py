from copy import deepcopy

from src.services.identity_context import align_event_identities


def source(message_id, account_id, name, body):
    return {'message_id': message_id, 'account_id': account_id, 'name': name, 'body': body}


def event(person_id, employee_name, message_id):
    return {'person_id': person_id, 'employee_name': employee_name, 'source_message_ids': [message_id]}


def test_different_verified_people_with_one_model_id_are_split():
    snapshot = [source('a', 101, 'Người Giả Lập', 'Lập OT 30 phút'),
                source('b', 202, 'Một Người Khác', 'Khác OT 30 phút')]
    rows = [event('P1', 'Người Giả Lập', 'a'), event('P1', 'Một Người Khác', 'b')]
    align_event_identities(rows, snapshot)
    assert rows[0]['person_id'] != rows[1]['person_id']
    assert all(row['person_id'].startswith('SRC-A-') for row in rows)


def test_same_verified_sender_alternate_model_ids_align_without_changing_original():
    snapshot = [source('a', 101, 'Người Giả Lập', 'Em OT 30 phút'),
                source('b', 101, 'Người Giả Lập', 'Em OT 60 phút')]
    raw = [event('P1', 'Người Giả Lập', 'a'), event('OTHER', 'Người Giả Lập', 'b')]
    derived = deepcopy(raw)
    align_event_identities(derived, snapshot)
    assert derived[0]['person_id'] == derived[1]['person_id']
    assert [row['person_id'] for row in raw] == ['P1', 'OTHER']


def test_identical_names_with_different_linked_sender_accounts_never_merge():
    snapshot = [source('a', 101, 'Người Giả Lập', 'Em OT 30 phút'),
                source('b', 202, 'Người Giả Lập', 'Em OT 60 phút')]
    rows = [event('P1', 'Người Giả Lập', 'a'), event('P2', 'Người Giả Lập', 'b')]
    align_event_identities(rows, snapshot)
    assert rows[0]['person_id'] != rows[1]['person_id']


def test_unique_alias_in_report_matches_real_sender_from_another_batch():
    snapshot = [source('report', 303, 'Người Báo Hộ', 'Lập, Khác OT 30 phút'),
                source('a', 101, 'Người Giả Lập', 'Em về sớm'),
                source('b', 202, 'Một Người Khác', 'Em nghỉ')]
    rows = [event('P1', 'Người Giả Lập', 'report'), event('P9', 'Lập', 'report'),
            event('P1', 'Một Người Khác', 'report')]
    align_event_identities(rows, snapshot)
    assert rows[0]['person_id'] == rows[1]['person_id']
    assert rows[0]['employee_name'] == rows[1]['employee_name'] == 'Người Giả Lập'
    assert rows[0]['person_id'] != rows[2]['person_id']


def test_ambiguous_alias_in_report_is_not_assigned_to_either_account():
    snapshot = [source('report', 303, 'Người Báo Hộ', 'Lập OT 30 phút'),
                source('a', 101, 'Người Giả Lập', ''),
                source('b', 202, 'Người Khác Lập', '')]
    rows = [event('UNRESOLVED', 'Lập', 'report')]
    align_event_identities(rows, snapshot)
    assert rows[0]['person_id'] == 'UNRESOLVED'
    assert rows[0]['employee_name'] == 'Lập'
    assert rows[0]['identity_uncertain'] is True


def test_same_name_without_accounts_does_not_merge_alternate_model_ids():
    snapshot = [source('a', None, 'Người Giả Lập', 'Em OT 30 phút'),
                source('b', None, 'Người Giả Lập', 'Em OT 60 phút')]
    rows = [event('P1', 'Người Giả Lập', 'a'), event('P2', 'Người Giả Lập', 'b')]
    align_event_identities(rows, snapshot)
    assert [row['person_id'] for row in rows] == ['P1', 'P2']


def test_unverified_names_reusing_model_id_split_without_inventing_full_names():
    snapshot = [source('report', 303, 'Người Báo Hộ', 'Lập, An (CTV) OT 30 phút')]
    rows = [event('P1', 'Lập', 'report'), event('P1', 'An (CTV)', 'report')]
    align_event_identities(rows, snapshot)
    assert rows[0]['person_id'] != rows[1]['person_id']
    assert [row['employee_name'] for row in rows] == ['Lập', 'An (CTV)']


def test_identity_alignment_is_deterministic_across_input_order():
    snapshot = [source('a', 101, 'Người Giả Lập', 'Em OT 30 phút'),
                source('b', 202, 'Một Người Khác', 'Em OT 60 phút')]
    rows = [event('P1', 'Người Giả Lập', 'a'), event('P1', 'Một Người Khác', 'b')]
    reverse = deepcopy(rows[::-1])
    align_event_identities(rows, snapshot)
    align_event_identities(reverse, snapshot[::-1])
    assert rows == reverse[::-1]


def test_invalid_model_source_ids_remain_available_for_local_validation():
    snapshot = [source('a', 101, 'Người Giả Lập', 'Em OT 30 phút')]
    row = event('P1', 'Người Giả Lập', 'a')
    row['source_message_ids'] = [{'invalid': 'a'}]
    align_event_identities([row], snapshot)
    assert row['person_id'] == 'P1'


def test_placeholder_account_zero_cannot_merge_two_people():
    snapshot = [source('a', 0, 'Người Giả Lập', 'Em OT 30 phút'),
                source('b', 0, 'Một Người Khác', 'Em OT 60 phút')]
    rows = [event('P1', 'Người Giả Lập', 'a'), event('P2', 'Một Người Khác', 'b')]
    align_event_identities(rows, snapshot)
    assert [row['person_id'] for row in rows] == ['P1', 'P2']


def test_malformed_model_person_id_is_not_repaired_by_sender_account():
    snapshot = [source('a', 101, 'Người Giả Lập', 'Em OT 30 phút')]
    for malformed in (None, [], {}, 123, True):
        row = event(malformed, 'Người Giả Lập', 'a')
        align_event_identities([row], snapshot)
        assert row['person_id'] is malformed


def test_vietnamese_tone_differences_split_reused_model_identity():
    snapshot=[source('report',303,'Người Tổng Hợp','Bảo, Báo OT 30 phút')]
    rows=[event('MODEL-SAME','Bảo','report'),event('MODEL-SAME','Báo','report')]
    align_event_identities(rows,snapshot)
    assert rows[0]['person_id'] != rows[1]['person_id']
    assert all(e['person_id'].startswith('SRC-U-') for e in rows)
