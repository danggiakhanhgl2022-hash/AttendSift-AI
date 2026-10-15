'use strict';
const $=id=>document.getElementById(id);let sid=null,current=null,selected=null;
const csrf=document.querySelector('meta[name="csrf-token"]').content;
const status=text=>{$('status').textContent=text;$('notice').hidden=!text;};
async function api(path,data){const response=await fetch(path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:data===undefined?undefined:JSON.stringify(data)});if(response.status===401){location.assign('/login');throw Error('Cần đăng nhập.');}const value=await response.json();if(!response.ok||!value.success)throw Error(value.error||'Thao tác thất bại.');return value.data;}
const month=id=>{const [year,month]=$ (id).value.split('-').map(Number);return {month,year};};
function article(parent,title,content){const node=document.createElement('article'),strong=document.createElement('strong'),pre=document.createElement('pre');strong.textContent=title;pre.textContent=content;node.append(strong,pre);parent.append(node);return node;}
function bind(id,action){$(id).addEventListener('click',async()=>{const button=$(id);button.disabled=true;try{await action();}catch(error){status(error.message);}finally{button.disabled=false;}});}
const headerActions=document.createElement('div');headerActions.className='header-actions';
const version=$('appVersion');version.textContent='Bộ phận AI · Đặng Gia Khánh';headerActions.append(version);
const logout=document.createElement('button');logout.id='logout';logout.textContent='Đăng xuất';headerActions.append(logout);document.querySelector('body > .header').append(headerActions);
async function loadConfig(){
 const config=await api('/api/config');
 $('config').textContent=JSON.stringify(config,null,2);
 $('roomName').textContent=config.room.room_name||config.room.room_id||'Chưa chọn nhóm';
 $('chatworkStatus').textContent=config.has_chatwork_key?'Đã kết nối Chatwork.':'Chưa kết nối Chatwork.';
 $('aiStatus').textContent=config.has_ai_key?'Đã kết nối dịch vụ phân tích.':'Chưa kết nối dịch vụ phân tích.';
 $('provider').value=config.ai_provider;
 $('model').value=config.ai_model||'';
 updateProviderAddress();
 return config;
}
function updateProviderAddress(){$('baseUrl').value=({gemini:'https://generativelanguage.googleapis.com/v1beta',openai:'https://api.openai.com/v1',anthropic:'https://api.anthropic.com/v1'})[$('provider').value];}
for(const id of ['chatworkForm','aiForm'])$(id).addEventListener('submit',event=>event.preventDefault());
$('provider').addEventListener('change',()=>{$('model').value='';updateProviderAddress();});
bind('saveAI',async()=>{status('Đang kiểm tra kết nối AI…');await api('/api/config/ai',{provider:$('provider').value,model:$('model').value,api_key:$('aiKey').value});$('aiKey').value='';await loadConfig();status('Đã kiểm tra và lưu kết nối AI.');});
bind('saveChatwork',async()=>{status('Đang kiểm tra Chatwork…');await api('/api/config/chatwork',{api_key:$('chatworkKey').value});$('chatworkKey').value='';await loadConfig();$('roomsButton').click();status('Đã kiểm tra và lưu kết nối Chatwork.');});
document.querySelectorAll('[data-go]').forEach(button=>button.addEventListener('click',()=>document.querySelector('[data-section="'+button.dataset.go+'"]').click()));
document.querySelectorAll('[data-section]').forEach(button=>{button.dataset.tab=button.dataset.section;button.addEventListener('click',()=>{const tab=button.dataset.tab;status('');document.querySelectorAll('[data-section]').forEach(item=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-current',active?'page':'false');});document.body.dataset.page=tab;['sync','export','history','settings'].forEach(id=>{$(id).hidden=id!==tab;$(id).classList.toggle('active',id===tab);});if(tab==='settings')loadConfig().catch(error=>status(error.message));});});
bind('logout',async()=>{await api('/logout',{});location.assign('/login');});
bind('syncButton',async()=>{status('Đang đồng bộ…');const result=await api('/api/sync',{});$('lastSync').textContent=new Date().toLocaleString('vi-VN');status(`Nhận ${result.received} tin; thêm ${result.added}, sửa ${result.updated}, giữ ${result.unchanged}. API trả cửa sổ gần nhất, không xác minh đủ lịch sử.`);});
let cachedMessages=[];
function renderMessages(){const sender=$('messageSender').value.trim().toLocaleLowerCase('vi'),keyword=$('messageKeyword').value.trim().toLocaleLowerCase('vi');const start=$('messageStart').value,end=$('messageEnd').value;const messages=cachedMessages.filter(m=>{const date=new Date(m.send_time);const day=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Bangkok'}).format(date);return (!start||day>=start)&&(!end||day<=end)&&(m.name||'').toLocaleLowerCase('vi').includes(sender)&&(m.body||'').toLocaleLowerCase('vi').includes(keyword);});$('messages').replaceChildren();if(!messages.length){const empty=document.createElement('p');empty.className='empty';empty.textContent='Không có tin nhắn phù hợp.';$('messages').append(empty);return;}const table=document.createElement('table'),head=document.createElement('thead'),tr=document.createElement('tr');for(const title of ['Thời gian','Người gửi','Nội dung gốc']){const th=document.createElement('th');th.textContent=title;tr.append(th);}head.append(tr);table.append(head);const body=document.createElement('tbody');for(const message of messages){const row=document.createElement('tr');for(const [index,value] of [message.send_time,message.name,message.body].entries()){const cell=document.createElement('td');cell.textContent=value;if(index===2)cell.className='message-body';row.append(cell);}body.append(row);}table.append(body);$('messages').append(table);}
bind('messagesButton',async()=>{const data=month('sourceMonth');const result=await api(`/api/messages?month=${data.month}&year=${data.year}`);cachedMessages=result.messages;renderMessages();status(`${result.message_count} tin trong kỳ; ${result.target_month_count} tin gửi trong tháng.`);});
for(const id of ['messageSender','messageKeyword','messageStart','messageEnd'])$(id).addEventListener('input',renderMessages);
async function loadSession(){
 current=await api('/api/sessions/'+sid);
 $('reviewPanel').hidden=false;
 $('step2').classList.add('active');
 $('exportMonth').value=current.year+'-'+String(current.month).padStart(2,'0');
 renderResults();
 $('progress').textContent='Đã xử lý '+current.completed.length+'/'+current.snapshot.length+' tin · '+current.status;
}
function renderResults(){
 const active=current.results.filter(event=>!event.is_excluded);
 const pending=active.filter(event=>event.review_state==='pending'||event.validation_errors?.length);
 $('exportButton').disabled=pending.length>0||!['ready','review','exported'].includes(current.status);
 $('reviewSummary').textContent=active.length+' dòng · '+pending.length+' dòng cần kiểm tra';
 const rows=$('reviewFilter').value==='pending'?pending:active;
 $('results').replaceChildren();
 if(!rows.length){const text=document.createElement('p');text.className='empty';text.textContent=pending.length?'Không có dòng phù hợp.':'Không còn dòng cần kiểm tra. Chọn “Tất cả kết quả” để xem bảng.';$('results').append(text);return;}
 const table=document.createElement('table'),head=document.createElement('thead'),titles=document.createElement('tr');
 for(const title of ['Nhân viên','Ngày','Sự kiện','OT (phút)','Không bù','Trạng thái','']){const th=document.createElement('th');th.textContent=title;titles.append(th);}head.append(titles);table.append(head);
 const body=document.createElement('tbody');
 for(const event of rows){const row=document.createElement('tr');for(const value of [event.employee_name,event.event_date,event.event_type,event.ot_minutes||0,event.minutes_not_compensated||0,event.review_state==='pending'?'Cần kiểm tra':event.review_state==='confirmed'?'Đã xác nhận':'Hợp lệ']){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}const cell=document.createElement('td'),button=document.createElement('button');button.textContent='Xem / sửa';button.addEventListener('click',()=>openReview(event));cell.append(button);row.append(cell);body.append(row);}
 table.append(body);$('results').append(table);
}
$('reviewFilter').addEventListener('change',()=>{if(current)renderResults();});
bind('analyzeButton',async()=>{const value=await api('/api/sessions',{...month('exportMonth'),accept_risk:$('acceptRisk').checked});sid=value.session_id;$('exportButton').disabled=true;let running=true;while(running){status('Đang xử lý từng lô; tiến độ được lưu sau mỗi lô.');const progress=await api(`/api/sessions/${sid}/analyze`,{});$('progress').textContent=`Đã xử lý ${progress.completed}; còn ${progress.remaining} tin`;running=progress.remaining>0;}await loadSession();status('Phân tích xong. Tin ngoài tháng và lịch bên ngoài chỉ giữ trong nguồn.');});
bind('exportButton',async()=>{if(!sid)throw Error('Tạo hoặc mở phiên trước.');const data=await api(`/api/sessions/${sid}/export`,{});$('step3').classList.add('active');$('exportDone').hidden=false;$('exportFilename').textContent='Cham_cong_'+String(current.month).padStart(2,'0')+'_'+current.year+'.xlsx';$('download').href=data.download_url;location.assign(data.download_url);});
bind('rawButton',async()=>{const response=await fetch('/api/raw',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(month('exportMonth'))});if(!response.ok){const data=await response.json();throw Error(data.error||'Xuất tin thất bại.');}const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`TinNhan_${$('exportMonth').value}.xlsx`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status('Đã xuất tin nguồn.');});
function openReview(event){selected=event;$('reviewSources').replaceChildren();for(const message of current.snapshot.filter(m=>event.source_message_ids.includes(m.message_id)))article($('reviewSources'),`${message.name} · ${message.send_time}`,message.body);$('reviewIssues').textContent=[...(event.validation_errors||[]),...(event.validation_warnings||[])].join('\n');const editable={};for(const field of ['person_id','employee_name','identity_evidence','identity_uncertain','event_date','event_type','event_subtype','reason','hours_compensation','minutes_not_compensated','minutes_compensated','ot_minutes','ot_used_minutes','ot_credit_date','leave_days','start_time','end_time','source_message_ids','confidence','needs_review','review_reason'])editable[field]=event[field]??null;$('reviewJson').value=JSON.stringify(editable,null,2);renderReviewFields(editable);$('reviewDialog').showModal();}
bind('confirmReview',async()=>{await api(`/api/sessions/${sid}/review`,{event_id:selected.event_id,changes:reviewChanges()});$('reviewDialog').close();await loadSession();status('Đã lưu xác nhận.');});
bind('excludeReview',async()=>{await api(`/api/sessions/${sid}/review`,{event_id:selected.event_id,exclude:true});$('reviewDialog').close();await loadSession();status('Chỉ giữ tin nguồn cho dòng này.');});
$('closeReview').addEventListener('click',()=>$('reviewDialog').close());
let savedSessions=[],savedActions=[];
function renderHistory(){
 const start=$('historyStart').value,end=$('historyEnd').value,kind=$('historyType').value,outcome=$('historyStatus').value;
 const inRange=item=>{const day=(item.created_at||'').slice(0,10);return (!start||day>=start)&&(!end||day<=end);};
 $('sessions').replaceChildren();$('actions').replaceChildren();
 for(const item of savedSessions.filter(inRange)){
  const row=article($('sessions'),item.month+'/'+item.year+' · '+item.status,item.error_message||item.session_id),button=document.createElement('button');
  button.textContent='Mở phiên';button.addEventListener('click',async()=>{sid=item.session_id;try{await loadSession();document.querySelector('[data-tab="export"]').click();}catch(error){status(error.message);}});row.append(button);
  if(item.status==='exported'){const link=document.createElement('a');link.textContent='Tải Excel';link.href='/api/sessions/'+item.session_id+'/download';row.append(link);}
 }
 for(const item of savedActions.filter(item=>inRange(item)&&(!kind||item.kind===kind)&&(!outcome||item.status===outcome)))article($('actions'),item.created_at+' · '+item.kind+' · '+item.status,item.summary);
 for(const id of ['sessions','actions'])if(!$(id).children.length){const empty=document.createElement('p');empty.className='empty';empty.textContent='Chưa có dữ liệu phù hợp.';$(id).append(empty);}
}
bind('historyButton',async()=>{[savedSessions,savedActions]=await Promise.all([api('/api/sessions'),api('/api/history')]);renderHistory();});
bind('filterHistory',async()=>{renderHistory();});
bind('roomsButton',async()=>{const rooms=await api('/api/rooms');$('rooms').replaceChildren();rooms.forEach(room=>{const option=document.createElement('option');option.value=String(room.room_id);option.textContent=room.name;$('rooms').append(option);});});
bind('roomButton',async()=>{await api('/api/room',{room_id:$('rooms').value});await loadConfig();status('Đã lưu phòng cloud.');});
const today=new Date();const initial=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}`;$('sourceMonth').value=initial;$('exportMonth').value=initial;

const reviewSpec=[['employee_name','Họ tên','text'],['event_date','Ngày sự kiện','date'],['event_type','Loại sự kiện','text'],['ot_minutes','Số phút OT','number'],['minutes_not_compensated','Phút không bù','number'],['minutes_compensated','Phút đã bù','number'],['leave_days','Số ngày nghỉ','number'],['ot_used_minutes','Phút tăng ca dùng nghỉ bù','number'],['ot_credit_date','Ngày dùng tăng ca nghỉ bù','date'],['identity_evidence','Bằng chứng tên trong tin nguồn','text'],['start_time','Giờ bắt đầu','time'],['end_time','Giờ kết thúc','time'],['reason','Lý do','text']];
function renderReviewFields(values){$('reviewFields').replaceChildren();for(const [key,title,type] of reviewSpec){const label=document.createElement('label');label.textContent=title;const input=document.createElement('input');input.id='review-'+key;input.type=type;if(type==='number'){input.min='0';input.step='any';}input.value=values[key]??'';input.addEventListener('input',()=>{try{const changes=JSON.parse($('reviewJson').value);changes[key]=type==='number'?(input.value===''?null:Number(input.value)):input.value;$('reviewJson').value=JSON.stringify(changes,null,2);}catch(error){status('JSON chưa hợp lệ; sửa dữ liệu bổ sung trước.');}});label.append(input);$('reviewFields').append(label);}}
function reviewChanges(){return JSON.parse($('reviewJson').value);}
loadConfig().catch(error=>status(error.message));
