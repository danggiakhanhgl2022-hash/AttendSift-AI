"""Snapshot -> AI -> local validation -> review -> atomic, traceable export."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid
from datetime import datetime, timedelta
from datetime import date
from calendar import monthrange
import pytz
from ..adapters.ai_adapters import create_ai_adapter, AIAdapterError, AIResponseError
from ..app.paths import user_downloads_dir
from .validation import validate_set, NUMBERS

Vietnam_TZ = pytz.timezone('Asia/Ho_Chi_Minh')


class ExportServiceError(ValueError):
    pass


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class ExportService:
    def __init__(self, db, config_repo, message_repo, session_repo, action_repo, app_path):
        self.db, self.config_repo, self.message_repo = db, config_repo, message_repo
        self.session_repo, self.action_repo, self.app_path = session_repo, action_repo, app_path
        self.sync_service = None

    def _log(self, sid, kind, status='success', **kwargs):
        self.action_repo.log_event(operation_id=kind.upper()+'-'+uuid.uuid4().hex[:12],
            session_id=sid, action_type=kind, source='ai' if kind=='analyze' else 'user', status=status, **kwargs)

    def _get_date_range(self, month, year):
        if type(month) is not int or type(year) is not int or not 1<=month<=12 or not 2000<=year<=2100:
            raise ExportServiceError('Tháng/năm không hợp lệ (2000–2100).')
        first = datetime(year,month,1)
        previous=first-timedelta(days=1)
        return (Vietnam_TZ.localize(previous.replace(day=15)),
                Vietnam_TZ.localize(datetime(year,month,monthrange(year,month)[1],23,59,59)))

    def _get_messages_for_month(self, room_id, month, year):
        start,end=self._get_date_range(month,year)
        return [m for m in self.message_repo.get_by_room(room_id) if self._is_message_in_date_range(m,start,end)]

    def _is_message_in_date_range(self, message, start, end):
        try:
            dt=datetime.fromisoformat(message['send_time'].replace('Z','+00:00'))
            dt=Vietnam_TZ.localize(dt) if dt.tzinfo is None else dt.astimezone(Vietnam_TZ)
            start=Vietnam_TZ.localize(start) if start.tzinfo is None else start
            end=Vietnam_TZ.localize(end) if end.tzinfo is None else end
            return start<=dt<=end
        except (TypeError,ValueError,KeyError):
            return False

    def _verify_data_risk(self,messages,month,year):
        target=[m for m in messages if self._is_message_in_date_range(m,datetime(year,month,1),datetime(year,month,monthrange(year,month)[1],23,59,59))]
        times=sorted(m['send_time'] for m in messages)
        return {'risk_level':'medium' if messages else 'high', 'risk_message':
            f'Database có {len(messages)} tin trong khoảng ngữ cảnh, gồm {len(target)} tin gửi trong tháng. '
            + (f'Tin đầu: {times[0]}; tin cuối: {times[-1]}. ' if times else '')
            + 'Chưa xác nhận dữ liệu lịch sử đầy đủ. Có thể nhập MessageLog n8n trước khi tạo bảng. Ngày không có tin không đồng nghĩa thiếu dữ liệu.',
            'message_count':len(messages),'target_month_count':len(target),
            'first_message':times[0] if times else None,'last_message':times[-1] if times else None,
            'date_range':dict(zip(['start','end'],[x.isoformat() for x in self._get_date_range(month,year)]))}

    def preflight(self,month,year):
        self._get_date_range(month,year)
        cfg=self.config_repo.get_chatwork_config()
        if not cfg.get('room_id'):
            raise ExportServiceError('Chưa chọn Room Chatwork.')
        sync_error=None
        if self.sync_service:
            try:
                self.sync_service.catch_up('pre_export')
            except ValueError as error:
                sync_error=str(error)
        messages=self._get_messages_for_month(cfg['room_id'],month,year)
        risk=self._verify_data_risk(messages,month,year)
        return {'room_id':cfg['room_id'],'room_name':cfg.get('room_name'),**risk,
                'sync_error':sync_error,'can_continue':bool(messages),'requires_risk_acceptance':True}

    def create_session(self,month,year,accept_risk=False,request_id=None):
        # Recovery and source freshness checks happen before taking the snapshot.
        preflight=self.preflight(month,year)
        if not preflight['can_continue']:
            raise ExportServiceError('Không có tin nhắn trong kỳ. Vui lòng đồng bộ trước.')
        if accept_risk is not True:
            raise ExportServiceError('Cần xác nhận rủi ro thiếu dữ liệu để tạo bản tạm.')
        with self.db.operation_lock:
            cfg=self.config_repo.get_chatwork_config()
            ai=self.config_repo.get_ai_provider()
            if not ai.get('api_key'):
                raise ExportServiceError('Chưa cấu hình AI mặc định.')
            snapshot=self._get_messages_for_month(cfg['room_id'],month,year)
            snapshot=[{k:m.get(k) for k in ['message_id','room_id','account_id','name','body','send_time','content_hash']} for m in snapshot]
            for m in snapshot:
                m['content_hash']=self.db.compute_hash(m['body'])
            fingerprint=hashlib.sha256(encoded(snapshot).encode()).hexdigest()
            request_id=request_id or f'{cfg["room_id"]}:{month}:{year}:{fingerprint}:month-filter-v3:identity-v7-source-verified-annual-text'
            if not isinstance(request_id,str) or len(request_id)>200:
                raise ExportServiceError('Mã yêu cầu không hợp lệ.')
            start,end=self._get_date_range(month,year)
            sid='SES-'+uuid.uuid4().hex[:16].upper()
            settings={k:ai.get(k) for k in ['provider','model','base_url']}
            settings['month_filter_version']=2
            settings['identity_context_version']=5
            with self.db._get_connection() as conn:
                conn.execute('BEGIN IMMEDIATE')
                previous=conn.execute('SELECT session_id,status,month,year,room_id FROM export_sessions WHERE request_id=?',(request_id,)).fetchone()
                if previous:
                    if (previous['month'],previous['year'],previous['room_id'])!=(month,year,cfg['room_id']):
                        raise ExportServiceError('Mã yêu cầu đã được dùng cho kỳ hoặc Room khác.')
                    return {'session_id':previous['session_id'],'status':previous['status'],'existing':True}
                # A repeated click with another request ID still reuses an active identical snapshot.
                previous=conn.execute("SELECT session_id,status,snapshot,ai_settings FROM export_sessions WHERE room_id=? AND month=? AND year=? AND status IN ('prepared','analyzing','ready','review','failed','interrupted') ORDER BY created_at DESC",(cfg['room_id'],month,year)).fetchall()
                for row in previous:
                    if row['snapshot']==encoded(snapshot) and row['ai_settings']==encoded(settings):
                        return {'session_id':row['session_id'],'status':row['status'],'existing':True}
                now=self.db.now_vn()
                settings={k:ai.get(k) for k in ['provider','model','base_url']}
                settings['month_filter_version']=2
                settings['identity_context_version']=5
                conn.execute('INSERT INTO export_sessions(session_id,month,year,status,ai_provider,ai_model,created_at,updated_at,room_id,snapshot,request_id,is_draft,risk_message,period_start,period_end,ai_settings) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (sid,month,year,'prepared',ai['provider'],ai.get('model'),now,now,cfg['room_id'],encoded(snapshot),request_id,1,preflight['risk_message'],start.isoformat(),end.isoformat(),encoded(settings)))
            self._log(sid,'create_session',summary='Tạo snapshot và chấp nhận bản tạm.',details={'month':month,'year':year,'room_id':cfg['room_id'],'message_count':len(snapshot)})
            return {'session_id':sid,'status':'prepared','existing':False,'message_count':len(snapshot),'is_draft':True,'risk_info':preflight}

    def _session(self,sid):
        session=self.session_repo.get_session(sid)
        if not session:
            raise ExportServiceError('Phiên không tồn tại.')
        if not session.get('snapshot'):
            raise ExportServiceError('Phiên cũ thiếu snapshot. Vui lòng tạo lại bảng; lịch sử cũ vẫn được giữ.')
        session['snapshot_data']=json.loads(session['snapshot'])
        return session

    def analyze(self,sid):
        with self.db.operation_lock:
            session=self._session(sid)
            if session['status'] in {'ready','review','exported'}:
                return {'success':True,'existing':True,'status':session['status']}
            if session['status'] not in {'prepared','failed','interrupted'}:
                raise ExportServiceError('Phiên đang xử lý hoặc đã lỗi. Tạo phiên mới để thử lại.')
            self.session_repo.update_session(sid,status='analyzing')
            self._log(sid,'analyze','running',summary='Đang phân tích snapshot bằng AI.')
            try:
                settings=json.loads(session['ai_settings'])
                settings.pop('directories', None)  # Earlier development sessions remain readable.
                settings.pop('month_filter_version', None)
                settings.pop('identity_context_version', None)
                current=self.config_repo.get_ai_provider()
                if current['provider']!=settings['provider']:
                    raise ExportServiceError('AI mặc định đã đổi. Vui lòng tạo phiên mới.')
                adapter=create_ai_adapter(**settings,api_key=current.get('api_key'))
                snapshot=session['snapshot_data']
                from .identity_context import identity_hints
                adapter.identity_hints=identity_hints(snapshot)
                checkpoint=json.loads(session.get('analysis_checkpoint') or '{"events":[],"completed":[]}')
                events=checkpoint['events']
                completed=set(checkpoint['completed'])
                adapter.identities=[{'person_id':e.get('person_id'),'employee_name':e.get('employee_name'),
                                     'identity_evidence':e.get('identity_evidence')} for e in events]
                # Bound input by characters as well as message count; never truncate a message.
                batches=[]; batch=[]; size=0
                for message in snapshot:
                    if message['message_id'] in completed:
                        continue
                    length=len(encoded(message))
                    if length>60000:
                        raise ExportServiceError('Tin nhắn quá dài để xử lý an toàn; cần kiểm tra nguồn.')
                    if batch and (len(batch)>=10 or size+length>20000):
                        batches.append(batch);batch=[];size=0
                    batch.append(message);size+=length
                if batch:batches.append(batch)
                def analyze_batch(batch):
                    try:
                        result=adapter.analyze_attendance(batch,session['month'],session['year'])
                    except AIResponseError as error:
                        if error.code in {'timeout','truncated'} and len(batch)>1:
                            midpoint=len(batch)//2
                            analyze_batch(batch[:midpoint])
                            analyze_batch(batch[midpoint:])
                            return
                        raise
                    if not isinstance(result,list) or any(not isinstance(e,dict) for e in result):
                        raise AIResponseError('protocol')
                    events.extend(result)
                    completed.update(m['message_id'] for m in batch)
                    with self.db._get_connection() as conn:
                        conn.execute('UPDATE export_sessions SET analysis_checkpoint=?,updated_at=? WHERE session_id=?',
                                     (encoded({'events':events,'completed':sorted(completed)}),self.db.now_vn(),sid))
                    adapter.identities=[{'person_id':e.get('person_id'),'employee_name':e.get('employee_name'),
                                         'identity_evidence':e.get('identity_evidence')} for e in events]
                for batch in batches:
                    analyze_batch(batch)
                originals=json.loads(encoded(events))
                from .source_reconciliation import reconcile_explicit_records
                reconcile_explicit_records(events,snapshot,session['month'],session['year'])
                from .identity_context import repair_identity_evidence,align_event_identities
                from .event_policy import mark_information_only, mark_annual_leave_source_only, mark_ctv_source_only, reason_from_source
                for event in events:
                    if not event.get('is_excluded'):
                        repair_identity_evidence(event,snapshot)
                # A model row disproved by a fully parsed group report remains
                # stored for audit, but must not contaminate identity matching
                # or duplicate checks for the verified source-derived rows.
                align_event_identities([e for e in events if not e.get('is_excluded')],snapshot)
                validate_set(events,snapshot,session['month'],session['year'])
                def outside_month(event):
                    try:
                        day=date.fromisoformat(event.get('event_date',''))
                        return (day.month,day.year)!=(session['month'],session['year'])
                    except (TypeError,ValueError):
                        return False  # Unknown/invalid dates must still be reviewed.
                for event in events:
                    # Preserve exclusions already justified by source-level
                    # reconciliation; an in-month date must not resurrect a
                    # disproved AI attribution.
                    event['is_excluded']=bool(event.get('is_excluded') or outside_month(event))
                    mark_information_only(event,snapshot)
                    mark_annual_leave_source_only(event,snapshot)
                    mark_ctv_source_only(event,snapshot)
                    event['reason'] = reason_from_source(event,snapshot)
                    if outside_month(event) and not event.get('source_only'):
                        event.update(is_excluded=True, source_only=True,
                                     review_state='excluded', needs_review=False,
                                     review_reason='Sự kiện ngoài tháng xuất; chỉ lưu tin nguồn làm ngữ cảnh.',
                                     validation_errors=[], validation_warnings=[])
                # Context and informational rows cannot cause identity, duplicate
                # or OT-link errors in the attendance rows kept for this month.
                validate_set([e for e in events if not e.get('is_excluded')],snapshot,session['month'],session['year'])
                with self.db._get_connection() as conn:
                    for index,event in enumerate(events,1):
                        raw=encoded(originals[index-1]) if index <= len(originals) else encoded({'source':'deterministic_reconciliation','derived_from_source':event.get('source_message_ids',[])})
                        payload=encoded(event)
                        errors=event['validation_errors'];warnings=event['validation_warnings']
                        excluded=bool(event.get('is_excluded'))
                        needs=bool(errors or warnings) and not excluded
                        # Persist untrusted output without coercing invalid strings into numbers.
                        number=lambda key: event.get(key,0) if isinstance(event.get(key,0),(int,float)) and not isinstance(event.get(key),bool) else 0
                        ids=event.get('source_message_ids')
                        source_id=ids[0] if isinstance(ids,list) and ids and isinstance(ids[0],str) else ''
                        conn.execute('INSERT INTO ai_results(session_id,event_id,source_id,employee_name,display_name,event_date,event_type,minutes_not_compensated,minutes_compensated,source_message_ids,confidence,needs_review,review_reason,ai_raw_output,created_at,updated_at,person_id,payload,validation_errors,review_state,is_excluded) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                            (sid,f'EVT{index:05d}',source_id,str(event.get('employee_name') or ''),str(event.get('employee_name') or ''),str(event.get('event_date') or ''),str(event.get('event_type') or ''),number('minutes_not_compensated'),number('minutes_compensated'),encoded(event.get('source_message_ids',[])),number('confidence'),int(needs),event.get('review_reason') if excluded else '\n'.join(errors+warnings),raw,self.db.now_vn(),self.db.now_vn(),str(event.get('person_id') or ''),payload,encoded(errors),'excluded' if excluded else ('pending' if needs else 'valid'),int(excluded)))
                    status='review' if any((e['validation_errors'] or e['validation_warnings']) and not e.get('is_excluded') for e in events) else 'ready'
                    conn.execute('UPDATE export_sessions SET status=?,updated_at=?,analysis_checkpoint=NULL,error_message=NULL WHERE session_id=?',(status,self.db.now_vn(),sid))
                self._log(sid,'analyze',summary=f'Phân tích xong {len(events)} sự kiện.')
                return {'success':True,'status':status,'event_count':len(events)}
            except Exception as error:
                self.session_repo.update_session(sid,status='failed')
                from ..adapters.ai_adapters import AIHTTPError
                from ..utils.security import SecretError
                detail = 'Phân tích thất bại; kiểm tra kết nối, model và cấu trúc kết quả.'
                if isinstance(error, AIHTTPError):
                    detail = str(AIHTTPError(error.status))
                elif isinstance(error, AIResponseError):
                    detail = str(AIResponseError(error.code))
                elif isinstance(error, SecretError):
                    detail = 'Không giải mã được khóa trên tài khoản Windows này. Nhập lại API key trong Thiết lập.'
                with self.db._get_connection() as conn:
                    conn.execute('UPDATE export_sessions SET error_message=? WHERE session_id=?', (detail, sid))
                self._log(sid,'analyze','failed',error_message=detail)
                raise ExportServiceError(detail + ' Tạo phiên mới để thử lại.') from None

    def get_results(self,sid,include_excluded=False):
        rows=self.session_repo.get_results(sid,include_excluded)
        for row in rows:
            payload=json.loads(row.get('payload') or '{}')
            for key,value in payload.items():
                if key not in {'result_id','session_id','event_id','ai_raw_output','created_at','updated_at','is_excluded','review_state'}:
                    row[key]=value
            row['validation_errors']=json.loads(row['validation_errors']) if isinstance(row.get('validation_errors'),str) else row.get('validation_errors',[])
        return rows

    def get_results_for_review(self,sid):
        return [r for r in self.get_results(sid) if r.get('review_state')=='pending']

    def review(self,sid,result_id,changes=None,exclude=False):
        with self.db.operation_lock:
            session=self._session(sid)
            if session['status'] not in {'ready','review'}:
                raise ExportServiceError('Phiên không ở trạng thái cho phép kiểm tra.')
            rows=self.get_results(sid,True)
            row=next((r for r in rows if r['result_id']==result_id),None)
            if not row:raise ExportServiceError('Kết quả không thuộc phiên.')
            allowed={'employee_name','person_id','identity_evidence','identity_uncertain','event_date','event_type',
                'event_subtype','reason','hours_compensation','minutes_not_compensated','minutes_compensated',
                'ot_minutes','ot_used_minutes','ot_credit_date','leave_days','start_time','end_time','source_message_ids'}
            changes=changes or {}
            if not isinstance(changes,dict) or set(changes)-allowed:
                raise ExportServiceError('Trường chỉnh sửa không hợp lệ.')
            original=dict(row)
            row.update(changes)
            row['needs_review']=False;row['identity_uncertain']=False
            others=[r for r in rows if r['result_id']!=result_id and not r['is_excluded']]
            validate_set(others+[row],session['snapshot_data'],session['month'],session['year'])
            if row['validation_errors'] and not exclude:
                raise ExportServiceError('\n'.join(row['validation_errors']))
            with self.db._get_connection() as conn:
                for field,value in {**changes,'review_state':'excluded' if exclude else 'confirmed','is_excluded':int(exclude)}.items():
                    before=original.get(field)
                    if before!=value:
                        conn.execute('INSERT INTO corrections(result_id,session_id,field_name,old_value,new_value,corrected_at,correction_type) VALUES(?,?,?,?,?,?,?)',
                            (result_id,sid,field,encoded(before),encoded(value),self.db.now_vn(),'exclude' if exclude else 'review'))
                payload={k:v for k,v in row.items() if k in allowed or k in {'confidence','needs_review','review_reason','validation_errors','validation_warnings'}}
                conn.execute('UPDATE ai_results SET payload=?,employee_name=?,display_name=?,person_id=?,is_excluded=?,needs_review=0,validation_errors=?,review_state=?,updated_at=? WHERE result_id=? AND session_id=?',
                    (encoded(payload),str(row.get('employee_name') or ''),str(row.get('employee_name') or ''),str(row.get('person_id') or ''),int(exclude),encoded(row['validation_errors']),'excluded' if exclude else 'confirmed',self.db.now_vn(),result_id,sid))
            remaining=self.get_results_for_review(sid)
            self.session_repo.update_session(sid,status='review' if remaining else 'ready')
            self._log(sid,'exclude' if exclude else 'confirm',summary=f'{"Loại" if exclude else "Lưu và xác nhận"} kết quả #{result_id}',details={'result_id':result_id})
            return {'success':True,'remaining':len(remaining)}

    def apply_correction(self,result_id,session_id,field_name,old_value,new_value):
        return self.review(session_id,result_id,{field_name:new_value})

    def exclude_result(self,result_id,session_id,reason=None):
        return self.review(session_id,result_id,exclude=True)

    def verify_source_integrity(self,sid):
        session=self._session(sid)
        current=self._get_messages_for_month(session['room_id'],session['month'],session['year'])
        original={m['message_id']:m for m in session['snapshot_data']}
        now={m['message_id']:m for m in current}
        valid=original.keys()==now.keys() and all(
            original[i]['content_hash']==self.db.compute_hash(original[i]['body']) and
            now[i]['content_hash']==self.db.compute_hash(now[i]['body']) and
            all(original[i].get(k)==now[i].get(k) for k in ['body','room_id','name','account_id','send_time']) for i in original)
        return {'valid':valid,'reason':None if valid else 'Tin nguồn đã đổi. Vui lòng tạo lại bảng.'}

    def session_file(self,session):
        outputs=(Path(self.app_path)/'outputs').resolve()
        saved=Path(session.get('file_path') or '')
        # A portable folder may have moved since this session was exported.
        candidates=[saved if saved.is_absolute() else Path(self.app_path)/saved,
                    outputs/'sessions'/session['session_id']/saved.name]
        for candidate in candidates:
            candidate=candidate.resolve()
            if candidate.is_relative_to(outputs) and candidate.is_file():return candidate
        return None

    def export_to_excel(self,sid,overwrite=False):
        with self.db.operation_lock:
            session=self._session(sid)
            if session['status'] not in {'ready','review'}:
                raise ExportServiceError('Phiên chưa sẵn sàng xuất.')
            if not self.verify_source_integrity(sid)['valid']:
                raise ExportServiceError('Tin nguồn đã đổi. Vui lòng tạo lại bảng.')
            results=self.get_results(sid)
            validate_set(results,session['snapshot_data'],session['month'],session['year'])
            if any(r['validation_errors'] or r.get('review_state') not in {'valid','confirmed'} for r in results):
                raise ExportServiceError('Còn dòng chưa hợp lệ hoặc chưa được kiểm tra. Hãy sửa hoặc loại dòng.')
            from ..utils.excel_export import export_to_excel, verify_workbook
            # Publish the user-facing workbook in the logged-in user's Downloads.
            # Keep a separate immutable session archive in the portable data folder
            # so History/Download and interrupted-export recovery still work.
            downloads=user_downloads_dir()
            filename=f'Cham_cong_{session["month"]:02d}_{session["year"]}.xlsx'
            monthly=downloads/filename
            if monthly.exists() and not overwrite:
                raise ExportServiceError('File tháng đã tồn tại trong Downloads. Cần xác nhận ghi đè.')
            outputs=Path(self.app_path)/'outputs'
            archived=outputs/'sessions'/sid/filename;archived.parent.mkdir(parents=True,exist_ok=True)
            pending=archived.with_suffix('.pending.xlsx')
            publish=monthly.with_suffix('.pending.xlsx')
            self.session_repo.update_session(sid,status='exporting',file_path=str(archived))
            try:
                export_to_excel(self.get_results(sid,True),{**session,'snapshot':session['snapshot_data']},str(pending))
                verify_workbook(pending)
                digest=hashlib.sha256(pending.read_bytes()).hexdigest()
                os.replace(pending,archived)
                with self.db._get_connection() as conn:
                    conn.execute('UPDATE export_sessions SET file_hash=? WHERE session_id=?',(digest,sid))
                downloads.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(archived,publish)
                os.replace(publish,monthly)
                self.session_repo.update_session(sid,status='exported',file_path=str(archived))
                self._log(sid,'export',summary='Đã lưu Excel vào Downloads.',file_path=str(monthly),details={'filename':filename,'saved_to':str(monthly),'archive':str(archived),'sha256':digest})
                return {'success':True,'filename':filename,'file_path':str(archived),
                        'saved_to':str(monthly), 'download_url':f'/api/export/{sid}/download',
                        'event_count':len(results),'is_draft':bool(session['is_draft'])}
            except Exception:
                self.session_repo.update_session(sid,status='ready')
                self._log(sid,'export','failed',error_message='Không ghi được Excel trong Downloads. Kiểm tra quyền ghi hoặc file đang mở.')
                raise ExportServiceError('Không lưu được Excel vào Downloads. Đóng file Excel nếu đang mở và kiểm tra quyền ghi thư mục Tải xuống.') from None
            finally:
                for file in [pending,publish]:
                    if file.exists():file.unlink()

    def recover(self):
        recovered=[]
        with self.db.operation_lock, self.db._get_connection() as conn:
            rows=conn.execute("SELECT * FROM export_sessions WHERE status IN ('analyzing','exporting')").fetchall()
            for row in rows:
                status='interrupted'
                if row['status']=='exporting' and row['file_path'] and row['file_hash']:
                    file=self.session_file(dict(row))
                    if file and hashlib.sha256(file.read_bytes()).hexdigest()==row['file_hash']:
                        from ..utils.excel_export import verify_workbook
                        try:verify_workbook(file);status='exported'
                        except ValueError:pass
                conn.execute('UPDATE export_sessions SET status=?,updated_at=? WHERE session_id=?',(status,self.db.now_vn(),row['session_id']))
                recovered.append((row['session_id'],status))
        for sid,status in recovered:
            self._log(sid,'recovery',status,summary='Đối chiếu phiên sau gián đoạn.')
