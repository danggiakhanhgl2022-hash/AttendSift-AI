"""Start the genuine Windows-local SQLite server and open its browser UI."""
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8766'

def _is_our_app():
    try:
        with urlopen(URL + '/api/version', timeout=0.7) as response:
            payload = json.loads(response.read())
            return response.status == 200 and payload.get('success') is True and 'data' in payload
    except (URLError, OSError, ValueError, TimeoutError):
        return False


def main():
    command = [sys.executable, str(ROOT / 'main.py'), '--headless', '--port', '8766']
    print('Starting ChamCongChatwork LOCAL (SQLite, 127.0.0.1)...', flush=True)
    process = subprocess.Popen(command, cwd=str(ROOT))
    try:
        ready = False
        for _ in range(60):
            if process.poll() is not None:
                print('The application stopped during startup. Read logs/application.log.', flush=True)
                return 1
            if _is_our_app():
                ready = True
                break
            time.sleep(0.5)
        if not ready:
            print('Could not reach 127.0.0.1:8766 after 30 seconds. Check port and logs.', flush=True)
            return 1
        print('READY: ' + URL, flush=True)
        print('Keep this window open. Press Ctrl+C here to stop the local server.', flush=True)
        webbrowser.open(URL)
        process.wait()
        return process.returncode or 0
    except KeyboardInterrupt:
        print('Stopping local application...', flush=True)
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()

if __name__ == '__main__':
    sys.exit(main())
