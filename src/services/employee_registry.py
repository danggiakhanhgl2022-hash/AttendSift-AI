"""Private, revisioned employee registry stored in existing application settings."""
import copy
import hashlib
import json
import re
import unicodedata
import uuid
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from flask import request, jsonify

KEY = 'employee_registry_v1'


def name_key(value):
    return ' '.join(unicodedata.normalize('NFC', str(value or '')).casefold().split())


def clean_text(value, field, limit=200):
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError(f'{field}: dữ liệu không hợp lệ.')
    return ' '.join(unicodedata.normalize('NFC', value).split())


class EmployeeRegistry:
    def __init__(self, get, set_value, lock=None, audit=None):
        self.get, self.set = get, set_value
        self.lock = lock or nullcontext
        self.audit = audit or (lambda *args: None)

    def read(self):
        value = self.get(KEY, None)
        return copy.deepcopy(value) if value is not None else {
            'version': 1, 'initialized': False, 'revision': 0, 'employees': []}

    def _save(self, value, action):
        value['initialized'] = True
        value['revision'] += 1
        self.set(KEY, value)
        self.audit(action, value['revision'])

    def _entry(self, data, existing=None):
        allowed = {'employee_code', 'full_name', 'aliases', 'chatwork_account_id', 'active'}
        if not isinstance(data, dict) or set(data) - allowed:
            raise ValueError('Thông tin nhân viên không hợp lệ.')
        item = dict(existing or {})
        item.update(data)
        item['full_name'] = clean_text(item.get('full_name', ''), 'Họ tên')
        if not item['full_name']:
            raise ValueError('Cần nhập họ tên.')
        for field in ('employee_code', 'chatwork_account_id'):
            item[field] = clean_text(item.get(field, ''), field, 100)
        if item['chatwork_account_id'] and not item['chatwork_account_id'].isdigit():
            raise ValueError('Chatwork account ID phải là chữ số.')
        aliases = item.get('aliases', [])
        if not isinstance(aliases, list) or len(aliases) > 50:
            raise ValueError('Tên thường dùng phải là danh sách tối đa 50 tên.')
        item['aliases'] = list(dict.fromkeys(clean_text(v, 'Tên thường dùng') for v in aliases))
        if any(not v for v in item['aliases']):
            raise ValueError('Tên thường dùng không được trống.')
        item.setdefault('active', True)
        if type(item['active']) is not bool:
            raise ValueError('Trạng thái nhân viên không hợp lệ.')
        now = datetime.now(timezone.utc).isoformat()
        item.setdefault('id', 'EMP-' + uuid.uuid4().hex)
        item.setdefault('created_at', now)
        item['updated_at'] = now
        return item

    def _check_unique(self, items):
        codes, accounts, identities = set(), set(), {}
        for item in items:
            code, account = name_key(item['employee_code']), item['chatwork_account_id']
            if code and code in codes:
                raise ValueError('Mã nhân viên đã tồn tại.')
            if account and account in accounts:
                raise ValueError('Chatwork account ID đã gắn với nhân viên khác.')
            codes.add(code) if code else None
            accounts.add(account) if account else None
            if not item['active']:
                continue
            for alias in {name_key(item['full_name']), *(name_key(a) for a in item['aliases'])}:
                prior = identities.get(alias)
                if prior and prior['id'] != item['id']:
                    # Names may overlap; stable, distinct employee codes or Chatwork
                    # accounts are required so a reviewer can distinguish them.
                    if not (item['employee_code'] or item['chatwork_account_id']) or not (prior['employee_code'] or prior['chatwork_account_id']):
                        raise ValueError('Tên trùng: mỗi người cần mã nhân viên hoặc Chatwork Account ID riêng để đối chiếu.')
                identities[alias] = item

    def upsert(self, data, employee_id=None):
        with self.lock():
            value = self.read()
            existing = next((e for e in value['employees'] if e['id'] == employee_id), None)
            if employee_id and existing is None:
                raise ValueError('Nhân viên không tồn tại.')
            item = self._entry(data, existing)
            items = [e for e in value['employees'] if e['id'] != item['id']] + [item]
            self._check_unique(items)
            value['employees'] = items
            self._save(value, 'update' if existing else 'create')
            return item

    def import_entries(self, entries):
        if not isinstance(entries, list) or not entries or len(entries) > 10000:
            raise ValueError('Cần danh sách từ 1 đến 10000 nhân viên.')
        with self.lock():
            value = self.read()
            items = list(value['employees'])
            added = 0
            for entry in entries:
                supplied_identity = isinstance(entry, dict) and bool(
                    entry.get('employee_code') or entry.get('chatwork_account_id'))
                entry = {'full_name': entry} if isinstance(entry, str) else entry
                item = self._entry(entry)
                if any((item['employee_code'] and item['employee_code'] == old['employee_code']) or
                       (item['chatwork_account_id'] and item['chatwork_account_id'] == old['chatwork_account_id']) or
                       (not supplied_identity and name_key(item['full_name']) == name_key(old['full_name']))
                       for old in items):
                    continue  # Never overwrite/re-enable existing employee records.
                items.append(item)
                added += 1
            self._check_unique(items)
            value['employees'] = items
            if added or not value['initialized']:
                self._save(value, 'import')
            return {'added': added, 'total': len(items)}

    def seed_once(self, path):
        path = Path(path)
        if not path.exists() or self.read()['initialized']:
            return
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        with self.lock():
            if not self.read()['initialized']:
                self.import_entries(data['employees'] if isinstance(data, dict) else data)

    def snapshot(self, confirm_empty=False):
        value = self.read()
        if not any(e['active'] for e in value['employees']) and confirm_empty is not True:
            raise ValueError('Danh sách chính thức đang trống. Thêm/nhập nhân viên hoặc xác nhận rõ tiếp tục xếp người xác định được vào CTV.')
        value['policy_version'] = 1
        return value


def register_employee_routes(app, registry):
    @app.get('/api/employees')
    def employee_list():
        value = registry.read()
        return jsonify(success=True, data=value)

    @app.post('/api/employees')
    def employee_create():
        return jsonify(success=True, data=registry.upsert(request.get_json(silent=True)))

    @app.post('/api/employees/import')
    def employee_import():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError('Cần dữ liệu JSON hợp lệ.')
        return jsonify(success=True, data=registry.import_entries(data.get('employees')))

    @app.post('/api/employees/<employee_id>')
    def employee_update(employee_id):
        return jsonify(success=True, data=registry.upsert(request.get_json(silent=True), employee_id))
