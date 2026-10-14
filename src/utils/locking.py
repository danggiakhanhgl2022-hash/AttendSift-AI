"""One reentrant, interprocess maintenance lock per database."""
import os
import threading
from pathlib import Path

_registry = {}
_registry_guard = threading.Lock()


class BusyError(ValueError):
    pass


class FileMutex:
    def __init__(self, path):
        self.path = str(Path(path).resolve())
        with _registry_guard:
            self.state = _registry.setdefault(self.path, {'guard': threading.RLock(), 'depth': 0})

    def __enter__(self):
        if not self.state['guard'].acquire(blocking=False):
            raise BusyError('Một thao tác đang chạy. Vui lòng chờ hoàn tất rồi thử lại.')
        try:
            if self.state['depth'] == 0:
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)
                handle = open(self.path, 'a+b')
                handle.seek(0)
                try:
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    handle.close()
                    raise BusyError('Ứng dụng đang xử lý dữ liệu ở tiến trình khác.')
                self.state['handle'] = handle
            self.state['depth'] += 1
            return self
        except Exception:
            self.state['guard'].release()
            raise

    def __exit__(self, *args):
        self.state['depth'] -= 1
        if self.state['depth'] == 0:
            self.state.pop('handle').close()
        self.state['guard'].release()
