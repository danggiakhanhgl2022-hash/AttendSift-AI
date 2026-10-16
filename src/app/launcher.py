"""Portable desktop lifecycle, single instance and graceful server shutdown."""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import threading
import webbrowser
from werkzeug.serving import make_server
from .paths import APP_PATH
from .server import create_app
from ..utils.locking import FileMutex,BusyError


def open_webview(port=8766):
    import webview
    loaded=threading.Event()
    window=webview.create_window(title='ChamCongChatwork — Chấm công từ Chatwork',url=f'http://127.0.0.1:{port}',
                                width=1200,height=800,min_size=(900,600),resizable=True)
    window.events.loaded += loaded.set
    watchdog=threading.Timer(20,lambda:window.destroy() if not loaded.is_set() else None)
    watchdog.start()
    try:
        webview.start(gui='edgechromium' if sys.platform == 'win32' else None, debug=False)
    finally:
        watchdog.cancel()
    return loaded.is_set()


def initialize(app):
    services=app.extensions['services']
    try:services['export'].recover()
    except BusyError:pass


def main():
    parser=argparse.ArgumentParser(description='ChamCongChatwork')
    parser.add_argument('--sync',action='store_true')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--check-runtime',metavar='REPORT')
    parser.add_argument('--check-desktop',metavar='REPORT')
    args=parser.parse_args()
    root=Path(APP_PATH)
    for folder in ['data','outputs','backups','logs','config']:(root/folder).mkdir(exist_ok=True)
    handler=RotatingFileHandler(root/'logs'/'application.log',maxBytes=2*1024*1024,backupCount=5,encoding='utf-8')
    logging.basicConfig(level=logging.INFO,handlers=[handler],format='%(asctime)s %(levelname)s %(message)s',force=True)
    if args.check_runtime:
        from ..utils.excel_export import verify_workbook, builtin_workbook_path
        report={}
        for name in ['webview','requests','openpyxl']:
            try:__import__(name);report[name]='ok'
            except Exception:report[name]='error'
        try:verify_workbook(builtin_workbook_path());report['template']='ok'
        except Exception:report['template']='error'
        Path(args.check_runtime).write_text(json.dumps(report,indent=2),encoding='utf-8')
        return 0 if all(v=='ok' for v in report.values()) else 1
    if args.check_desktop:
        import webview
        report={'native_webview':False}
        test_app=create_app();test_server=make_server('127.0.0.1',0,test_app,threaded=True)
        thread=threading.Thread(target=test_server.serve_forever,daemon=True);thread.start()
        window=webview.create_window('ChamCongChatwork acceptance',f'http://127.0.0.1:{test_server.server_port}',hidden=True)
        finished=threading.Event()
        def inspect():
            try:
                report['native_webview']=bool(window.evaluate_js("document.querySelectorAll('.nav-item').length===5 && document.querySelector('#appVersion').textContent.length>0"))
                report['settings_ready']=bool(window.evaluate_js("['sync','export','history','settings'].every(name=>!!document.getElementById(name+'-section')) && !!document.querySelector('#chatworkForm') && !!document.querySelector('#aiForm') && !!document.querySelector('#scheduleTime')"))
            except Exception:report['native_webview']=False
            finally:finished.set();window.destroy()
        window.events.loaded+=lambda:threading.Timer(2,inspect).start()
        watchdog=threading.Timer(30,lambda:window.destroy() if not finished.is_set() else None);watchdog.start()
        try:webview.start(gui='edgechromium' if sys.platform == 'win32' else None, debug=False)
        finally:
            watchdog.cancel();test_server.shutdown();thread.join();test_server.server_close()
            Path(args.check_desktop).write_text(json.dumps(report),encoding='utf-8')
        return 0 if report['native_webview'] and report.get('settings_ready') else 1
    if args.sync:
        try:create_app().extensions['services']['sync'].catch_up('scheduled');return 0
        except BusyError:
            logging.info('Đồng bộ đang chờ thao tác khác; Windows sẽ thử lại theo lịch.')
            return 1
        except Exception:logging.error('Đồng bộ theo lịch thất bại.');return 1
    mutex=FileMutex(root/'data'/'desktop.lock')
    try:mutex.__enter__()
    except BusyError:
        try:
            port=json.loads((root/'data'/'instance.json').read_text())['port']
            if not args.headless:webbrowser.open(f'http://127.0.0.1:{port}')
        except (ValueError,OSError):pass
        return 0
    stop=threading.Event();server=None;server_thread=None
    try:
        app=create_app()
        services=app.extensions['services']
        server=make_server('127.0.0.1',args.port,app,threaded=True)
        (root/'data'/'instance.json').write_text(json.dumps({'port':args.port}),encoding='utf-8')
        initialize(app)
        def recovery():
            while not stop.is_set():
                try:services['sync'].catch_up('catchup')
                except Exception:logging.warning('Chạy bù chưa thành công; sẽ kiểm tra lại khi ứng dụng đang mở.')
                stop.wait(60)
        worker=threading.Thread(target=recovery,daemon=True);worker.start()
        if args.headless:
            server.serve_forever()
        else:
            server_thread=threading.Thread(target=server.serve_forever,daemon=True);server_thread.start()
            try:
                if not open_webview(args.port):
                    raise RuntimeError('Native webview did not load')
            except Exception:
                # Keep the local service alive if Edge/WebView2 is unavailable.
                webbrowser.open(f'http://127.0.0.1:{args.port}')
                server_thread.join()
        return 0
    except (OSError,ValueError):
        logging.error('Không khởi động được ứng dụng. Kiểm tra cổng và quyền ghi thư mục.')
        if not args.headless and sys.platform=='win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,'Không mở được ứng dụng. Kiểm tra quyền ghi thư mục hoặc cổng đang sử dụng.','ChamCongChatwork',16)
        return 1
    finally:
        stop.set()
        if server:
            # server.shutdown is only needed when serve_forever runs in another thread.
            if server_thread is not None and server_thread.is_alive():
                server.shutdown()
                server_thread.join(timeout=5)
            server.server_close()
        mutex.__exit__(None,None,None)


if __name__=='__main__':sys.exit(main())
