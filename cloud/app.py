"""Cloud API: authenticated users, Neon state, one AI batch per invocation."""
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from io import BytesIO
from pathlib import Path
import copy
import hashlib
import json
import os
import logging
import secrets
import uuid

from flask import Flask, jsonify, render_template, request, send_file, session, redirect, g
from werkzeug.exceptions import HTTPException
from .security import validate_admin_hash, verify_admin_password, token_digest
from .repository import LeaseBusy, PostgresRepository
from src.adapters.ai_adapters import create_ai_adapter, AIHTTPError, AIResponseError, PROPERTIES
from src.adapters.chatwork_adapter import ChatworkAdapter, ChatworkAPIError
from src.services.identity_context import identity_hints, repair_identity_evidence, align_event_identities
from src.services.validation import validate_set
from src.utils.raw_message_export import export_raw_messages
from src.utils.excel_export import export_to_excel

TZ = timezone(timedelta(hours=7))
MAX_FILE = 4_000_000


class PublicError(ValueError):
    """Only explicitly safe, application-authored messages may reach clients."""


def period(month, year, raw=False):
    if type(month) is not int or type(year) is not int or not 1 <= month <= 12 or not 2000 <= year <= 2100:
        raise ValueError('Tháng/năm không hợp lệ.')
    first = datetime(year, month, 1, tzinfo=TZ)
    previous = first - timedelta(days=1)
    start = first-timedelta(days=15) if raw else previous.replace(day=15)
    end = datetime(year+(month == 12), month % 12+1, 1, tzinfo=TZ)
    return start, end


def finalize(raw_events, snapshot, month, year, sid, employee_aliases=None):
    events = copy.deepcopy(raw_events)
    from src.services.source_reconciliation import reconcile_explicit_records
    reconcile_explicit_records(events, snapshot, month, year)
    for event in events:
        repair_identity_evidence(event, snapshot)
    align_event_identities(events, snapshot)
    from src.services.event_policy import mark_information_only, mark_ctv_source_only, mark_annual_leave_source_only, reason_from_source
    for index, event in enumerate(events, 1):
        event['event_id'] = f'EVT{index:05d}'
        mark_information_only(event, snapshot)
        mark_ctv_source_only(event, snapshot)
        mark_annual_leave_source_only(event, snapshot)
        event['reason'] = reason_from_source(event, snapshot)
        official_name = (employee_aliases or {}).get(event.get('employee_name'))
        if official_name and not event.get('is_excluded'):
            event['employee_name'] = official_name
        try:
            day = date.fromisoformat(event.get('event_date', ''))
            outside = (day.month, day.year) != (month, year)
        except (TypeError, ValueError):
            outside = False
        if outside:
            event['is_excluded'] = True
            event['review_reason'] = 'Ngoài tháng xuất; giữ toàn bộ tin nguồn.'
        if event.get('is_excluded'):
            event['review_state'] = 'excluded'
            event['validation_errors'] = []
            event['validation_warnings'] = []
    kept = [event for event in events if not event.get('is_excluded')]
    validate_set(kept, snapshot, month, year)
    for event in kept:
        event['review_state'] = 'pending' if event['validation_errors'] or event['validation_warnings'] else 'valid'
    return events


def bounded_ai(provider, api_key, model, base_url=None):
    """One 90-second attempt; persistent checkpoint owns retry, not a long loop."""
    import requests
    adapter = create_ai_adapter(provider=provider, api_key=api_key, model=model, base_url=base_url)
    def call(method, endpoint, headers, payload=None):
        try:
            response = requests.request(method, adapter.base_url+endpoint, headers=headers,
                                        json=payload, timeout=(10,90), allow_redirects=False)
            if response.status_code >= 300:
                raise AIHTTPError(response.status_code)
            return response.json()
        except requests.Timeout:
            raise AIResponseError('timeout') from None
        except requests.RequestException:
            raise AIResponseError('connection') from None
        except ValueError as error:
            if isinstance(error, (AIHTTPError, AIResponseError)):
                raise
            raise AIResponseError('json') from None
    adapter._request = call
    return adapter


class CloudChatwork(ChatworkAdapter):
    def _request(self, method, endpoint, params=None, data=None, retry_count=1):
        return super()._request(method, endpoint, params, data, retry_count=1)


def create_app(repository=None, config=None, ai_factory=bounded_ai, chatwork_factory=CloudChatwork):
    env = dict(os.environ)
    if config:
        env.update(config)
    try:
        if 'CHAMCONG_CTV_ALIASES' in env:
            json_ctv = json.loads(env['CHAMCONG_CTV_ALIASES'])
            if (not isinstance(json_ctv, list) or
                any(not isinstance(item, str) or not item.strip() for item in json_ctv)):
                raise ValueError()
    except (ValueError, TypeError):
        raise RuntimeError('CHAMCONG_CTV_ALIASES phải là mảng JSON tên CTV đã xác nhận.') from None
    try:
        employee_aliases = json.loads(env.get('CHAMCONG_EMPLOYEE_ALIASES', '{}'))
        if not isinstance(employee_aliases, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not v.strip() for k,v in employee_aliases.items()):
            raise ValueError()
    except (ValueError, TypeError):
        raise RuntimeError('CHAMCONG_EMPLOYEE_ALIASES phải là JSON tên ngắn: họ tên đầy đủ.') from None
    secret = env.get('CHAMCONG_SESSION_SECRET', '')
    password_hash = env.get('CHAMCONG_ADMIN_PASSWORD_HASH', '')
    if len(secret) < 32:
        raise RuntimeError('Cần session secret ít nhất 32 ký tự.')
    validate_admin_hash(password_hash)
    repo = repository or PostgresRepository(env.get('DATABASE_URL'))
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.update(SECRET_KEY=secret, MAX_CONTENT_LENGTH=MAX_FILE, DEBUG=False,
        PROPAGATE_EXCEPTIONS=False, SESSION_REFRESH_EACH_REQUEST=False,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=env.get('CHAMCONG_INSECURE_LOCAL') != '1',
        SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=1))
    app.logger.setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    app.extensions['repository'] = repo
    hosts = {host.strip().lower() for host in env.get('CHAMCONG_ALLOWED_HOSTS', '').split(',') if host.strip()}
    if not hosts:
        raise RuntimeError('Cần CHAMCONG_ALLOWED_HOSTS; không mặc định mở dữ liệu nhân viên ra Internet.')

    @app.before_request
    def protection():
        g.request_id = uuid.uuid4().hex
        if app.debug:
            return jsonify(success=False,error='Chế độ debug không được phép trên web này.'),503
        if request.host.split(':')[0].lower() not in hosts:
            return jsonify(success=False, error='Host không hợp lệ.'), 403
        if request.endpoint in {'static', 'health', 'readiness', 'login', 'cron'}:
            return None
        auth_token = session.get('auth_token')
        if (not session.get('authenticated') or not isinstance(auth_token, str) or
                not repo.auth_session_valid(token_digest(auth_token), 900)):
            session.clear()
            if request.endpoint == 'index':
                return redirect('/login')
            return jsonify(success=False, error='Cần đăng nhập.'), 401
        if request.method not in {'GET','HEAD','OPTIONS'}:
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'):
                return jsonify(success=False, error='Origin không hợp lệ.'), 403
            token = request.headers.get('X-CSRF-Token','')
            if not secrets.compare_digest(token, session.get('csrf','')) or not token:
                return jsonify(success=False, error='Phiên giao diện hết hạn; tải lại trang.'),403

    @app.after_request
    def security_headers(response):
        response.headers['X-Request-ID'] = getattr(g,'request_id','')
        if env.get('CHAMCONG_INSECURE_LOCAL') != '1':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
            'X-Frame-Options':'DENY','Referrer-Policy':'same-origin',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"})
        return response

    def track_failure(category):
        event_id = getattr(g,'request_id',uuid.uuid4().hex)
        # Deliberately omit exception text, URLs, headers, request data and SQL.
        app.logger.error(json.dumps({'event':'request_failed','id':event_id,'category':category}))
        try:
            repo.log('error','failed','Lỗi xử lý; mã tham chiếu '+event_id,
                     details={'error_id':event_id,'category':category})
        except Exception:
            pass  # Database outages must not prevent the safe error response.
        return event_id

    @app.errorhandler(Exception)
    def errors(error):
        if isinstance(error, LeaseBusy):
            return jsonify(success=False,error='Tác vụ đang được xử lý. Thử lại sau.'),409
        if isinstance(error,(AIHTTPError,AIResponseError)):
            event_id=track_failure('upstream')
            return jsonify(success=False,error='Dịch vụ phân tích chưa sẵn sàng. Thử lại sau.',error_id=event_id),502
        if isinstance(error,PublicError):
            return jsonify(success=False,error=str(error)),400
        if isinstance(error,ValueError):
            return jsonify(success=False,error='Dữ liệu hoặc cấu hình không hợp lệ.'),400
        if isinstance(error,HTTPException):
            return jsonify(success=False,error='Yêu cầu không hợp lệ.'),error.code
        event_id=track_failure('internal')
        return jsonify(success=False,error='Thao tác thất bại. Liên hệ người quản trị với mã tham chiếu.',error_id=event_id),500

    def body():
        value = request.get_json(silent=True)
        if not isinstance(value,dict):
            raise ValueError('Cần JSON hợp lệ.')
        return value

    def ok(data):
        return jsonify(success=True,data=data)

    def room():
        selected = repo.get_setting('room', None)
        if selected:
            return selected['room_id']
        value = env.get('CHATWORK_ROOM_ID','')
        if not value.isdigit():
            raise ValueError('Chưa cấu hình phòng Chatwork.')
        return value

    def get_session(sid):
        value = repo.session(sid)
        if not value:
            raise ValueError('Phiên không tồn tại.')
        return value

    def settings():
        provider = env.get('AI_PROVIDER','gemini')
        key_name = {'gemini':'GEMINI_API_KEY','anthropic':'ANTHROPIC_API_KEY',
                    'openai':'OPENAI_API_KEY','openai_compatible':'OPENAI_API_KEY'}.get(provider)
        if not key_name or not env.get(key_name):
            raise ValueError('Chưa cấu hình API key AI phía máy chủ.')
        return {'provider':provider,'model':env.get('AI_MODEL') or None,'base_url':env.get('AI_BASE_URL') or None},env[key_name]

    @app.get('/health')
    def health():
        return ok({'service':'ChamCongChatwork cloud','status':'alive'})

    @app.get('/health/ready')
    def readiness():
        if repo.ready():
            return ok({'status':'ready'})
        return jsonify(success=False,error='Dịch vụ chưa sẵn sàng.'),503

    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        origin=request.headers.get('Origin')
        if origin and origin != request.host_url.rstrip('/'):
            return jsonify(success=False,error='Origin không hợp lệ.'),403
        fingerprint=hashlib.sha256((secret+'|'+str(request.remote_addr)).encode()).hexdigest()
        global_key=hashlib.sha256((secret+'|admin-login').encode()).hexdigest()
        if not repo.login_allowed(fingerprint) or not repo.login_allowed(global_key,limit=100):
            return jsonify(success=False,error='Thử đăng nhập quá nhiều. Chờ 15 phút.'),429,{'Retry-After':'900'}
        password=body().get('password','')
        if not verify_admin_password(password_hash,password):
            return jsonify(success=False,error='Mật khẩu không đúng.'),401
        previous=session.get('auth_token')
        if isinstance(previous,str):
            repo.revoke_auth_session(token_digest(previous))
        session.clear()
        auth_token=secrets.token_urlsafe(48)
        repo.create_auth_session(token_digest(auth_token),3600)
        session['auth_token']=auth_token
        session['authenticated']=True
        session['csrf']=secrets.token_urlsafe(32)
        session.permanent=True
        return ok({'csrf_token':session['csrf']})

    @app.post('/logout')
    def logout():
        repo.revoke_auth_session(token_digest(session['auth_token']))
        session.clear()
        return ok({})

    @app.get('/')
    def index():
        return render_template('index.html',csrf_token=session['csrf'])

    @app.get('/api/config')
    def config_status():
        selected=repo.get_setting('room',{'room_id':env.get('CHATWORK_ROOM_ID',''),'room_name':''})
        return ok({'room':selected,'ai_provider':env.get('AI_PROVIDER','gemini'),
                   'ai_model':env.get('AI_MODEL',''),'has_chatwork_key':bool(env.get('CHATWORK_API_KEY')),
                   'schedule':'13:00 UTC+7 (06:00 UTC); cloud Cron',
                   'keys_managed_in':'Vercel Environment Variables'})

    @app.get('/api/rooms')
    def rooms():
        if not env.get('CHATWORK_API_KEY'):
            raise ValueError('Chưa cấu hình CHATWORK_API_KEY phía máy chủ.')
        return ok(chatwork_factory(env['CHATWORK_API_KEY']).get_rooms())

    @app.post('/api/room')
    def select_room():
        value=body().get('room_id')
        if not isinstance(value,str) or not value.isdigit():
            raise ValueError('Room ID không hợp lệ.')
        available=chatwork_factory(env.get('CHATWORK_API_KEY','')).get_rooms()
        selected=next((r for r in available if str(r.get('room_id'))==value),None)
        if not selected:
            raise ValueError('Room không thuộc quyền API.')
        repo.set_setting('room',{'room_id':value,'room_name':selected.get('name','')})
        return ok({'room_id':value})

    def run_sync():
        selected=room()
        if not env.get('CHATWORK_API_KEY'):
            raise ValueError('Chưa cấu hình CHATWORK_API_KEY.')
        with repo.lease('sync:'+selected,seconds=120) as owner:
            adapter=chatwork_factory(env['CHATWORK_API_KEY'])
            raw=adapter.get_recent_messages(selected)
            messages=[]
            for item in raw:
                value=adapter.normalize_message({**item,'room_id':selected})
                if not value['message_id'] or not isinstance(value['body'],str):
                    raise ValueError('Tin nguồn không hợp lệ; chưa ghi dữ liệu.')
                messages.append(value)
            counts=repo.save_messages(selected,messages,owner)
            repo.log('sync','success',f'Đồng bộ {len(messages)} tin gần nhất; lịch sử tích lũy giữ nguyên.',details=counts)
            return {**counts,'received':len(messages),'history_limit':100,
                    'history_verified':False,'last_success':repo.get_setting('last_sync:'+selected)}

    @app.post('/api/sync')
    def sync():
        return ok(run_sync())

    @app.get('/api/cron/sync')
    def cron():
        cron_secret=env.get('CRON_SECRET','')
        if len(cron_secret)<32 or not secrets.compare_digest(request.headers.get('Authorization',''),'Bearer '+cron_secret):
            return jsonify(success=False,error='Unauthorized'),401
        return ok(run_sync())

    @app.get('/api/messages')
    def messages():
        month=int(request.args.get('month','0'));year=int(request.args.get('year','0'))
        start,end=period(month,year)
        values=repo.messages(room(),start,end)
        return ok({'messages':values,'message_count':len(values),
            'target_month_count':sum(datetime.fromisoformat(m['send_time']).astimezone(TZ).month==month for m in values),
            'history_verified':False})

    @app.post('/api/raw')
    def raw_export():
        data=body();month,year=data.get('month'),data.get('year')
        start,end=period(month,year,raw=True)
        values=repo.messages(room(),start,end)
        if not values:
            raise ValueError('Không có tin nguồn trong kỳ.')
        stream=BytesIO();export_raw_messages(values,stream)
        if stream.getbuffer().nbytes>MAX_FILE:
            raise ValueError('File vượt giới hạn cloud 4 MB; chia kỳ khi xuất.')
        stream.seek(0)
        repo.log('raw_export','success',f'Xuất {len(values)} tin nguồn.')
        return send_file(stream,as_attachment=True,download_name=f'TinNhan_{month:02d}_{year}.xlsx')

    @app.post('/api/sessions')
    def create_session():
        data=body();month,year=data.get('month'),data.get('year')
        start,end=period(month,year)
        if data.get('accept_risk') is not True:
            raise ValueError('Cần chấp nhận bản tạm do chưa xác minh lịch sử đầy đủ.')
        selected=room();snapshot=repo.messages(selected,start,end)
        if not snapshot:
            raise ValueError('Chưa có tin nguồn trong kỳ; đồng bộ trước.')
        ai,_=settings()
        fingerprint=hashlib.sha256(json.dumps({'room':selected,'month':month,'year':year,
            'snapshot':snapshot,'ai':ai,'policy_version':2},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        value=repo.create_session({'session_id':'CLOUD-'+uuid.uuid4().hex[:16],
            'fingerprint':fingerprint,'room_id':selected,'month':month,'year':year,'snapshot':snapshot,'ai_settings':ai})
        return ok({'session_id':value['session_id'],'status':value['status'],'message_count':len(snapshot)})

    @app.get('/api/sessions')
    def sessions():
        return ok([{**row,'error_message':'Phân tích chưa hoàn tất; thử lại hoặc liên hệ quản trị.' if row.get('error_message') else None} for row in repo.sessions()])

    @app.get('/api/sessions/<sid>')
    def session_status(sid):
        value=get_session(sid)
        data={key:value.get(key) for key in ('session_id','month','year','status','snapshot','results','completed')}
        data['error_message']='Phân tích chưa hoàn tất; thử lại hoặc liên hệ quản trị.' if value.get('error_message') else None
        return ok(data)

    @app.post('/api/sessions/<sid>/analyze')
    def analyze(sid):
        with repo.lease('session:'+sid,seconds=180) as owner:
            value=get_session(sid)
            if value['status'] in {'ready','review','exported'}:
                return ok({'status':value['status'],'completed':len(value['completed']),'remaining':0})
            ai,key=settings()
            if ai!=value['ai_settings']:
                raise ValueError('Cấu hình AI đã đổi; tạo phiên mới.')
            pending=[m for m in value['snapshot'] if m['message_id'] not in value['completed']]
            batch=[];size=0
            for message in pending[:10]:
                length=len(json.dumps(message,ensure_ascii=False))
                if length>20000:
                    raise ValueError('Một tin quá dài cho lô AI; xuất tin nguồn để xử lý riêng.')
                if batch and size+length>20000:
                    break
                batch.append(message);size+=length
            try:
                events=value['raw_events'];completed=value['completed']
                if batch:
                    adapter=ai_factory(**ai,api_key=key)
                    adapter.identity_hints=identity_hints(value['snapshot'])
                    adapter.identities=[{k:e.get(k) for k in ('person_id','employee_name','identity_evidence')} for e in events]
                    response=adapter.analyze_attendance(batch,value['month'],value['year'])
                    if not isinstance(response,list) or any(not isinstance(e,dict) for e in response):
                        raise AIResponseError('protocol')
                    events=events+response
                    completed=completed+[m['message_id'] for m in batch]
                remaining=len(value['snapshot'])-len(completed)
                # Preserve a completed provider call even if final validation raises.
                repo.save_analysis(sid,owner,raw_events=events,completed=completed,results=[],status='analyzing')
                results=finalize(events,value['snapshot'],value['month'],value['year'],sid,employee_aliases) if not remaining else []
                status='analyzing' if remaining else ('review' if any(e.get('review_state')=='pending' for e in results) else 'ready')
                repo.save_analysis(sid,owner,raw_events=events,completed=completed,results=results,status=status)
                repo.log('analyze','success',f'Đã xử lý {len(completed)}/{len(value["snapshot"])} tin.',sid)
                return ok({'status':status,'completed':len(completed),'remaining':remaining})
            except (AIHTTPError,AIResponseError) as error:
                repo.save_analysis(sid,owner,raw_events=value['raw_events'],completed=value['completed'],results=value['results'],status='failed',error='Dịch vụ phân tích chưa sẵn sàng.')
                repo.log('analyze','failed','Dịch vụ phân tích chưa sẵn sàng.',sid)
                raise

    @app.post('/api/sessions/<sid>/review')
    def review(sid):
        data=body()
        with repo.lease('session:'+sid) as owner:
            value=get_session(sid)
            if value['status'] not in {'ready','review'}:
                raise ValueError('Phiên chưa hoàn tất phân tích.')
            results=copy.deepcopy(value['results'])
            target=next((e for e in results if e['event_id']==data.get('event_id')),None)
            if not target:
                raise ValueError('Dòng không thuộc phiên.')
            if data.get('exclude') is True:
                target.update(is_excluded=True,review_state='excluded',validation_errors=[],validation_warnings=[])
            else:
                changes=data.get('changes',{})
                if not isinstance(changes,dict) or any(k not in PROPERTIES for k in changes):
                    raise ValueError('Trường sửa không hợp lệ.')
                target.update(changes)
                from src.services.validation import validate
                errors,warnings=validate(target,value['snapshot'],value['month'],value['year'])
                if errors:
                    raise ValueError('\n'.join(errors))
                target.update(validation_errors=[],validation_warnings=warnings,review_state='confirmed',needs_review=False)
            active=[e for e in results if not e.get('is_excluded')]
            validate_set(active,value['snapshot'],value['month'],value['year'])
            for event in active:
                if event['validation_errors']:
                    event['review_state']='pending'
            status='review' if any(e.get('review_state')=='pending' for e in active) else 'ready'
            repo.save_analysis(sid,owner,raw_events=value['raw_events'],completed=value['completed'],results=results,status=status)
            repo.log('review','success','Xác nhận hoặc loại một dòng.',sid,details={'event_id':target['event_id'],'exclude':bool(data.get('exclude')),'changes':data.get('changes',{})})
            return ok({'status':status})

    @app.post('/api/sessions/<sid>/export')
    def export(sid):
        with repo.lease('session:'+sid) as owner:
            value=get_session(sid)
            if value['status'] not in {'ready','review','exported'}:
                raise ValueError('Phiên chưa hoàn tất phân tích.')
            if any(not e.get('is_excluded') and (e.get('validation_errors') or e.get('review_state')=='pending') for e in value['results']):
                raise ValueError('Còn dòng cần kiểm tra. Có thể xuất tin nguồn ngay.')
            start,end=period(value['month'],value['year'])
            latest=repo.messages(value['room_id'],start,end)
            if latest!=value['snapshot']:
                raise ValueError('Tin nguồn đã được thêm hoặc sửa sau snapshot. Tạo bảng mới để xuất đúng dữ liệu hiện tại.')
            stream=BytesIO()
            export_to_excel(value['results'],{**value,'is_draft':True},stream)
            content=stream.getvalue()
            if len(content)>MAX_FILE:
                raise ValueError('File vượt giới hạn cloud 4 MB; cần object storage để xuất file lớn.')
            name=f'Cham_cong_{value["month"]:02d}_{value["year"]}.xlsx'
            repo.save_file(sid,owner,name,content)
            repo.log('export','success','Đã lưu Excel bền vững trong Neon.',sid)
            return ok({'download_url':f'/api/sessions/{sid}/download'})

    @app.get('/api/sessions/<sid>/download')
    def download(sid):
        get_session(sid)
        value=repo.file(sid)
        if not value:
            raise ValueError('Phiên chưa có Excel.')
        content=bytes(value['content'])
        if hashlib.sha256(content).hexdigest()!=value['sha256']:
            raise ValueError('File lịch sử không khớp hash; không tải dữ liệu đã đổi.')
        return send_file(BytesIO(content),as_attachment=True,download_name=value['filename'])

    @app.get('/api/history')
    def history():
        return ok([{**row,'summary':'Tác vụ thất bại; xem giám sát lỗi phía máy chủ.' if row.get('status')=='failed' else row.get('summary')} for row in repo.history()])

    @app.get('/api/operations')
    def operations():
        return ok(repo.error_summary())

    return app
