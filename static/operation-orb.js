/* Visual observer only. Returns the original fetch promise and never changes request data. */
'use strict';
(() => {
    const container=document.querySelector('.container'),nav=document.querySelector('body > .nav');
    if(!container||!nav)return;
    const panel=document.createElement('aside');panel.className='operation-sidebar';panel.id='operation-sidebar';
    panel.setAttribute('aria-label','Điều khiển và trạng thái thao tác');
    panel.innerHTML=`<header><span>WORKFLOW / 5D CORE</span><small id="orb-view-name">Điều khiển</small></header>
      <div class="operation-orbit" data-expanded="false"><svg viewBox="0 0 300 300" class="orb-tree" aria-hidden="true"><path d="M150 150V28"/><path d="M150 150Q205 85 261 105"/><path d="M150 150Q220 180 222 246"/><path d="M150 150Q80 180 78 246"/><path d="M150 150Q95 85 39 105"/></svg>
      <button type="button" class="orbit-center" aria-expanded="false" aria-controls="orb-branches" aria-label="Mở các nhánh chức năng"><i class="orbit-ring orbit-ring-one" aria-hidden="true"></i><i class="orbit-ring orbit-ring-two" aria-hidden="true"></i><i class="orbit-dots" aria-hidden="true"></i><span class="orbit-icon" aria-hidden="true">◎</span><strong id="orb-center-state">Sẵn sàng</strong><small>Nhấn để mở nhánh</small></button>
      <div id="orb-branches" hidden><button type="button" data-orb-target="sync">Đồng bộ</button><button type="button" data-orb-target="export">Xuất công</button><button type="button" data-orb-target="history">Lịch sử</button><button type="button" data-orb-target="settings">Thiết lập</button><button type="button" data-orb-target="employees">Nhân viên</button></div></div>
      <div class="orb-feedback" role="status" aria-live="polite"><span id="orb-action-label">Chờ thao tác của bạn</span><p id="orb-action-detail">Chọn nhánh hoặc dùng biểu mẫu bên cạnh. Trạng thái lấy từ phản hồi của ứng dụng.</p></div>
      <ol class="orb-steps"><li data-orb-step="idle">Nhập dữ liệu</li><li data-orb-step="busy">Gửi xử lý</li><li data-orb-step="response">Nhận phản hồi</li><li data-orb-step="done">Kết quả</li></ol>
      <button type="button" class="orb-back">← Về tổng quan</button><p class="orb-footnote">Vòng sáng là hiệu ứng. Chỉ hiện thành công khi thao tác thực sự được ứng dụng chấp nhận; không tự xác nhận bảng công.</p>`;
    container.append(panel);
    const local=id=>panel.querySelector('#'+id),stage=panel.querySelector('.operation-orbit');
    const center=panel.querySelector('.orbit-center'), branches=local('orb-branches');
    const labels={sync:'Đồng bộ',export:'Xuất công',history:'Lịch sử',settings:'Thiết lập',employees:'Nhân viên'};
    let status='idle',expanded=false,batch=[],sequence=0;
    const pending=new Map();
    function paint(kind,label,detail) {
        status=kind;panel.dataset.state=kind;
        local('orb-center-state').textContent={idle:'Sẵn sàng',busy:'Đang xử lý',success:'Thành công',review:'Cần xác nhận',failed:'Chưa hoàn tất',unknown:'Chưa xác minh'}[kind];
        panel.querySelector('.orbit-icon').textContent={idle:'◎',busy:'↻',success:'✓',review:'!',failed:'×',unknown:'?'}[kind];
        local('orb-action-label').textContent=label;local('orb-action-detail').textContent=detail;
        panel.querySelectorAll('[data-orb-step]').forEach((node,i)=>node.classList.toggle('current',i===(kind==='idle'?0:kind==='busy'?1:kind==='unknown'?2:3)));
    }
    function expand(value) {expanded=value;stage.dataset.expanded=String(value);branches.hidden=!value;center.setAttribute('aria-expanded',String(value));center.setAttribute('aria-label',value?'Thu gọn các nhánh chức năng':'Mở các nhánh chức năng');}
    center.addEventListener('click',()=>expand(!expanded));
    panel.addEventListener('keydown',event=>{if(event.key==='Escape'){expand(false);center.focus();}});
    branches.addEventListener('click',event=>{const button=event.target.closest('[data-orb-target]');if(!button)return;nav.querySelector(`[data-section="${button.dataset.orbTarget}"]`)?.click();});
    panel.querySelector('.orb-back').addEventListener('click',()=>document.getElementById('dashboard-nav')?.click());
    nav.addEventListener('click',event=>{const key=event.target.closest('[data-section]')?.dataset.section;if(!key)return;local('orb-view-name').textContent=labels[key]||'Điều khiển';branches.querySelectorAll('button').forEach(button=>button.classList.toggle('selected',button.dataset.orbTarget===key));if(!pending.size&&status==='idle')paint('idle','Đang mở '+labels[key],'Nhập thông tin trong biểu mẫu. Nhánh điều khiển không tự gửi dữ liệu hoặc xác nhận kết quả.');});
    const motion=matchMedia('(prefers-reduced-motion: reduce)');
    function motionPolicy() {panel.dataset.motion=(document.documentElement.dataset.motionPolicy!=='full'&&motion.matches)||document.documentElement.dataset.motion==='paused'?'paused':'running';}
    motion.addEventListener('change',motionPolicy);
    const observer=new MutationObserver(motionPolicy);observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-motion']});motionPolicy();
    const originalFetch=window.fetch;
    function operation(input,init) {
        try {
            const url=new URL(input instanceof Request?input.url:String(input),location.href);
            const method=String(init?.method||(input instanceof Request?input.method:'GET')).toUpperCase();
            if(url.origin!==location.origin||method!=='POST')return null;
            const path=url.pathname;
            if(path==='/api/sync/run'||path==='/api/sync')return 'Đồng bộ tin nhắn';
            if(path.startsWith('/api/config/chatwork'))return 'Kiểm tra kết nối Chatwork';
            if(path.startsWith('/api/config/ai'))return 'Kiểm tra kết nối phân tích';
            if(path==='/api/config/room'||path==='/api/room')return 'Lưu nhóm Chatwork';
            if(path==='/api/config/schedule')return 'Lưu lịch đồng bộ';
            if(path==='/api/export/preflight')return 'Kiểm tra kỳ chấm công';
            if(path==='/api/export/create-session'||path==='/api/sessions')return 'Tạo phiên chấm công';
            if(/^\/api\/(export|sessions)\/[^/]+\/analyze$/.test(path))return 'Phân tích tin nhắn';
            if(/^\/api\/(export|sessions)\/[^/]+\/export$/.test(path))return 'Xuất bảng Excel';
            if(/^\/api\/(export|sessions)\/[^/]+\/(review|correct)$/.test(path))return 'Lưu kiểm tra bản ghi';
            if(path.startsWith('/api/employees'))return 'Lưu danh sách nhân viên';
            if(path==='/api/data/import')return 'Nhập tin lịch sử';
            return null;
        } catch {return null;}
    }
    function finish(id,outcome) {
        if(!pending.has(id))return;
        const label=pending.get(id);pending.delete(id);batch.push({...outcome,label});
        if(pending.size){paint('busy','Đang xử lý '+pending.size+' thao tác','Đang chờ phản hồi của ứng dụng. Có thể tiếp tục xem thông tin bên cạnh.');return;}
        const final=batch.find(item=>item.kind==='failed')||batch.find(item=>item.kind==='unknown')||batch.find(item=>item.kind==='review')||batch.at(-1);
        paint(final.kind,final.label,final.detail);
    }
    const instrumentedFetch=function(...args) {
        const label=operation(args[0],args[1]);
        let id;
        if(label){if(!pending.size)batch=[];id=++sequence;pending.set(id,label);paint('busy',label,'Thông tin đang được ứng dụng xử lý. Vòng sáng không biểu diễn phần trăm tiến độ.');}
        // The caller receives exactly the original promise, response and errors.
        let promise;
        try{promise=originalFetch.apply(this,args);}catch(error){if(label)finish(id,{kind:'failed',detail:'Không gửi được yêu cầu. Xem thông báo trong biểu mẫu.'});throw error;}
        if(label)promise.then(async response=>{
            if(!response.ok){finish(id,{kind:'failed',detail:'Ứng dụng trả lỗi HTTP '+response.status+'. Xem thông báo trong biểu mẫu; dữ liệu không được tự xác nhận.'});return;}
            let payload;try{payload=await response.clone().json();}catch{finish(id,{kind:'unknown',detail:'Chưa đọc được phản hồi xác nhận. Kiểm tra thông báo trong biểu mẫu.'});return;}
            if(payload.success!==true||payload.data?.success===false){finish(id,{kind:'failed',detail:'Ứng dụng chưa chấp nhận thao tác. Xem thông báo chi tiết trong biểu mẫu.'});return;}
            if(payload.data?.can_continue===false){finish(id,{kind:'review',detail:'Chưa đủ điều kiện tiếp tục. Kiểm tra dữ liệu của kỳ trong quy trình hiện có.'});return;}
            if(payload.data?.status==='review'||payload.data?.requires_risk_acceptance||payload.data?.is_draft){finish(id,{kind:'review',detail:payload.data?.is_draft?'Thao tác hoàn tất với bản tạm. Cần đối chiếu dữ liệu trước khi dùng số liệu chính thức.':'Ứng dụng yêu cầu kiểm tra hoặc xác nhận. Thực hiện trong biểu mẫu; vòng tròn không tự chấp nhận thay bạn.'});return;}
            finish(id,{kind:'success',detail:'Ứng dụng đã trả phản hồi thành công cho thao tác này. Kết quả chi tiết nằm trong biểu mẫu bên cạnh.'});
        }).catch(()=>finish(id,{kind:'failed',detail:'Không nhận được phản hồi hoàn tất. Kiểm tra kết nối và thông báo trong biểu mẫu.'}));
        return promise;
    };
    window.fetch=instrumentedFetch;
    window.OperationOrb={getState:()=>({status,expanded,pending:pending.size}),expand};
    paint('idle','Chờ thao tác của bạn','Chọn nhánh hoặc dùng biểu mẫu bên cạnh. Trạng thái lấy từ phản hồi của ứng dụng.');
    window.addEventListener('pagehide',event=>{if(event.persisted)return;observer.disconnect();if(window.fetch===instrumentedFetch)window.fetch=originalFetch;},{once:false});
})();
