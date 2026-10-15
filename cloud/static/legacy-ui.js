'use strict';

(() => {
    const body = document.body;
    const oldAside = body.querySelector(':scope > aside');
    const oldMain = body.querySelector(':scope > main');
    if (!oldAside || !oldMain) {
        throw new Error('Không tìm thấy giao diện ứng dụng để dựng bố cục.');
    }

    const header = document.createElement('header');
    header.className = 'header';
    header.innerHTML = '<h1>ChamCong / Chatwork</h1><span class="version" id="appVersion">Bộ phận AI · Đặng Gia Khánh</span><span id="pageLabel" hidden></span>';

    const skipLink = document.createElement('a');
    skipLink.className = 'skip-link';
    skipLink.href = '#main-content';
    skipLink.textContent = 'Bỏ qua phần giới thiệu, đến nội dung chính';
    skipLink.addEventListener('click', () => {
        skipLink.style.display = 'none';
    });

    const nav = document.createElement('nav');
    nav.className = 'nav';
    nav.setAttribute('aria-label', 'Chức năng chính');
    nav.innerHTML = `
        <button type="button" class="nav-item active" data-section="sync">Đồng bộ</button>
        <button type="button" class="nav-item" data-section="export">Xuất công</button>
        <button type="button" class="nav-item" data-section="history">Lịch sử</button>
        <button type="button" class="nav-item" data-section="settings">Thiết lập</button>
    `;
    nav.addEventListener('click', event => {
        const button = event.target.closest('[data-section]');
        if (button) {
            window.CinematicScene?.goTo(button.dataset.section);
        }
    });

    const container = document.createElement('div');
    container.className = 'container';
    container.id = 'main-content';

    const intro = document.createElement('aside');
    intro.className = 'intro';
    intro.setAttribute('aria-label', 'Không gian xe 3D');
    intro.dataset.shot = 'sync';
    intro.innerHTML = `
        <div class="cinematic-viewport" aria-hidden="true"></div>
        <div class="cinematic-controls">
            <div class="cinematic-dots" role="group" aria-label="Chọn góc máy">
                <button type="button" class="cinematic-dot" aria-label="Góc toàn cảnh" aria-pressed="true"></button>
                <button type="button" class="cinematic-dot" aria-label="Góc cận thân xe" aria-pressed="false"></button>
                <button type="button" class="cinematic-dot" aria-label="Góc phía sau" aria-pressed="false"></button>
                <button type="button" class="cinematic-dot" aria-label="Góc phía trước" aria-pressed="false"></button>
            </div>
            <button type="button" class="cinematic-toggle" aria-pressed="false">Tạm dừng</button>
        </div>
        <div class="cinematic-timeline" aria-hidden="true"></div>
    `;

    const workspace = document.createElement('div');
    workspace.className = 'workspace';
    workspace.setAttribute('role', 'region');
    workspace.setAttribute('aria-label', 'Nội dung chức năng');

    const notice = oldMain.querySelector('#notice');
    const pages = [...oldMain.querySelectorAll(':scope > .page')];
    const dialogs = [...oldMain.querySelectorAll(':scope > dialog')];
    if (!notice || pages.length !== 4) {
        throw new Error('Giao diện chức năng chưa đầy đủ để dựng bố cục.');
    }

    pages.forEach(page => page.classList.add('section'));
    workspace.append(notice, ...pages);
    container.append(intro, workspace);

    body.insertBefore(skipLink, body.firstChild);
    body.insertBefore(header, oldAside);
    body.insertBefore(nav, oldAside);
    body.insertBefore(container, oldAside);
    dialogs.forEach(dialog => body.append(dialog));
    oldAside.remove();
    oldMain.remove();
})();
