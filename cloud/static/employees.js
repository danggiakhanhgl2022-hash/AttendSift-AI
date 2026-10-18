'use strict';
(() => {
 const local=!!document.getElementById('sync-section');
 const csrf=document.querySelector('meta[name="csrf-token"]').content;
 const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const api=async(path,data)=>{
  const response=await fetch(path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:data===undefined?undefined:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok||!result.success)throw Error(result.error||'Không lưu được danh sách.');
  return result.data;
 };
 const tab=node('button','Nhân viên');tab.type='button';tab.className='nav-item';tab.dataset.section='employees';
 document.querySelector('nav').append(tab);
 const section=node('section');section.id=local?'employees-section':'employees';section.className='page section';section.hidden=true;
 section.innerHTML='<div class="page-title"><div><h1>Nhân viên</h1><p>Quản lý danh sách chính thức. Người xác định được nhưng không khớp danh sách sẽ được xếp CTV; tên mơ hồ cần kiểm tra.</p></div></div><p id="employeeFeedback" role="status"></p><div class="card"><h2>Thêm / sửa nhân viên</h2><form id="employeeForm"><input id="employeeEditId" type="hidden"><div class="filters"><label>Mã nhân viên (nếu có)<input id="employeeCode" maxlength="100"></label><label>Họ tên chính thức<input id="employeeName" required maxlength="200"></label><label>Chatwork account ID (nếu có)<input id="employeeAccount" inputmode="numeric" maxlength="100"></label><label>Tên thường dùng (mỗi tên một dòng)<textarea id="employeeAliases" rows="3"></textarea></label></div><button type="submit" class="primary">Lưu nhân viên</button><button id="employeeReset" type="button">Nhập người mới</button></form></div><div class="card"><h2>Nhập danh sách riêng</h2><p>Nhập JSON do người quản lý cung cấp hoặc dán mỗi họ tên trên một dòng. Nhập lại không ghi đè chỉnh sửa hay khôi phục người đã ngừng hoạt động. Không đưa danh sách nhân sự lên GitHub.</p><label>File JSON<input id="employeeImportFile" type="file" accept=".json"></label><label>Danh sách họ tên<textarea id="employeeImportText" rows="4"></textarea></label><button id="employeeImport" type="button">Nhập danh sách</button></div><div class="card"><label>Tìm nhân viên<input id="employeeSearch" placeholder="Mã, họ tên, tên thường dùng"></label><p id="employeeCount"></p><div id="employeeRows" class="table-wrap"></div></div>';
 document.querySelector('.workspace').append(section);
 const $=id=>document.getElementById(id);
 let registry={employees:[]};
 function feedback(text,error=false){$('employeeFeedback').textContent=text;$('employeeFeedback').className=error?'error':'success';}
 async function work(fn){try{await fn();}catch(e){feedback(e.message,true);}}
 function render(){
  const key=$('employeeSearch').value.trim().toLocaleLowerCase('vi');
  const rows=registry.employees.filter(p=>[p.full_name,p.employee_code,...p.aliases].join(' ').toLocaleLowerCase('vi').includes(key));
  $('employeeCount').textContent=registry.employees.filter(p=>p.active).length+' nhân viên đang hoạt động · phiên bản danh sách '+registry.revision;
  const table=node('table'),head=node('tr');['Mã','Họ tên','Tên thường dùng','Trạng thái','Thao tác'].forEach(t=>head.append(node('th',t)));table.append(head);
  for(const p of rows){
   const row=node('tr');
   [p.employee_code,p.full_name,p.aliases.join(', ')+' · Chatwork ID: '+(p.chatwork_account_id||'chưa có'),p.active?'Đang hoạt động':'Đã ngừng'].forEach(v=>row.append(node('td',v)));
   const actions=node('td'),edit=node('button','Sửa'),remove=node('button',p.active?'Xóa khỏi danh sách':'Kích hoạt lại');
   edit.type=remove.type='button';
   edit.onclick=()=>{$('employeeEditId').value=p.id;$('employeeName').value=p.full_name;$('employeeCode').value=p.employee_code;$('employeeAccount').value=p.chatwork_account_id;$('employeeAliases').value=p.aliases.join('\n');$('employeeName').focus();};
   remove.onclick=()=>work(async()=>{if(!confirm(p.active?'Ngừng hoạt động nhân viên này? Báo cáo cũ được giữ nguyên.':'Kích hoạt lại nhân viên này?'))return;await api('/api/employees/'+encodeURIComponent(p.id),{active:!p.active});await load();feedback('Đã cập nhật trạng thái.');});
   actions.append(edit,remove);row.append(actions);table.append(row);
  }
  $('employeeRows').replaceChildren(table);
 }
 async function load(){registry=await api('/api/employees');render();return registry;}
 $('employeeForm').onsubmit=e=>{e.preventDefault();work(async()=>{const id=$('employeeEditId').value;await api('/api/employees'+(id?'/'+encodeURIComponent(id):''),{full_name:$('employeeName').value,employee_code:$('employeeCode').value,chatwork_account_id:$('employeeAccount').value,aliases:$('employeeAliases').value.split(/[\n,]/).map(s=>s.trim()).filter(Boolean)});$('employeeForm').reset();$('employeeEditId').value='';await load();feedback('Đã lưu nhân viên. Báo cáo cũ không thay đổi.');});};
 $('employeeReset').onclick=()=>{$('employeeForm').reset();$('employeeEditId').value='';};
 $('employeeSearch').oninput=render;
 $('employeeImport').onclick=()=>work(async()=>{let employees;const file=$('employeeImportFile').files[0];if(file){const value=JSON.parse(await file.text());employees=Array.isArray(value)?value:value.employees;}else employees=$('employeeImportText').value.split('\n').map(s=>s.trim()).filter(Boolean);const result=await api('/api/employees/import',{employees});await load();feedback('Đã thêm '+result.added+' người; không ghi đè thông tin đang có.');});
 async function confirmRoster(){
  const value=await api('/api/employees');
  if(value.employees.some(p=>p.active))return {confirm_empty_roster:false};
  if(!confirm('Danh sách chính thức đang trống. Tiếp tục sẽ xếp người xác định được vào CTV. Bạn có chắc muốn tiếp tục?'))throw Error('Hãy vào tab Nhân viên để nhập danh sách trước.');
  return {confirm_empty_roster:true};
 }
 function reviewInputs(parent,roster,event){
  parent.querySelectorAll('[data-personnel-review]').forEach(n=>n.remove());
  if(!roster)return;
  const block=node('div');block.dataset.personnelReview='true';block.className='card';
  const groupLabel=node('label','Nhóm nhân sự'),group=node('select');group.id='reviewPersonnelGroup';
  for(const [value,text] of [['unresolved','Cần kiểm tra'],['official','Nhân viên chính thức'],['contractor','CTV']]){const o=node('option',text);o.value=value;group.append(o);}
  group.value=event.classification||'unresolved';groupLabel.append(group);
  const personLabel=node('label','Đối chiếu nhân viên bằng mã hoặc Chatwork ID trong danh sách của phiên'),person=node('select');person.id='reviewPersonnelEmployee';
  const empty=node('option','Chọn nhân viên');empty.value='';person.append(empty);
  for(const p of roster.employees.filter(p=>p.active)){const label=p.full_name+' — Mã: '+(p.employee_code||'chưa có')+' — Chatwork ID: '+(p.chatwork_account_id||'chưa có')+' — ID: '+p.id;const o=node('option',label);o.value=p.id;person.append(o);}
  person.value=event.employee_id||'';person.onchange=()=>{if(person.value)group.value='official';};personLabel.append(person);
  const reason=node('p',event.classification_reason||'');reason.className='hint';
  const alias=node('button','Lưu tên trong nguồn làm tên thường dùng');alias.type='button';
  const aliasStatus=node('p');aliasStatus.setAttribute('role','status');
  alias.onclick=async()=>{try{
   const id=person.value;if(!id)throw Error('Chọn nhân viên chính thức trước.');
   const value=await api('/api/employees');const current=value.employees.find(p=>p.id===id&&p.active);
   if(!current)throw Error('Nhân viên không còn hoạt động trong danh sách hiện tại.');
   const name=String(event.source_employee_name||event.identity_evidence||'').trim();
   if(!name)throw Error('Không có tên nguồn để lưu.');
   if(!confirm('Gắn tên thường dùng "'+name+'" với '+current.full_name+'?'))return;
   await api('/api/employees/'+encodeURIComponent(id),{aliases:[...new Set([...current.aliases,name])]});
   aliasStatus.textContent='Đã lưu tên thường dùng cho các phiên mới.';
  }catch(e){aliasStatus.textContent=e.message;}};
  block.append(groupLabel,personLabel,reason,alias,aliasStatus);parent.append(block);
 }
 function reviewChanges(changes){
  if(!$('reviewPersonnelGroup'))return changes;
  return {...changes,classification:$('reviewPersonnelGroup').value,employee_id:$('reviewPersonnelEmployee').value||null};
 }
 window.personnelUI={load,confirmRoster,reviewInputs,reviewChanges};
})();