"""Separate persistent portable data from bundled read-only resources."""
import os
import sys

APP_PATH = (os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)
            else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RESOURCE_PATH = getattr(sys, '_MEIPASS', APP_PATH)


def user_downloads_dir():
    """Find this Windows user's Downloads, including a relocated Known Folder.

    Use the OS account, not the application's portable/executable location.
    No directory is created until a file is actually exported.
    """
    from pathlib import Path
    if sys.platform == 'win32':
        try:
            import ctypes
            import uuid
            from ctypes import wintypes

            class GUID(ctypes.Structure):
                _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD),
                            ('Data3', wintypes.WORD), ('Data4', ctypes.c_ubyte * 8)]

            folder_id = GUID.from_buffer_copy(
                uuid.UUID('374DE290-123F-4565-9164-39C4925E467B').bytes_le
            )
            address = ctypes.c_wchar_p()
            shell = ctypes.windll.shell32
            shell.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD,
                                                  wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)]
            shell.SHGetKnownFolderPath.restype = ctypes.c_long
            status = shell.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(address))
            try:
                if status == 0 and address.value:
                    return Path(address.value)
            finally:
                if address:
                    ctypes.windll.ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
                    ctypes.windll.ole32.CoTaskMemFree(ctypes.cast(address, ctypes.c_void_p))
        except (AttributeError, OSError, ValueError):
            # Old/locked-down Windows: resolve the standard user-profile folder.
            pass
        return Path(os.environ.get('USERPROFILE') or Path.home()) / 'Downloads'
    return Path.home() / 'Downloads'
