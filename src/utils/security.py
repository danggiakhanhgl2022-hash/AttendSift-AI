"""Windows user-bound credentials, deliberately outside SQLite backups."""
import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path


class SecretError(ValueError):
    pass


def dpapi(data, decrypt=False):
    if os.name != 'nt':
        raise SecretError('Kho khóa yêu cầu Windows. Vui lòng nhập lại API key trên Windows.')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise SecretError('Không giải mã được khóa trên tài khoản này. Vui lòng nhập lại API key.')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        free = ctypes.WinDLL('kernel32').LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        free(target.data)


class SecretStore:
    def __init__(self, db_path):
        self.path = Path(str(db_path) + '.credentials')

    def _read(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding='utf-8'))

    def get(self, key):
        encoded = self._read().get(key)
        if not encoded:
            return None
        return dpapi(base64.b64decode(encoded), decrypt=True).decode('utf-8')

    def set(self, key, value):
        data = self._read()
        if value:
            data[key] = base64.b64encode(dpapi(str(value).encode('utf-8'))).decode('ascii')
        else:
            data.pop(key, None)
        temporary = self.path.with_suffix('.credentials.tmp')
        temporary.write_text(json.dumps(data), encoding='utf-8')
        os.replace(temporary, self.path)


SECRET_KEYS = {'chatwork_api_key', 'ai_api_key'}
