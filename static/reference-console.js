/* Layout and scene selection only. Reuses the existing overview nodes and handlers. */
'use strict';
(() => {
    const root=document.getElementById('control-dashboard');if(!root)return;
    root.classList.add('reference-console');root.dataset.consoleView='neural';
    const nav=document.querySelector('body > .nav'),overview=document.getElementById('dashboard-nav');
    const syncNavigation=()=>{if(root.hidden)return;nav?.querySelectorAll('.nav-item').forEach(button=>{const expected=button===overview;if(button.classList.contains('active')!==expected)button.classList.toggle('active',expected);if(button===overview)button.setAttribute('aria-current','page');});};
    const navObserver=new MutationObserver(syncNavigation);if(nav)navObserver.observe(nav,{subtree:true,attributes:true,attributeFilter:['class']});syncNavigation();
    window.addEventListener('pagehide',event=>{if(!event.persisted)navObserver.disconnect();});
    const toolbar=document.createElement('div');toolbar.className='console-view-switch';toolbar.setAttribute('role','group');toolbar.setAttribute('aria-label','Phong cách bảng điều khiển');
    toolbar.innerHTML='<span class="terminal-name">01 / NEURAL TERMINAL</span><span>Minh họa chuyển động · số liệu từ nguồn đã chọn</span>';
    root.querySelector('.dash-statusbar').before(toolbar);
    const deck=document.createElement('div');deck.className='console-kpi-deck';
    const metrics=root.querySelector('.dash-metrics'),people=root.querySelector('.people-summary');metrics.before(deck);deck.append(metrics,people.querySelector('.people-kpis'));
    deck.after(root.querySelector('.dash-upper'));root.querySelector('.dash-upper').after(root.querySelector('.neural-panel'));
    const lower=document.createElement('div');lower.className='console-lower-deck';root.querySelector('.neural-panel').after(lower);lower.append(people,root.querySelector('.dash-bottom'));
    lower.after(root.querySelector('.interpretation-panel'));
    const signal=document.createElement('div');signal.className='console-signal-strip';signal.setAttribute('aria-hidden','true');
    signal.innerHTML='<div>CHATWORK / SNAPSHOT <b>→</b> AI EXTRACTION <b>→</b> IDENTITY MATCH <b>→</b> HUMAN REVIEW <b>→</b> EXCEL / 5 SHEETS <b>◆</b> EVIDENCE PRESERVED <b>◆</b> CHATWORK / SNAPSHOT <b>→</b> AI EXTRACTION <b>→</b> IDENTITY MATCH <b>→</b> HUMAN REVIEW <b>→</b> EXCEL / 5 SHEETS <b>◆</b> EVIDENCE PRESERVED <b>◆</b></div>';
    root.querySelector('.neural-panel').after(signal);
    toolbar.addEventListener('click',event=>{
        const button=event.target.closest('button[data-console-view]');if(!button)return;
        root.dataset.consoleView=button.dataset.consoleView;
        toolbar.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
        window.dispatchEvent(new CustomEvent('console:view',{detail:{view:button.dataset.consoleView}}));
    });
})();
