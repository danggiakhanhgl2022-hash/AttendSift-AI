/* Read-only view of stored results. No requests, payroll writes or AI calls. */
'use strict';
(() => {
    const dashboard=document.getElementById('control-dashboard');if(!dashboard)return;
    const panel=document.createElement('section');panel.className='dash-panel people-summary';panel.id='people-summary';
    panel.innerHTML=`<header><div><span class="panel-code">PEOPLE / ATTENDANCE TOTALS</span><h2>Từ từng tin nhắn, đến tổng của từng người.</h2></div><span class="summary-orbit" aria-hidden="true"></span></header>
      <div class="summary-top"><p id="people-scope">Đang đọc kết quả của phiên gần nhất…</p><span id="people-status">CHỜ DỮ LIỆU</span></div>
      <div class="people-kpis"><article><span>Nhân sự có kết quả</span><strong id="people-count">—</strong><i aria-hidden="true"></i></article><article><span>Tổng OT thực tế · phút</span><strong id="people-ot">—</strong><i aria-hidden="true"></i></article><article><span>Tổng ngày nghỉ</span><strong id="people-leave">—</strong><i aria-hidden="true"></i></article><article><span>Dòng chờ kiểm tra · chưa cộng</span><strong id="people-held">—</strong><i aria-hidden="true"></i></article></div>
      <div class="people-tools"><div class="people-filters" role="group" aria-label="Nhóm nhân sự"><button type="button" data-people-filter="all" aria-pressed="true">Tất cả</button><button type="button" data-people-filter="official" aria-pressed="false">Chính thức</button><button type="button" data-people-filter="contractor" aria-pressed="false">CTV</button></div><label>Tìm người<input id="people-search" type="search" placeholder="Tên hoặc mã nhân sự" autocomplete="off"></label><button type="button" id="people-evidence">Mở phiên để đối chiếu ↗</button></div>
      <div class="people-table-wrap"><table><caption class="people-caption">Tổng theo người · kết quả đã lưu, tách riêng dòng cần kiểm tra</caption><thead><tr><th scope="col">Mã / định danh</th><th scope="col">Họ tên</th><th scope="col">Nhóm</th><th scope="col">Tổng OT (phút)</th><th scope="col">Tổng ngày nghỉ</th><th scope="col">Số sự kiện</th></tr></thead><tbody id="people-rows"></tbody></table></div>
      <footer><span class="people-signal" aria-hidden="true"></span><p id="people-note">Chỉ cộng các dòng đủ điều kiện của phiên; không cộng dồn nhiều tháng. Hiệu ứng ánh sáng minh họa, số liệu chỉ đổi khi kết quả đổi.</p></footer>`;
    dashboard.querySelector('.dash-metrics').after(panel);
    const $=id=>document.getElementById(id),number=new Intl.NumberFormat('vi-VN',{maximumFractionDigits:2});
    const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const numeric=value=>Number.isFinite(Number(value))?Number(value):0;
    const rosterWarning=document.createElement('p');rosterWarning.id='people-roster-warning';rosterWarning.className='people-roster-warning';rosterWarning.hidden=true;panel.querySelector('.summary-top').after(rosterWarning);
    let current=null,filter='official',people=[],held=0;
    let workbook=null,uploaded=false,workbookRequest=0;
    const fileTools=document.createElement('div');fileTools.className='people-file-tools';
    fileTools.innerHTML='<button type="button" id="people-read-file">Đọc file Excel để hiển thị</button><input type="file" id="people-workbook-file" accept=".xlsx" hidden><button type="button" id="people-session-file">Dùng file của phiên đang xem</button>';
    panel.querySelector('.people-tools').after(fileTools);
    const sumField=(items,key)=>items.some(p=>p[key]===null)?'—':number.format(items.reduce((sum,p)=>sum+p[key],0));
    // Same eligibility order as needs_excel_review: fatal errors first, then confirmation.
    function heldForReview(row){
        if(row.validation_errors?.length)return true;
        if(row.review_state==='confirmed'&&row.classification!=='unresolved')return false;
        return row.review_state==='pending'||!!row.validation_warnings?.length||!!row.needs_review||!!row.identity_uncertain||row.classification==='unresolved';
    }
    function project(rows){
        const totals=new Map();held=0;
        for(const row of rows||[]){
            if(row.is_excluded||row.source_only)continue;
            if(heldForReview(row)||!['official','contractor'].includes(row.classification)){held++;continue;}
            const identity=row.person_id||row.employee_name;
            if(!identity){held++;continue;}
            const key=JSON.stringify([row.classification,identity]);
            if(!totals.has(key))totals.set(key,{id:row.person_id||row.employee_code||row.employee_id||'—',name:row.employee_name||'Chưa có tên',classification:row.classification,ot:0,leave:0,count:0});
            const person=totals.get(key);
            person.ot+=['OT','Tăng ca'].includes(row.event_type)?numeric(row.ot_minutes):0;
            person.leave+=numeric(row.leave_days);person.count++;
        }
        return [...totals.values()].sort((a,b)=>a.name.localeCompare(b.name,'vi')||String(a.id).localeCompare(String(b.id)));
    }
    function draw(){
        panel.querySelector('header h2').textContent=filter==='official'?'Chấm công — Nhân viên chính thức':filter==='contractor'?'CTV — Tổng theo từng người':'Tổng hợp nhân sự — tách riêng chính thức và CTV';
        const query=$('people-search').value.trim().toLocaleLowerCase('vi');
        const visible=people.filter(p=>(filter==='all'||p.classification===filter)&&(!query||(p.name+' '+p.id).toLocaleLowerCase('vi').includes(query)));
        const complete=!!workbook||current?.mode==='demo';
        $('people-count').textContent=complete?number.format(visible.length):'—';
        $('people-ot').textContent=complete?sumField(visible,'ot'):'—';
        $('people-leave').textContent=complete?sumField(visible,'leave'):'—';
        $('people-held').textContent=complete?number.format(held):'—';
        const maximum=Math.max(1,...visible.map(p=>p.ot));
        $('people-rows').innerHTML=visible.length?visible.map((p,i)=>`<tr style="--person-delay:-${i%8*.65}s"><td><code>${escape(p.id)}</code></td><th scope="row">${escape(p.name)}</th><td><span class="people-group ${p.classification}">${p.classification==='official'?'Chính thức':'CTV'}</span></td><td class="people-ot-cell"><strong>${p.ot===null?'—':number.format(p.ot)}</strong><span class="people-ot-track" aria-hidden="true"><i style="width:${Math.max(0,p.ot||0)/maximum*100}%"></i></span></td><td class="people-number">${p.leave===null?'—':number.format(p.leave)}</td><td class="people-number">${p.count}</td></tr>`).join(''):`<tr><td colspan="6" class="people-empty">${complete?'Không có người phù hợp với bộ lọc.':'Xuất Excel từ phiên này hoặc chọn file chấm công để hiển thị đúng các sheet.'}</td></tr>`;
        panel.querySelectorAll('[data-people-filter]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.peopleFilter===filter)));
        $('people-evidence').disabled=uploaded||!current?.session||current?.mode!=='live';
    }
    function showWorkbook(value){
        workbook=value;people=value.people||[];held=value.pending||0;rosterWarning.hidden=true;
        $('people-scope').textContent=`Nguồn bảng: ${value.filename} · Chính thức: 2_CHAM_CONG / 3_TONG_KET · CTV: 5_CTV`;
        $('people-status').textContent='HIỂN THỊ TỪ FILE EXCEL';
        $('people-note').textContent=value.missing_cached_values?'Có ô công thức chưa lưu giá trị trong file: hiển thị —, không tự đoán thành 0. Mở và lưu lại bằng Excel rồi chọn lại file.':'Bảng này đọc đúng các sheet của Excel. Không phân loại lại nhân sự, không sửa dữ liệu hay tính lại bảng công.';
        draw();
    }
    async function useSessionFile(){
        const request=++workbookRequest;
        if(uploaded)return;
        workbook=null;people=[];held=0;draw();
        if(current?.mode==='demo'){people=project(current.rows);draw();return;}
        if(!current?.session)return;
        try{
            const response=await fetch('/api/export/'+encodeURIComponent(current.session.session_id)+'/workbook-summary');
            const payload=await response.json();if(request!==workbookRequest||uploaded)return;
            if(!response.ok||payload.success!==true)throw Error(payload.error||'Không đọc được file Excel.');
            if(payload.data.available)showWorkbook(payload.data);
            else{$('people-status').textContent='CHƯA CÓ FILE EXCEL ĐÃ XUẤT';draw();}
        }catch(error){if(request===workbookRequest&&!uploaded){rosterWarning.hidden=false;rosterWarning.textContent=error.message;$('people-status').textContent='CHƯA ĐỌC ĐƯỢC FILE EXCEL';}}
    }
    window.addEventListener('dashboard:summary',event=>{
        current=event.detail;if(uploaded)return;panel.dataset.stale='false';
        const session=current.session,complete=['review','ready','exported'].includes(session?.status);
        $('people-scope').textContent=session?`Phiên đang xem · ${String(session.month).padStart(2,'0')}/${session.year} · ${session.session_id}`:'Chưa có phiên phân tích. Chọn tháng và phân tích trong tab Xuất công.';
        rosterWarning.hidden=true;
        $('people-status').textContent=current.mode==='demo'?'DỮ LIỆU GIẢ LẬP':!complete?'CHỜ PHÂN TÍCH XONG':held?'CÒN DÒNG CẦN KIỂM TRA':'ĐÃ CÓ KẾT QUẢ';
        panel.dataset.review=String(held>0);useSessionFile();
    });
    $('people-read-file').addEventListener('click',()=>$('people-workbook-file').click());
    $('people-workbook-file').addEventListener('change',async()=>{
        const file=$('people-workbook-file').files[0];if(!file)return;
        const request=++workbookRequest,body=new FormData();body.append('file',file);
        $('people-read-file').disabled=true;
        try{
            const response=await fetch('/api/dashboard/workbook-summary',{method:'POST',headers:{'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},body});
            const payload=await response.json();if(request!==workbookRequest)return;
            if(!response.ok||payload.success!==true)throw Error(payload.error||'Không đọc được file.');
            uploaded=true;showWorkbook(payload.data);
        }catch(error){rosterWarning.hidden=false;rosterWarning.textContent=error.message;}
        finally{$('people-read-file').disabled=false;$('people-workbook-file').value='';}
    });
    $('people-session-file').addEventListener('click',()=>{uploaded=false;useSessionFile();});
    window.addEventListener('dashboard:summary-stale',()=>{panel.dataset.stale='true';$('people-status').textContent='CHƯA LÀM MỚI ĐƯỢC · DỮ LIỆU CÓ THỂ CŨ';});
    window.addEventListener('dashboard:summary-fresh',()=>{if(panel.dataset.stale==='true'&&current)window.dispatchEvent(new CustomEvent('dashboard:summary',{detail:current}));});
    panel.addEventListener('click',event=>{const button=event.target.closest('[data-people-filter]');if(button){filter=button.dataset.peopleFilter;draw();}});
    $('people-search').addEventListener('input',draw);
    $('people-evidence').addEventListener('click',()=>document.getElementById('dash-open-evidence')?.click());
    draw();
})();
