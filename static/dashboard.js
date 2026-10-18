/* Read-only dashboard. Existing forms, mutation endpoints and payroll logic are untouched. */
'use strict';
(() => {
    const nav = document.querySelector('body > .nav');
    const workspace = document.querySelector('.container');
    const brain = document.querySelector('.intro');
    if (!nav || !workspace || !brain) return;
    const root = document.createElement('main');
    root.id = 'control-dashboard'; root.className = 'control-dashboard';
    root.setAttribute('aria-label', 'Tổng quan dữ liệu chấm công');
    root.innerHTML = `
      <div class="dash-topline"><div><span class="dash-kicker">ATTENDSIFT / OPERATIONS CONSOLE</span><h1>Trung tâm dữ liệu chấm công<span class="console-cursor">_</span></h1><p>Từ tin nguồn đến kết quả có thể đối chiếu.</p></div>
      <div class="dash-toolbar"><span id="dash-clock"></span><label>Nguồn<select id="dash-source"><option value="live">Dữ liệu ứng dụng</option><option value="demo">Trình diễn giả lập</option></select></label><label>Hiệu ứng<select id="dash-motion"><option value="auto">Tự động / Tự chạy</option><option value="system">Theo hệ thống</option><option value="light">Nhẹ</option><option value="strong">Mạnh</option><option value="off">Tắt</option></select></label><button type="button" id="dash-refresh">↻ Làm mới</button></div></div>
      <div class="dash-statusbar"><span id="dash-source-badge">DỮ LIỆU ỨNG DỤNG</span><span id="dash-connection">Đang đọc dữ liệu…</span><span id="dash-updated">Chưa cập nhật</span><span class="dash-status-right">Đọc dữ liệu mỗi 15 giây khi mở tổng quan</span></div>
      <section class="dash-panel interpretation-panel" aria-labelledby="dash-interpretation-title"><header><div><span class="panel-code">EVIDENCE / RESULT EXPLANATION</span><h2 id="dash-interpretation-title">Diễn giải từ thông tin của bạn</h2></div><span id="dash-explanation-source">ĐANG ĐỌC DỮ LIỆU</span></header><p id="dash-narrative" class="dash-narrative">Đang đọc tin nguồn và kết quả đã lưu…</p><div class="explanation-toolbar"><label>Bản ghi<select id="dash-explain-row" aria-label="Chọn bản ghi để diễn giải"><option>Chưa có kết quả</option></select></label><label class="explanation-auto"><input type="checkbox" id="dash-follow" checked> Tự động đi qua các bước</label><button type="button" data-dashboard-go="settings">Kết nối dữ liệu của tôi</button><button type="button" data-dashboard-go="export">Phân tích bằng quy trình hiện có</button><button type="button" id="dash-open-evidence" disabled>Mở phiên đã lưu</button></div><div id="dash-explanation-steps" class="explanation-steps"></div><p id="dash-explanation-note" class="chart-scope">Chỉ diễn giải kết quả và bằng chứng đã lưu; không tự xác nhận hay đổi số công.</p></section>
      <div class="dash-metrics">
        <article class="dash-panel metric-main"><span class="panel-code">01 / SOURCE MESSAGES</span><span class="metric-label">Tin nhắn đã lưu</span><strong data-metric="messages">—</strong><svg class="metric-spark" viewBox="0 0 240 44" aria-hidden="true"></svg><small>Toàn bộ tin đã lưu của phòng đang chọn</small></article>
        <article class="dash-panel"><span class="panel-code">02 / EMPLOYEE REGISTRY</span><span class="metric-label">Nhân viên hoạt động</span><strong data-metric="employees">—</strong><div class="metric-bars" aria-hidden="true"></div><small>Danh sách nhân viên chính thức</small></article>
        <article class="dash-panel"><span class="panel-code">03 / LATEST SESSION</span><span class="metric-label">Sự kiện trích xuất</span><strong data-metric="events">—</strong><div class="metric-bars" aria-hidden="true"></div><small class="dash-session-label">Chưa có phiên phân tích</small></article>
        <article class="dash-panel metric-warning"><span class="panel-code">04 / HUMAN REVIEW</span><span class="metric-label">Dòng cần kiểm tra</span><strong data-metric="pending">—</strong><div class="metric-bars" aria-hidden="true"></div><small>Phiên gần nhất · chưa được xác nhận</small></article>
      </div>
      <div class="dash-upper">
        <article class="dash-panel"><header><h2>Mật độ tin nhắn</h2><span>NGÀY GỬI</span></header><div id="dash-message-chart" class="dash-chart" role="img" aria-label="Số tin theo ngày gửi"></div><p id="dash-message-scope" class="chart-scope"></p></article>
        <article class="dash-panel"><header><h2>Trạng thái phiên</h2><span>WORKFLOW</span></header><div id="dash-session-chart" class="session-breakdown"></div><p class="chart-scope">Tối đa 100 phiên gần nhất, mọi phòng · không cộng dồn số công</p></article>
        <article class="dash-panel"><header><h2>Hoạt động hệ thống</h2><span>7 NGÀY</span></header><div class="health-metrics"><div><strong id="dash-success">—</strong><span>Thành công</span></div><div><strong id="dash-failed">—</strong><span>Thất bại</span></div><div><strong id="dash-syncs">—</strong><span>Đồng bộ</span></div></div><div id="dash-activity-chart" class="dash-chart compact-chart" role="img" aria-label="20 hoạt động gần nhất theo ngày"></div><p class="chart-scope">Đường biểu diễn từ tối đa 20 hoạt động gần nhất trong 7 ngày</p></article>
      </div>
      <article class="dash-panel neural-panel"><header><div><span class="panel-code">NEURAL DATA FLOW / ARCHITECTURE VISUALIZATION</span><h2>Luồng thông tin hội tụ</h2></div><span id="dash-flow-mode">CHUYỂN ĐỘNG MINH HỌA</span></header><div class="neural-layout"><svg class="neural-wiring" viewBox="0 0 1000 400" preserveAspectRatio="none" aria-hidden="true"><path d="M170 75 C320 75 300 200 430 200"/><path d="M170 200 H430"/><path d="M170 325 C320 325 300 200 430 200"/><path d="M830 75 C680 75 700 200 570 200"/><path class="review-wire" d="M830 200 H570"/><path d="M830 325 C680 325 700 200 570 200"/></svg><div class="flow-column" id="dash-inputs"></div><div id="dash-brain-slot"></div><div class="flow-column flow-output" id="dash-outputs"></div></div><footer class="neural-footer"><span><i></i> Tin nguồn</span><span><i></i> Đối chiếu</span><span><i></i> Cần xác nhận</span><small>Khối 3D và đường truyền minh họa kiến trúc; các bộ đếm lấy theo nguồn đã chọn.</small></footer></article>
      <div class="dash-bottom">
        <article class="dash-panel"><header><h2>Phân nhóm kết quả</h2><span>PHIÊN GẦN NHẤT</span></header><div id="dash-class-chart" class="class-chart"></div><p class="chart-scope">Chính thức / CTV / chưa xác định · số dòng, không phải giờ công</p></article>
        <article class="dash-panel"><header><h2>Phân bố sự kiện</h2><span>SỐ DÒNG</span></header><div id="dash-event-chart" class="dash-chart" role="img" aria-label="Phân bố loại sự kiện trong phiên"></div><p class="chart-scope">Thống kê bản ghi trích xuất; bao gồm dòng đang cần kiểm tra</p></article>
        <article class="dash-panel"><header><h2>Nhật ký dữ liệu</h2><span>GẦN NHẤT</span></header><ol id="dash-log" class="dash-log"></ol></article>
      </div>
      <footer class="dashboard-footer"><span id="dash-room">Chưa chọn phòng Chatwork</span><span id="dash-latest-scope">Phiên phân tích gần nhất: mọi phòng</span><span>Không thay đổi cách tính công hay quy tắc xác nhận</span></footer>`;
    workspace.before(root);
    root.querySelector('.neural-panel').after(root.querySelector('.interpretation-panel'));
    const liveSummary=document.createElement('div');liveSummary.className='dash-live-summary';liveSummary.id='dash-live-summary';
    root.querySelector('.dash-statusbar').after(liveSummary);
    root.querySelector('#dash-brain-slot').append(brain);
    const overview = document.createElement('button'); overview.type = 'button';
    overview.className = 'nav-item active'; overview.textContent = 'Tổng quan'; overview.id = 'dashboard-nav';
    nav.prepend(overview);
    const byId = id => root.querySelector('#' + id);
    const sessionLabel=document.createElement('label');sessionLabel.innerHTML='Phiên<select id="dash-session" aria-label="Phiên dùng để tổng hợp"><option value="latest">Phiên mới nhất</option></select>';
    root.querySelector('.dash-toolbar').prepend(sessionLabel);
    const nf = new Intl.NumberFormat('vi-VN');
    const escaped = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const finite = value => Number.isFinite(Number(value)) ? Math.max(0, Number(value)) : 0;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    let mode = 'live', active = true, loading = false, stopped = false, controller;
    let sessionChoice='latest';
    let data = null, intensity = 'auto', frameId = 0, drawTime = 0, lastFrame = 0, disposed = false;
    let dataTransition = 0, clockTimer, pollTimer, demoTimer;
    let explanationIndex = 0, explanationPhase = -1, explanationHeld = false, explanationChangedAt = 0;
    let explanationRows = [], explanationSnapshot = [], explanationKey = '';
    const processPanel=document.createElement('section');processPanel.className='process-stream';
    processPanel.innerHTML='<article><span>01 / SNAPSHOT CHATWORK</span><p id="process-source"></p></article><article class="process-core"><span>02 / AI ENGINE</span><strong id="process-state" role="status"></strong><small id="process-detail"></small></article><article><span>03 / KẾT QUẢ ĐÃ LƯU</span><p id="process-result"></p></article>';
    root.querySelector('.neural-layout').after(processPanel);
    const coreStatus=document.createElement('div');coreStatus.className='brain-process-label';
    byId('dash-brain-slot').append(coreStatus);
    let processTick=-1;
    function renderProcess() {
        if(!data)return;
        const status=data.latest?.status||'idle', complete=sessionIsComplete(data.latest);
        root.dataset.process=status;
        byId('process-state').textContent=({analyzing:'AI đang phân tích',prepared:'Chờ phân tích',review:'Phân tích xong · cần kiểm tra',ready:'Phân tích thành công',exported:'Đã xuất Excel',failed:'Phân tích thất bại',interrupted:'Phân tích gián đoạn'})[status]||'Chờ phiên phân tích';
        coreStatus.textContent=byId('process-state').textContent;
        byId('process-detail').textContent=status==='analyzing'?'Đang chờ kết quả từ dịch vụ AI · không ước lượng %':complete?'Kết quả từ phiên '+data.latest.session_id:'Theo dõi trạng thái phiên đã lưu';
        const index=Math.floor(drawTime/4), sources=data.snapshot||[], results=(data.rows||[]).filter(r=>!r.is_excluded);
        const source=sources[index%Math.max(1,sources.length)], result=results[index%Math.max(1,results.length)];
        byId('process-source').textContent=source?String(source.message_id)+' · '+String(source.body||'Không có nội dung').slice(0,280):'Chưa có snapshot của phiên. Không dùng tin phòng khác thay thế.';
        byId('process-result').textContent=complete?(result?`${result.employee_name||'Chưa xác định'} · ${result.event_type||'Chưa xác định'} · ${result.event_date||'Chưa rõ ngày'} · ${isPending(result)?'Cần kiểm tra':'Đã lưu kết quả'}`:'Phiên đã hoàn tất, không có sự kiện được tính.'):'Chưa có kết quả hoàn tất · không hiển thị kết quả phiên cũ';
        processTick=index;
        window.dispatchEvent(new CustomEvent('dashboard:process',{detail:{status,complete,hasSources:sources.length>0}}));
    }
    const metricValues = new Map();
    const metricAnimations = new Map();
    const stateNames = { prepared:'Chưa phân tích', analyzing:'Đang phân tích', review:'Cần kiểm tra', ready:'Sẵn sàng', exported:'Đã xuất', failed:'Thất bại', interrupted:'Gián đoạn' };
    const activityNames = {sync:'Đồng bộ',export:'Xuất Excel',analyze:'Phân tích',create_session:'Tạo phiên',confirm:'Xác nhận',exclude:'Loại dòng'};
    function visibleDashboard() { return active && !document.hidden && !disposed; }
    function motionLevel() {
        if (stopped || intensity === 'off' || (document.documentElement.dataset.motionPolicy !== 'full' && reduced.matches)) return 0;
        if (intensity === 'light') return .35;
        if (intensity === 'strong') return 1;
        const busy = data?.sessions.some(s => s.status === 'analyzing');
        return busy ? 1 : Math.min(.95, .72 + Math.log2((data?.sync.message_count || 0) + 1) / 40);
    }
    function setMotion() {
        const level = motionLevel(); root.dataset.motion = level ? 'running' : 'paused';
        root.style.setProperty('--dash-energy', String(level));
        root.style.setProperty('--dash-speed', `${Math.round(6 - level * 3)}s`);
        window.dispatchEvent(new CustomEvent('dashboard:motion', {detail:{level, stopped:level === 0}}));
        if (!level) { cancelAnimationFrame(frameId); frameId = 0; }
        else requestDraw();
    }
    function openOverview() {
        active = true; root.hidden = false; workspace.hidden = true;
        nav.querySelectorAll('.nav-item').forEach(b => { b.classList.toggle('active', b === overview); b.setAttribute('aria-current', b === overview ? 'page' : 'false'); });
        setMotion(); refresh();
    }
    overview.addEventListener('click', openOverview);
    nav.addEventListener('click', event => {
        const button = event.target.closest('[data-section]'); if (!button) return;
        active = false; root.hidden = true; workspace.hidden = false; overview.classList.remove('active');
        overview.setAttribute('aria-current','false'); cancelAnimationFrame(frameId); frameId = 0;
    });
    function countTo(node, value) {
        value = finite(value); const old = metricValues.get(node);
        if (old === value) return;
        cancelAnimationFrame(metricAnimations.get(node)); metricValues.set(node, value);
        node.dataset.value = String(value);
        if (!motionLevel() || old === undefined || !visibleDashboard()) { node.textContent = nf.format(value); return; }
        const start = performance.now();
        const animate = now => {
            const p = Math.min(1, (now - start) / 800), ease = 1 - (1 - p) ** 3;
            node.textContent = nf.format(Math.round(old + (value - old) * ease));
            if (p < 1 && visibleDashboard() && motionLevel()) metricAnimations.set(node,requestAnimationFrame(animate));
            else node.textContent = nf.format(value);
        }; metricAnimations.set(node,requestAnimationFrame(animate));
    }
    async function get(url, signal) {
        const response = await fetch(url,{signal,headers:{'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content}});
        if (!response.ok) throw Error('Chưa đọc được dữ liệu ứng dụng (' + response.status + ')');
        const value = await response.json(); if (value.success === false) throw Error(value.error || 'Chưa đọc được dữ liệu');
        return value.data;
    }
    const sessionIsComplete = s => ['review','ready','exported'].includes(s?.status);
    function isPending(r) { return r.review_state === 'pending' || !!r.needs_review || !!r.validation_errors?.length; }
    async function loadLive(signal) {
        const [sync, employeeRegistry, history, sessions] = await Promise.all([
            get('/api/sync/status',signal),get('/api/employees',signal),get('/api/history/dashboard',signal),get('/api/export?limit=100',signal)
        ]);
        const messages = sync.room_id ? await get('/api/sync/messages?limit=500',signal) : [];
        let latest = sessionChoice!=='auto'&&sessionChoice!=='latest'?sessions.find(s=>s.session_id===sessionChoice)||null:sessions[0]||null;
        // Do not mix old sessions with the one currently being prepared or analyzed.
        let rows = null, snapshot = [],rosterActive=null,skippedSession=null;
        if (latest) {
            const detailFor=s=>get('/api/export/'+encodeURIComponent(s.session_id),signal);
            const rosterCount=detail=>{
                let settings=detail.ai_settings;if(typeof settings==='string'){try{settings=JSON.parse(settings);}catch{return null;}}
                return Array.isArray(settings?.employee_registry?.employees)?settings.employee_registry.employees.filter(e=>e.active).length:null;
            };
            let detail=await detailFor(latest);rosterActive=rosterCount(detail);
            rows=sessionIsComplete(latest)?await get('/api/export/'+encodeURIComponent(latest.session_id)+'/results',signal):null;
            snapshot = Array.isArray(detail.snapshot) ? detail.snapshot : [];
        }
        return {sync, employees:employeeRegistry.employees || [],history,sessions,messages,latest,rows,snapshot,rosterActive,skippedSession};
    }
    let demoTick = 0;
    function demoData() {
        const now = new Date(), day = now.toLocaleDateString('en-CA',{timeZone:'Asia/Ho_Chi_Minh'});
        const messages = Array.from({length:180 + demoTick % 20}, (_,i) => ({send_time:new Date(now - ((i*i+7*i) % 14) * 86400000).toISOString()}));
        const types = ['Tăng ca','Tăng ca','Tăng ca','Đi trễ','Về sớm','Nghỉ','Làm bù'];
        const rows = Array.from({length:86 + demoTick % 7},(_,i)=>({event_id:'DEMO-E'+i,employee_name:i%11===0?'Quân':'Nhân viên Demo '+(i+1),source_message_ids:['DEMO-S'+i],event_type:types[i % types.length],classification:i % 11 === 0 ? 'unresolved' : i % 7 === 0 ? 'contractor' : 'official',review_state:i % 11 === 0 ? 'pending' : 'confirmed',review_reason:i%11===0?'Tên Quân chưa xác định được duy nhất một nhân viên.':'',event_date:day,ot_minutes:types[i%types.length]==='Tăng ca'?120:0,reason:'Nội dung minh họa, không phải dữ liệu người dùng.'}));
        const snapshot=rows.map((row,i)=>({message_id:'DEMO-S'+i,name:'Người báo cáo Demo',send_time:now.toISOString(),body:`Ngày ${day}: ${row.employee_name} báo ${row.event_type}${row.ot_minutes?' 2h':''}. Tin giả lập.`}));
        const sessions = ['exported','review','ready','exported','prepared','failed','exported'].map((status,i)=>({status,session_id:'DEMO-'+i,month:now.getMonth()+1,year:now.getFullYear()}));
        const events = Array.from({length:20},(_,i)=>({action_time:new Date(now - Math.pow(i,1.2) * 4 * 3600000).toISOString(),action_type:['sync','analyze','export'][i % 3],status:i % 9 === 0 ? 'failed' : 'success'}));
        return {sync:{message_count:1248 + demoTick,room_id:'demo',room_name:'Phòng minh họa — dữ liệu giả lập',last_successful_sync:now.toISOString()},employees:Array.from({length:32},()=>({active:true})),history:{success_count:56 + demoTick,failed_count:2,sync_count:14,recent_events:events},sessions,messages,latest:sessions[0],rows,snapshot};
    }
    async function refresh() {
        if (loading || !visibleDashboard()) return;
        loading = true; byId('dash-refresh').disabled = true;
        controller = new AbortController(); const currentMode = mode,currentSession=sessionChoice;
        const timeout = setTimeout(() => controller?.abort(),12000);
        try {
            const next = mode === 'demo' ? demoData() : await loadLive(controller.signal);
            if (mode !== currentMode || currentSession!==sessionChoice || disposed) return;
            const changed = JSON.stringify(data) !== JSON.stringify(next); data = next;
            if (changed) dataTransition = performance.now();
            // Polling identical data must not recreate SVGs and restart their animation clocks.
            if (changed) renderData();
            byId('dash-connection').textContent = mode === 'demo' ? 'TRÌNH DIỄN · KHÔNG PHẢI SỐ LIỆU THẬT' : 'Đã đọc dữ liệu lưu trong ứng dụng';
            byId('dash-updated').textContent = 'Cập nhật ' + new Date().toLocaleTimeString('vi-VN');
            root.dataset.error = 'false'; setMotion();
            window.dispatchEvent(new CustomEvent('dashboard:summary-fresh'));
        } catch (error) {
            if (mode === currentMode && !disposed) {
                byId('dash-connection').textContent = 'Chưa làm mới được · số đang hiển thị có thể đã cũ'; root.dataset.error = 'true';
                window.dispatchEvent(new CustomEvent('dashboard:summary-stale'));
                byId('dash-connection').title = error.name === 'AbortError' ? 'Quá thời gian đọc dữ liệu' : error.message;
            }
        } finally { clearTimeout(timeout);loading = false;byId('dash-refresh').disabled = false;if(mode!==currentMode)refresh(); }
    }
    function group(items, field) {
        const counts = new Map();
        for (const item of items) {
            let value = String(item[field] || 'Chưa rõ');
            if (field.endsWith('time')) {
                const date = new Date(value); if (Number.isNaN(date.getTime())) continue;
                value = date.toLocaleDateString('en-CA',{timeZone:'Asia/Ho_Chi_Minh'});
            }
            counts.set(value, (counts.get(value) || 0) + 1);
        }
        return [...counts].sort((a,b) => a[0].localeCompare(b[0]));
    }
    function svgLine(items, color = '#66e6ce', bars = false) {
        if (!items.length) return '<p class="dash-empty">Chưa có dữ liệu để biểu diễn</p>';
        const width=600,height=138,pad=14,max=Math.max(1,...items.map(x=>finite(x[1])));
        const coords=items.map((item,i)=>[pad+i*(width-pad*2)/Math.max(1,items.length-1),height-pad-(finite(item[1])/max)*(height-pad*2)]);
        const d=coords.map((p,i)=>(i?'L':'M')+p.join(',')).join(' ');
        const shapes=bars ? coords.map((p,i)=>`<rect x="${p[0]-Math.min(16,240/items.length)}" y="${p[1]}" width="${Math.min(32,480/items.length)}" height="${height-pad-p[1]}" rx="2" fill="${color}"><title>${escaped(items[i][0])}: ${items[i][1]}</title></rect>`).join('') : `<path class="chart-area" d="${d} L${width-pad},${height-pad} L${pad},${height-pad}Z" fill="${color}" fill-opacity=".09"/><path class="chart-data-line" d="${d}" fill="none" stroke="${color}" stroke-width="2.5" vector-effect="non-scaling-stroke"/>${coords.map((p,i)=>`<circle cx="${p[0]}" cy="${p[1]}" r="3" fill="${color}"><title>${escaped(items[i][0])}: ${items[i][1]}</title></circle>`).join('')}`;
        return `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">${[.25,.5,.75,1].map(n=>`<path d="M0,${Math.round(n*(height-pad))} H600" stroke="#203343" stroke-width="1"/>`).join('')}${shapes}${!bars&&items.length>1?`<path class="chart-tracer" d="${d}" fill="none" stroke="${color}" stroke-width="4" pathLength="100" vector-effect="non-scaling-stroke"/>`:""}<path class="chart-scan" d="M0,0 V138" stroke="${color}" stroke-opacity=".45"/></svg><div class="chart-axis"><span>${escaped(items[0][0])}</span><span>Đỉnh ${nf.format(max)} bản ghi</span><span>${escaped(items.at(-1)[0])}</span></div>`;
    }
    function flowCard(title, value, caption, index) { return `<div class="flow-channel" style="--flow-delay:${index*.4}s"><span class="flow-port"></span><div><span>${escaped(title)}</span><strong>${escaped(value)}</strong><small>${escaped(caption)}</small></div><svg viewBox="0 0 80 20" aria-hidden="true"><path d="M0 10H28L40 2L52 10H80"/><circle class="flow-dot" r="3" cx="0" cy="10"/></svg></div>`; }
    function readableDate(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? String(value || 'Chưa có ngày') : date.toLocaleString('vi-VN'); }
    function renderInterpretation() {
        const previousKey=explanationKey;
        explanationRows=(data.rows||[]).filter(r=>!r.is_excluded&&!r.source_only);
        explanationSnapshot=data.snapshot||[];
        const select=byId('dash-explain-row');select.replaceChildren();
        explanationRows.forEach((row,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=`${row.display_name||row.employee_name||'Chưa rõ người'} · ${row.event_date||'Chưa rõ ngày'} · ${row.event_type||'Chưa rõ loại'}`;select.append(option);});
        const restored=explanationRows.findIndex(r=>String(r.event_id||r.result_id)===previousKey);
        explanationIndex=restored>=0?restored:Math.min(explanationIndex,Math.max(0,explanationRows.length-1));
        if(!explanationRows.length){const option=document.createElement('option');option.textContent='Chưa có kết quả để diễn giải';select.append(option);select.disabled=true;}else{select.disabled=false;select.value=String(explanationIndex);}
        const pending=explanationRows.filter(isPending).length;
        const sessionLabel=data.latest?`${String(data.latest.month).padStart(2,'0')}/${data.latest.year}`:'';
        const prefix=mode==='demo'?'Minh họa giả lập. ':'';
        let narrative;
        if(!data.sync.room_id && !data.latest) narrative='Bạn chưa chọn phòng Chatwork. Kết nối dữ liệu, đồng bộ tin nhắn và chọn tháng phân tích; dashboard sẽ diễn giải từ kết quả của chính bạn.';
        else if(!data.latest) narrative=`Có ${nf.format(finite(data.sync.message_count))} tin đã lưu trong phòng đang chọn. Chưa có phiên phân tích để giải thích sự kiện chấm công. Chọn “Phân tích bằng quy trình hiện có” để tiếp tục.`;
        else if(!sessionIsComplete(data.latest)) narrative=`Phiên gần nhất ${sessionLabel} đang ở trạng thái “${stateNames[data.latest.status]||data.latest.status}”. Chưa có bộ kết quả hoàn tất để diễn giải; không sử dụng kết quả của phiên cũ thay thế.`;
        else narrative=`Phiên gần nhất ${sessionLabel} có ${nf.format(explanationRows.length)} bản ghi đang được giữ lại; ${nf.format(pending)} dòng có cờ cần kiểm tra. Chọn một bản ghi để xem tin nguồn, người được trích xuất, ngày sự kiện và trạng thái xử lý đã lưu.`;
        byId('dash-narrative').textContent=prefix+narrative;
        liveSummary.textContent=prefix+(explanationRows.length?`Phiên ${sessionLabel}: ${nf.format(explanationRows.length)} bản ghi · ${nf.format(pending)} cần kiểm tra. Xem phần Diễn giải để đối chiếu từng tin nguồn.`:narrative);
        byId('dash-explanation-source').textContent=mode==='demo'?'VÍ DỤ GIẢ LẬP':'ĐỌC TỪ KẾT QUẢ ĐÃ LƯU';
        byId('dash-open-evidence').disabled=mode!=='live'||!data.latest;
        byId('dash-explanation-note').textContent=mode==='demo'?'Các tin và kết quả dưới đây đều giả lập. Chọn Nguồn → Dữ liệu ứng dụng để diễn giải thông tin của bạn.':'Diễn giải theo phiên gần nhất của mọi phòng, có thể khác phòng đang chọn. Không tự suy đoán danh tính, xác nhận hay thay đổi số công.';
        showExplanation();
    }
    function showExplanation() {
        const row=explanationRows[explanationIndex];
        if(!row){byId('dash-explanation-steps').innerHTML='<div class="explanation-empty">Chưa có kết quả đã phân tích. Tin mới sẽ chỉ được diễn giải sau khi đi qua quy trình phân tích hiện có.</div>';explanationKey='';return;}
        explanationKey=String(row.event_id||row.result_id);byId('dash-explain-row').value=String(explanationIndex);
        const ids=Array.isArray(row.source_message_ids)&&row.source_message_ids.length?row.source_message_ids:(row.source_id?[row.source_id]:[]);
        const sources=explanationSnapshot.filter(m=>ids.map(String).includes(String(m.message_id)));
        const sourceHtml=sources.length?sources.slice(0,3).map(m=>`<blockquote><span>${escaped(m.message_id)} · Gửi ${escaped(readableDate(m.send_time))}</span><p>${escaped(m.body||'Tin nguồn không có nội dung')}</p></blockquote>`).join('')+(sources.length>3?`<small>Đang hiển thị 3/${sources.length} tin nguồn. Mở phiên đã lưu để đối chiếu toàn bộ.</small>`:''):'<p class="evidence-missing">Chưa tìm thấy tin nguồn tương ứng trong snapshot của phiên. Cần đối chiếu thủ công, không lấy tin ở phòng khác thay thế.</p>';
        const classification={official:'Nhân viên chính thức',contractor:'CTV',unresolved:'Chưa xác định nhân sự'}[row.classification]||'Chưa có phân loại';
        const personId=row.person_id||row.employee_id;
        const issues=[row.review_reason,...(Array.isArray(row.validation_errors)?row.validation_errors:[])].filter(Boolean);
        const pending=isPending(row);
        const state=row.review_state==='confirmed'?'Đã được xác nhận':pending?'Cần kiểm tra':'Không có cờ cần kiểm tra trong bản ghi';
        const amounts=[];
        for(const [field,label,unit] of [['ot_minutes','OT','phút'],['ot_used_minutes','OT dùng nghỉ bù','phút'],['minutes_compensated','Phút có bù','phút'],['minutes_not_compensated','Phút không bù','phút'],['paid_break_minutes','Nghỉ có lương','phút'],['leave_days','Nghỉ','ngày']]) {
            if(row[field]!==undefined&&row[field]!==null&&Number.isFinite(Number(row[field]))&&Number(row[field])!==0)amounts.push(`${label}: ${nf.format(Number(row[field]))} ${unit}`);
        }
        const notes=issues.length?issues.map(issue=>`<li>${escaped(typeof issue==='string'?issue:JSON.stringify(issue))}</li>`).join(''):`<li>${pending?'Bản ghi được gắn cờ kiểm tra nhưng chưa có lý do chi tiết. Cần xem phiên gốc.':'Đây là trạng thái đã lưu của bộ xử lý; không phải một lần xác minh mới từ dashboard.'}</li>`;
        const cards=[
            ['01','Tin làm căn cứ',sourceHtml+`<small>Source ID: ${escaped(ids.join(', ')||'Chưa có')}</small>`],
            ['02','Nhân sự được trích xuất',`<strong>${escaped(row.display_name||row.employee_name||'Chưa rõ tên')}</strong><p>${escaped(classification)}</p>${personId?`<small>ID đã lưu: ${escaped(personId)}</small>`:''}${row.identity_evidence?`<blockquote>${escaped(row.identity_evidence)}</blockquote>`:''}<small>Phân loại lấy từ kết quả của phiên, không khớp lại bằng danh sách hiện tại.</small>`],
            ['03','Sự kiện đã lưu',`<strong>${escaped(row.event_type||'Chưa có loại sự kiện')}</strong><p>Ngày sự kiện: ${escaped(row.event_date||'Chưa có')}</p><p>${escaped(amounts.join(' · ')||'Không có thời lượng khác 0 được lưu trong bản ghi.')}</p>${row.reason?`<blockquote>${escaped(row.reason)}</blockquote>`:''}<small>Hiển thị từng giá trị đã lưu, không cộng thành số công mới.</small>`],
            ['04','Vì sao cần chú ý',`<strong>${escaped(state)}</strong><ul>${notes}</ul><small>${pending?'Đối chiếu và xác nhận trong phiên gốc trước khi sử dụng số liệu.':'Đối chiếu tin nguồn khi cần kiểm tra lại kết quả.'}</small>`]
        ];
        root.dataset.evidenceState=pending?'review':'known';
        byId('dash-explanation-steps').innerHTML=cards.map((card,i)=>`<article class="explanation-card${i===Math.max(0,explanationPhase)?' is-reading':''}" data-explain-step="${i}"><span>${card[0]} / ${escaped(card[1])}</span>${card[2]}</article>`).join('');
    }
    function renderData() {
        const picker=byId('dash-session'),selection=picker.value;
        picker.innerHTML='<option value="latest">Phiên mới nhất</option>'+data.sessions.map(s=>`<option value="${escaped(s.session_id)}">${String(s.month).padStart(2,'0')}/${s.year} · ${escaped(s.session_id)} · ${escaped(stateNames[s.status]||s.status)}</option>`).join('');
        picker.value=[...picker.options].some(o=>o.value===selection)?selection:'latest';
        const rows = data.rows?.filter(r=>!r.is_excluded && !r.source_only);
        const pending = rows?.filter(isPending).length;
        const values = {messages:data.sync.message_count,employees:data.employees.filter(e=>e.active).length,events:rows?.length,pending};
        root.querySelectorAll('[data-metric]').forEach(node=>{
            const value=values[node.dataset.metric];
            if (value === undefined) { cancelAnimationFrame(metricAnimations.get(node));metricValues.delete(node);node.textContent='—';node.removeAttribute('data-value'); }
            else countTo(node,value);
        });
        const sessionCaption=data.latest ? `${String(data.latest.month).padStart(2,'0')}/${data.latest.year} · ${stateNames[data.latest.status] || data.latest.status}` : 'Chưa có phiên phân tích';
        root.querySelector('.dash-session-label').textContent=sessionCaption;
        byId('dash-latest-scope').textContent='Phiên đang xem: '+sessionCaption+' · '+(data.latest?.session_id||'—');
        byId('dash-room').textContent=data.sync.room_name || 'Chưa chọn phòng Chatwork';
        const messageDays=group(data.messages,'send_time');
        byId('dash-message-chart').innerHTML=svgLine(messageDays);
        byId('dash-message-chart').setAttribute('aria-label',messageDays.map(([day,count])=>`${day}: ${count} tin`).join('; ') || 'Chưa có tin nhắn');
        byId('dash-message-scope').textContent=`${nf.format(data.messages.length)} tin gần nhất, tối đa 500 · phòng đang chọn · không phản ánh độ đầy đủ của lịch sử`;
        const spark=root.querySelector('.metric-spark');
        const samples=messageDays.map(p=>p[1]);spark.innerHTML=samples.length?`<polyline points="${samples.map((v,i)=>`${i*240/Math.max(1,samples.length-1)},${40-v/Math.max(...samples)*34}`).join(' ')}" fill="none" stroke="#72e5b8" stroke-width="2"/>`:'';
        root.querySelectorAll('.metric-bars').forEach((bar,i)=>{const count=finite(Object.values(values)[i+1]);bar.innerHTML=Array.from({length:16},(_,n)=>`<i style="height:${10+(n*7)%20}px;opacity:${n<Math.min(16,count)?'.8':'.15'}"></i>`).join('');});
        const states=group(data.sessions,'status');
        byId('dash-session-chart').innerHTML=states.length?states.map(([name,count])=>`<div><span>${escaped(stateNames[name]||name)}</span><div class="dash-track"><i style="width:${count/Math.max(1,data.sessions.length)*100}%"></i></div><strong>${count}</strong></div>`).join(''):'<p class="dash-empty">Chưa có phiên chấm công</p>';
        for(const [id,key] of [['dash-success','success_count'],['dash-failed','failed_count'],['dash-syncs','sync_count']]) byId(id).textContent=nf.format(finite(data.history[key]));
        const events=data.history.recent_events || [];
        byId('dash-activity-chart').innerHTML=svgLine(group(events,'action_time'),'#83bafa');
        const classes=rows?group(rows,'classification'):[];
        const classNames={official:'Chính thức',contractor:'CTV',unresolved:'Chưa xác định'};
        byId('dash-class-chart').innerHTML=classes.length?`<div class="class-donut" style="background:conic-gradient(#68e4bc 0 ${classes.filter(x=>x[0]==='official').reduce((a,x)=>a+x[1],0)/rows.length*100}%,#79b6f3 0 ${classes.filter(x=>['official','contractor'].includes(x[0])).reduce((a,x)=>a+x[1],0)/rows.length*100}%,#eebf73 0)"><div><strong>${rows.length}</strong><span>bản ghi</span></div></div><div>${classes.map(([name,count])=>`<p><span>${escaped(classNames[name]||name)}</span><strong>${count}</strong></p>`).join('')}</div>`:'<p class="dash-empty">Chưa có kết quả phân tích</p>';
        byId('dash-event-chart').innerHTML=svgLine(rows?group(rows,'event_type'):[],'#a3b8ff',true);
        byId('dash-log').replaceChildren();
        if(!events.length) {const li=document.createElement('li');li.textContent='Chưa có hoạt động trong 7 ngày gần đây';byId('dash-log').append(li);}
        events.slice(0,5).forEach(event=>{const li=document.createElement('li');const date=new Date(event.action_time);li.dataset.status=event.status;const time=document.createElement('time');time.textContent=Number.isNaN(date.getTime())?'—':date.toLocaleTimeString('vi-VN');const text=document.createElement('span');text.textContent=activityNames[event.action_type]||event.action_type;const badge=document.createElement('small');badge.textContent=event.status==='success'?'Thành công':event.status==='failed'?'Thất bại':event.status;li.append(time,text,badge);byId('dash-log').append(li);});
        byId('dash-inputs').innerHTML=[['TIN NGUỒN',nf.format(finite(data.sync.message_count)),'Tin đã lưu / phòng đang chọn'],['NHÂN VIÊN',nf.format(data.employees.filter(e=>e.active).length),'Danh sách đang hoạt động'],['ĐỒNG BỘ',nf.format(finite(data.history.sync_count)),'Số lần trong 7 ngày']].map((v,i)=>flowCard(...v,i)).join('');
        byId('dash-outputs').innerHTML=[['SỰ KIỆN',rows?nf.format(rows.length):'—','Phiên phân tích gần nhất'],['CẦN XÁC NHẬN',pending===undefined?'—':nf.format(pending),'Dòng cần người kiểm tra'],['ĐÃ XUẤT',nf.format(data.sessions.filter(s=>s.status==='exported').length),'Trong tối đa 100 phiên']].map((v,i)=>flowCard(...v,i+3)).join('');
        root.dataset.source=mode;byId('dash-source-badge').textContent=mode==='demo'?'DỮ LIỆU GIẢ LẬP / DEMO':'DỮ LIỆU ỨNG DỤNG';
        root.querySelector('.dash-status-right').textContent=mode==='demo'?'Trình diễn cập nhật mỗi 3 giây · không lưu dữ liệu':'Đọc dữ liệu mỗi 15 giây khi mở tổng quan';
        byId('dash-flow-mode').textContent=mode==='demo'?'TRÌNH DIỄN GIẢ LẬP':'CHUYỂN ĐỘNG MINH HỌA / BỘ ĐẾM TỪ ỨNG DỤNG';
        window.dispatchEvent(new CustomEvent('dashboard:data',{detail:{messages:finite(data.sync.message_count),events:rows?.length||0,pending:pending||0,mode}}));
        renderInterpretation(); renderProcess();
        window.dispatchEvent(new CustomEvent('dashboard:summary',{detail:{rows:data.rows,session:data.latest,mode,rosterActive:data.rosterActive,skippedSession:data.skippedSession,currentRosterActive:data.employees.filter(e=>e.active).length}}));
    }
    function requestDraw() { if (!frameId && visibleDashboard() && motionLevel()) frameId=requestAnimationFrame(draw); }
    function draw(now) {
        frameId=0;if(!visibleDashboard()||!motionLevel())return;
        if(lastFrame&&now-lastFrame<40){requestDraw();return;}
        drawTime+=lastFrame?Math.min(.08,(now-lastFrame)/1000):0;lastFrame=now;
        if(Math.floor(drawTime/4)!==processTick)renderProcess();
        root.style.setProperty('--scan-position',`${(drawTime*65)%600}px`);
        root.style.setProperty('--ambient-phase',String(Math.sin(drawTime*.7)*.5+.5));
        if(byId('dash-follow').checked&&!explanationHeld&&explanationRows.length) {
            const phase=Math.floor(drawTime/3)%4;
            if(phase!==explanationPhase){explanationPhase=phase;root.querySelectorAll('[data-explain-step]').forEach((card,i)=>card.classList.toggle('is-reading',i===phase));window.CinematicScene?.goTo(['sync','history','export','settings'][phase]);}
            if(drawTime-explanationChangedAt>=12){explanationChangedAt=drawTime;explanationIndex=(explanationIndex+1)%explanationRows.length;showExplanation();}
        }
        const p=Math.min(1,(now-dataTransition)/1000);root.style.setProperty('--data-reveal',String(p));
        requestDraw();
    }
    byId('dash-source').addEventListener('change',()=>{mode=byId('dash-source').value;controller?.abort();data=null;metricValues.clear();setTimeout(refresh,50);});
    byId('dash-session').addEventListener('change',()=>{sessionChoice=byId('dash-session').value;controller?.abort();data=null;setTimeout(refresh,50);});
    byId('dash-motion').addEventListener('change',()=>{intensity=byId('dash-motion').value;document.documentElement.dataset.motionPolicy=intensity==='system'?'system':'full';stopped=false;setMotion();});
    byId('dash-refresh').addEventListener('click',()=>{if(mode==='demo')demoTick++;refresh();});
    byId('dash-explain-row').addEventListener('change',()=>{explanationIndex=Number(byId('dash-explain-row').value)||0;byId('dash-follow').checked=false;showExplanation();});
    const explanationPanel=root.querySelector('.interpretation-panel');
    explanationPanel.addEventListener('pointerenter',()=>explanationHeld=true);explanationPanel.addEventListener('pointerleave',()=>explanationHeld=false);
    explanationPanel.addEventListener('focusin',()=>explanationHeld=true);explanationPanel.addEventListener('focusout',event=>{if(!explanationPanel.contains(event.relatedTarget))explanationHeld=false;});
    root.addEventListener('click',event=>{const button=event.target.closest('[data-dashboard-go]');if(button)nav.querySelector(`[data-section="${button.dataset.dashboardGo}"]`)?.click();});
    byId('dash-open-evidence').addEventListener('click',async()=>{
        if(mode!=='live'||!data?.latest)return;
        const button=byId('dash-open-evidence');button.disabled=true;
        try {nav.querySelector('[data-section="export"]').click();if(typeof window.openSession==='function')await window.openSession(data.latest.session_id);}
        catch(error){const notice=document.getElementById('notice');notice.hidden=false;notice.textContent=error.message;notice.className='error';}
        finally{button.disabled=false;}
    });
    reduced.addEventListener('change',setMotion);
    window.addEventListener('cinematic:paused',event=>{stopped=event.detail.paused;setMotion();});
    document.addEventListener('visibilitychange',()=>{lastFrame=0;if(document.hidden){cancelAnimationFrame(frameId);frameId=0;}else{setMotion();refresh();}});
    clockTimer=setInterval(()=>{if(!visibleDashboard())return;byId('dash-clock').textContent=new Date().toLocaleTimeString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'})+' ICT';},1000);
    let lastPoll=0;pollTimer=setInterval(()=>{const interval=['analyzing','prepared'].includes(data?.latest?.status)?2000:15000;if(mode==='live'&&Date.now()-lastPoll>=interval){lastPoll=Date.now();refresh();}},1000);
    demoTimer=setInterval(()=>{if(mode==='demo'&&visibleDashboard()){demoTick++;refresh();}},3000);
    window.Dashboard5D={refresh,getState:()=>({mode,active,loading,level:motionLevel(),animationTime:drawTime,explanationPhase,selectedEvent:explanationKey,hasData:!!data,messages:data?.sync.message_count,rows:data?.rows?.length,processStatus:data?.latest?.status||'idle',error:root.dataset.error==='true'})};
    window.addEventListener('pagehide',event=>{if(event.persisted)return;disposed=true;clearInterval(clockTimer);clearInterval(pollTimer);clearInterval(demoTimer);cancelAnimationFrame(frameId);controller?.abort();metricAnimations.forEach(cancelAnimationFrame);});
    openOverview();
})();
