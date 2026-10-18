/* Presentation policy only: no network calls, data reads or application mutations. */
'use strict';
(() => {
    const html=document.documentElement;
    const reduced=matchMedia('(prefers-reduced-motion: reduce)');
    const motifs=[
        '<path class="fx-packet" d="M2 16H76"/><path d="M2 22h20l8-15 12 24 10-15h24"/>',
        '<circle cx="39" cy="18" r="13"/><g class="fx-orbit"><circle cx="39" cy="18" r="17" stroke-dasharray="12 9"/><circle cx="39" cy="1" r="3" fill="currentColor"/></g>',
        '<g class="fx-equalizer">'+[0,1,2,3,4,5,6,7].map(i=>`<rect x="${6+i*9}" y="${7+i%3*4}" width="4" height="${28-i%3*4}" style="animation-delay:-${i*.19}s"/>`).join('')+'</g>',
        '<g class="fx-beacon"><path d="M39 2 58 18 39 34 20 18Z"/><circle cx="39" cy="18" r="5" fill="currentColor"/></g><path class="fx-packet" d="M0 18H18M60 18H78"/>'
    ];
    document.querySelectorAll('.dash-metrics > .dash-panel').forEach((panel,i)=>{
        const glyph=document.createElement('div');glyph.className='panel-signature signature-'+i;
        glyph.setAttribute('aria-hidden','true');glyph.innerHTML=`<svg viewBox="0 0 78 36">${motifs[i]}</svg>`;panel.append(glyph);
    });
    document.querySelectorAll('.dash-panel > header').forEach((header,i)=>{
        const glyph=document.createElement('span');glyph.className='header-signature';glyph.setAttribute('aria-hidden','true');
        glyph.innerHTML=`<svg viewBox="0 0 78 36">${motifs[i%4]}</svg>`;header.prepend(glyph);
    });
    document.querySelectorAll('.workspace .card').forEach((panel,i)=>{
        const glyph=document.createElement('div');glyph.className='workspace-signature';glyph.setAttribute('aria-hidden','true');
        glyph.innerHTML=`<svg viewBox="0 0 78 36">${motifs[i%4]}</svg>`;panel.prepend(glyph);
    });
    const indicator=document.createElement('span');indicator.className='motion-indicator';indicator.id='motion-indicator';
    document.querySelector('.dash-toolbar')?.append(indicator);
    function update(level) {
        const paused=(html.dataset.motionPolicy!=='full'&&reduced.matches)||Number(level)===0;
        html.dataset.panelMotion=paused?'paused':'running';
        html.style.setProperty('--panel-cycle',`${(5-Math.min(1,Math.max(0,Number(level)||.4))*2.5).toFixed(1)}s`);
        indicator.textContent=paused?'Hiệu ứng tạm dừng':'Hiệu ứng tự chạy · V6.2';
    }
    function visibility(){html.dataset.panelVisibility=document.hidden?'hidden':'visible';}
    window.addEventListener('dashboard:motion',event=>update(event.detail.level));
    reduced.addEventListener('change',()=>update(window.Dashboard5D?.getState().level??.4));
    document.addEventListener('visibilitychange',visibility);
    update(window.Dashboard5D?.getState().level??.4);visibility();
})();
