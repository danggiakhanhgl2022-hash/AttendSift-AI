"""Loopback-only application API with CSRF checks and serialized mutations."""
import hashlib
import json
from pathlib import Path
import secrets
import sys
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from ..utils.raw_message_export import export_raw_messages
from ..services.export_service import Vietnam_TZ
from urllib.parse import urlparse
from flask import Flask, request, jsonify, render_template, send_file, g
from werkzeug.exceptions import HTTPException
from .paths import APP_PATH, RESOURCE_PATH
from ..models.database import Database, MessageRepository, ConfigRepository, SyncHistoryRepository, ExportSessionRepository, ActionEventRepository
from ..services.sync_service import SyncService
from ..services.export_service import ExportService
from ..services.config_service import ConfigService
from ..services.history_service import HistoryService
from ..services.import_service import ImportService
from ..scheduler.windows_scheduler import WindowsScheduler
from ..utils.locking import BusyError


def create_app(app_path=APP_PATH):
    app=Flask(__name__,template_folder=str(Path(RESOURCE_PATH)/'templates'),
              static_folder=str(Path(RESOURCE_PATH)/'static'))
    app.config['TEMPLATES_AUTO_RELOAD'] = not getattr(sys, 'frozen', False)
    app.config['MAX_CONTENT_LENGTH']=16*1024*1024
    token=secrets.token_urlsafe(32)
    db=Database(str(Path(app_path)/'data'/'chamcong.db'))
    messages=MessageRepository(db);config=ConfigRepository(db);syncs=SyncHistoryRepository(db)
    sessions=ExportSessionRepository(db);actions=ActionEventRepository(db)
    sync=SyncService(db,config,messages,syncs,actions,app_path)
    export=ExportService(db,config,messages,sessions,actions,app_path);export.sync_service=sync
    settings=ConfigService(db,config,actions,app_path)
    scheduler=WindowsScheduler(app_path)
    history=HistoryService(db,actions,sessions,syncs)
    app.extensions['services']={'db':db,'config':config,'sync':sync,'export':export,'settings':settings,'scheduler':scheduler,'sessions':sessions,'actions':actions}

    @app.before_request
    def protect():
        host=request.host.split(':')[0]
        if host not in {'127.0.0.1','localhost'}:
            return jsonify(success=False,error='Host không hợp lệ.'),403
        origin=request.headers.get('Origin')
        if origin and origin!=request.host_url.rstrip('/'):
            return jsonify(success=False,error='Origin không hợp lệ.'),403
        if request.method not in {'GET','HEAD','OPTIONS'}:
            g.operation_id='REQ-'+uuid.uuid4().hex[:16]
            if not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),token):
                return jsonify(success=False,error='Phiên giao diện hết hạn. Hãy tải lại ứng dụng.'),403
            db.operation_lock.__enter__();g.operation_locked=True

    @app.teardown_request
    def release(error):
        if getattr(g,'operation_locked',False):
            g.operation_locked=False;db.operation_lock.__exit__(None,None,None)

    @app.after_request
    def headers(response):
        if getattr(g,'operation_id',None) and response.is_json:
            payload=response.get_json()
            if isinstance(payload,dict):
                data=payload.get('data')
                payload.setdefault('operation_id',data.get('operation_id',g.operation_id) if isinstance(data,dict) else g.operation_id)
                response.set_data(app.json.dumps(payload))
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.errorhandler(Exception)
    def errors(error):
        if isinstance(error,BusyError):return jsonify(success=False,error=str(error)),409
        if isinstance(error,ValueError):return jsonify(success=False,error=str(error)),400
        if isinstance(error,HTTPException):return jsonify(success=False,error=error.description),error.code
        app.logger.error('Thao tác thất bại: %s',type(error).__name__)
        return jsonify(success=False,error='Thao tác thất bại. Kiểm tra dữ liệu, kết nối và quyền ghi thư mục.'),500

    def body():
        data=request.get_json(silent=True)
        if not isinstance(data,dict):raise ValueError('Yêu cầu phải là JSON hợp lệ.')
        return data

    def ok(data=None,**extra):return jsonify(success=True,data=data,**extra)

    @app.get('/')
    def index():return render_template('index.html',csrf_token=token)

    @app.get('/api/version')
    def version():return ok(settings.get_app_version())

    def schedule_status():
        schedule=settings.get_sync_schedule()
        actual=scheduler.get_task_status()
        return {'configured':schedule,'applied':scheduler.public_status(actual),
                'requested':config.get('schedule_requested'),'last_result':config.get('schedule_last_result'),
                'path_changed':bool(actual and actual['path_changed'])}

    @app.get('/api/sync/status')
    def sync_status():return ok({**sync.get_status(),'schedule':schedule_status()})

    @app.post('/api/sync/run')
    def sync_run():return ok(sync.sync())

    @app.get('/api/sync/messages')
    def message_list():
        filters = {key: request.args[key] for key in ['start_time','end_time','sender','keyword'] if key in request.args}
        return ok(sync.get_messages(**filters, limit=bounded_limit(request.args.get('limit',100))))

    @app.post('/api/export/raw-messages')
    def raw_messages():
        data = body()
        month, year = data.get('month'), data.get('year')
        export._get_date_range(month, year)  # Reuse month/year validation only.
        room_id = config.get_chatwork_config().get('room_id')
        if not room_id:
            raise ValueError('Chưa chọn phòng Chatwork trong Thiết lập.')
        first = Vietnam_TZ.localize(datetime(year, month, 1))
        start = first - timedelta(days=15)
        end = Vietnam_TZ.localize(datetime(year + (month == 12), month % 12 + 1, 1))
        selected = []
        for message in messages.get_by_room(room_id):
            try:
                sent = datetime.fromisoformat(message['send_time'].replace('Z', '+00:00'))
                sent = Vietnam_TZ.localize(sent) if sent.tzinfo is None else sent.astimezone(Vietnam_TZ)
            except (ValueError, TypeError, KeyError):
                raise ValueError('Có tin nhắn có thời gian gửi không hợp lệ; hãy kiểm tra dữ liệu trước khi xuất.')
            if start <= sent < end:
                selected.append({**message, 'send_time': sent.isoformat()})
        if not selected:
            raise ValueError('Không có tin nhắn đã lưu trong khoảng ngày đã chọn.')
        stream = BytesIO()
        export_raw_messages(selected, stream)
        stream.seek(0)
        filename = f'TinNhan_{year}_{month:02d}_Tu_{start:%Y-%m-%d}_Den_{end-timedelta(days=1):%Y-%m-%d}.xlsx'
        actions.log_event('RAW-'+uuid.uuid4().hex, 'export', 'manual', 'success',
                          summary=f'Xuất {len(selected)} tin nhắn từ database.',
                          details={'month':month, 'year':year, 'message_count':len(selected),
                                   'period_start':start.isoformat(), 'period_end_exclusive':end.isoformat()})
        response = send_file(stream, as_attachment=True, download_name=filename,
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers['X-Message-Count'] = str(len(selected))
        return response

    @app.post('/api/data/import')
    def import_data():
        upload = request.files.get('file')
        if not upload or not upload.filename:
            raise ValueError('Hãy chọn file dữ liệu n8n.')
        result = ImportService(db, messages, config).import_file(upload.filename, upload.read())
        actions.log_event('IMPORT-'+uuid.uuid4().hex, 'import', 'manual', 'success',
                          summary=f'Nhập {result["added"]} tin nhắn lịch sử.', details=result)
        return ok(result)

    @app.get('/api/export/data-status')
    def export_data_status():
        try:
            month, year = int(request.args.get('month','')), int(request.args.get('year',''))
        except ValueError:
            raise ValueError('Tháng/năm không hợp lệ.') from None
        export._get_date_range(month,year)
        room_id=config.get('chatwork_room_id')
        selected=export._get_messages_for_month(room_id,month,year) if room_id else []
        risk=export._verify_data_risk(selected,month,year)
        return ok({**risk,'room_id':room_id,'room_name':config.get('chatwork_room_name'),
                   'requires_risk_acceptance':True})

    @app.post('/api/export/preflight')
    def preflight():
        data=body();return ok(export.preflight(data.get('month'),data.get('year')))

    @app.post('/api/export/create-session')
    def create_session():
        data=body();return ok(export.create_session(data.get('month'),data.get('year'),data.get('accept_risk',False),data.get('request_id')))

    @app.post('/api/export/<sid>/analyze')
    def analyze(sid):return ok(export.analyze(sid))

    @app.get('/api/export/<sid>/results')
    def results(sid):return ok(export.get_results(sid,request.args.get('include_excluded')=='true'))

    @app.get('/api/export/<sid>/review')
    def review_list(sid):return ok(export.get_results_for_review(sid))

    @app.post('/api/export/<sid>/review')
    def review(sid):
        data=body();return ok(export.review(sid,data.get('result_id'),data.get('changes'),data.get('exclude') is True))

    @app.post('/api/export/<sid>/correct')
    def correct(sid):
        data=body();return ok(export.apply_correction(data.get('result_id'),sid,data.get('field'),None,data.get('new_value')))

    @app.post('/api/export/<sid>/export')
    def excel(sid):return ok(export.export_to_excel(sid,body().get('overwrite') is True))

    @app.get('/api/export/<sid>')
    def session_detail(sid):
        session=sessions.get_session(sid)
        if not session:return jsonify(success=False,error='Phiên không tồn tại.'),404
        session['snapshot']=json.loads(session['snapshot']) if session.get('snapshot') else []
        session['ai_settings']=json.loads(session['ai_settings']) if session.get('ai_settings') else None
        session['corrections']=sessions.get_corrections(sid)
        session['events']=actions.get_by_session(sid)
        session['remaining']=len(export.get_results_for_review(sid))
        session['download_url']=f'/api/export/{sid}/download' if session['file_path'] else None
        return ok(session)

    @app.get('/api/export/<sid>/download')
    def download(sid):
        session=sessions.get_session(sid)
        if not session or session['status']!='exported' or not session['file_path']:
            raise ValueError('Phiên chưa có file đã xuất.')
        path=export.session_file(session)
        if not path:raise ValueError('File lịch sử không còn tồn tại. Vui lòng tạo lại bảng.')
        if session.get('file_hash') and hashlib.sha256(path.read_bytes()).hexdigest()!=session['file_hash']:
            raise ValueError('File đã thay đổi sau xuất; không tải bản không đúng lịch sử.')
        return send_file(path,as_attachment=True)

    @app.get('/api/export')
    @app.get('/api/export/sessions')
    def list_export_sessions():
        limit = bounded_limit(request.args.get('limit', 100))
        with db._get_connection() as conn:
            rows = conn.execute('SELECT session_id,month,year,status,created_at,updated_at,is_draft,file_path FROM export_sessions ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
        return ok([{**dict(row), 'download_url': f"/api/export/{row['session_id']}/download" if row['status']=='exported' and row['file_path'] else None} for row in rows])

    def bounded_limit(value):
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError('Giới hạn phải là số nguyên từ 1 đến 5000.') from None
        if not 1 <= number <= 5000:
            raise ValueError('Giới hạn phải là số nguyên từ 1 đến 5000.')
        return number

    @app.get('/api/history')
    def history_list():
        return ok(history.get_events(start_time=request.args.get('start_time'),end_time=request.args.get('end_time'),
            action_types=request.args.get('types').split(',') if request.args.get('types') else None,
            statuses=request.args.get('statuses').split(',') if request.args.get('statuses') else None,limit=bounded_limit(request.args.get('limit',500))))

    @app.get('/api/history/dashboard')
    def dashboard():return ok(history.get_dashboard_summary())

    @app.get('/api/config')
    def get_config():return ok({'chatwork':settings.get_chatwork_config(),'ai':settings.get_ai_config(),
                              'schedule':settings.get_sync_schedule(),'profiles':config.get('ai_profiles',{})})

    @app.post('/api/config/chatwork/test')
    def test_chatwork():
        result=settings.test_chatwork_connection(body().get('api_key',''))
        return jsonify(result),200 if result['success'] else 400

    @app.post('/api/config/chatwork')
    def chatwork():
        data=body();return ok(settings.save_chatwork_config(data.get('api_key'),data.get('room_id'),data.get('room_name')))

    @app.get('/api/config/chatwork/rooms')
    def rooms():return ok(settings.get_rooms())

    @app.post('/api/config/room')
    def room():
        data=body();return ok(settings.save_room(data.get('room_id'),data.get('room_name')))

    @app.post('/api/config/ai/test')
    def test_ai():
        data=body();return ok(settings.test_ai_connection(data.get('provider',''),data.get('api_key'),data.get('model'),data.get('base_url')))

    @app.post('/api/config/ai')
    def ai():
        data=body();return ok(settings.save_ai_config(data.get('provider',''),data.get('api_key'),data.get('model'),data.get('base_url'),data.get('set_default',True)))

    @app.post('/api/config/schedule')
    def schedule():
        data=body();return ok(settings.save_sync_schedule(data.get('hour'),data.get('minute'),scheduler=scheduler))

    @app.get('/api/config/schedule/status')
    def applied():return ok(schedule_status())

    @app.get('/api/backup')
    def backups():return ok(settings.list_backups())

    @app.post('/api/backup/create')
    def backup():return ok(settings.create_backup())

    @app.post('/api/backup/<name>/restore')
    def restore(name):
        if body().get('confirmed') is not True:raise ValueError('Cần xác nhận thay thế dữ liệu hiện tại.')
        return ok(settings.restore_backup(name))

    return app


def run_server(host='127.0.0.1',port=8766,debug=False):
    if host!='127.0.0.1':raise ValueError('Server chỉ được phép bind loopback.')
    create_app().run(host=host,port=port,debug=False,use_reloader=False)
