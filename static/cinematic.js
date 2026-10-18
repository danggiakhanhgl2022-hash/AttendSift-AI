/* Decorative local 3D visualization. Never reads records or calls business APIs. */
'use strict';
(() => {
    const hero = document.querySelector('.intro');
    if (!hero) return;
    const host = hero.querySelector('.cinematic-viewport');
    const toggle = hero.querySelector('.cinematic-toggle');
    const dots = [...hero.querySelectorAll('.cinematic-dot')];
    const policy = matchMedia('(prefers-reduced-motion: reduce)');
    const keys = ['sync', 'export', 'history', 'settings'];
    const captions = ['Thu thập tin nguồn', 'Trích xuất sự kiện', 'Đối chiếu & truy vết', 'Kết nối hệ thống'];
    const systemReduction = () => document.documentElement.dataset.motionPolicy !== 'full' && policy.matches;
    let paused = systemReduction(), visible = true, shot = 0, raf = 0;
    let elapsed = 0, last = 0, frames = 0, render = () => {}, disposed = false, energy = .55;
    let processState={status:'idle',complete:false,hasSources:false};
    let sceneView='neural',studioStationCount=0,particleCount=0;
    window.addEventListener('dashboard:process',event=>{processState=event.detail;});
    window.addEventListener('console:view',event=>{sceneView=event.detail.view==='studio'?'studio':'neural';hero.dataset.sceneView=sceneView;render();requestFrame();});
    const pointer = { x: 0, y: 0 };
    hero.setAttribute('aria-label', 'Minh họa kiến trúc dữ liệu 3D');
    const copy = document.createElement('div');
    copy.className = 'tech-scene-copy';
    copy.innerHTML = '<span class="tech-eyebrow">ATTENDSIFT / DATA ENGINE</span><h2>Dữ liệu chuyển động.<br><em>Căn cứ được giữ lại.</em></h2><p>Chatwork → AI → Đối chiếu → Excel</p>';
    hero.prepend(copy);
    const legend = document.createElement('div');
    legend.className = 'tech-legend';
    legend.innerHTML = '<span>● Tin nguồn</span><span>● Đối chiếu</span><span>● Cần xác nhận</span><small>Minh họa kiến trúc · Không biểu diễn dữ liệu trực tiếp</small>';
    hero.append(legend);
    const stage = document.createElement('div');
    stage.className = 'tech-stage-label';
    copy.append(stage);
    function requestFrame() {
        if (!disposed && !raf && !paused && visible && !document.hidden && host.dataset.engine !== 'static') raf = requestAnimationFrame(frame);
    }
    function sync() {
        toggle.textContent = paused ? '▶ Tiếp tục' : 'Ⅱ Tạm dừng';
        toggle.setAttribute('aria-pressed', String(paused));
        toggle.setAttribute('aria-label', paused ? 'Tiếp tục hiệu ứng nền' : 'Tạm dừng hiệu ứng nền');
        document.documentElement.dataset.motion = paused ? 'paused' : 'running';
        hero.dataset.playing = String(!paused);
        last = 0;
        if (paused) { cancelAnimationFrame(raf); raf = 0; }
        render(); requestFrame();
    }
    function goTo(key) {
        const next = keys.indexOf(key === 'employees' ? 'history' : key);
        if (next < 0) return;
        shot = next; hero.dataset.shot = keys[shot];
        stage.textContent = `0${shot + 1} / ${captions[shot]}`;
        dots.forEach((dot, i) => dot.setAttribute('aria-pressed', String(i === shot)));
        render();
    }
    window.CinematicScene = { goTo, getState: () => ({ shot: keys[shot], paused, ready: hero.dataset.ready === 'true', engine: host.dataset.engine, frames,sceneView,studioStationCount,particleCount,sceneTime:elapsed }) };
    dots.forEach((dot, i) => {
        dot.setAttribute('aria-label', captions[i]);
        dot.addEventListener('click', () => goTo(keys[i]));
    });
    toggle.addEventListener('click', () => { paused = !paused; sync(); window.dispatchEvent(new CustomEvent('cinematic:paused',{detail:{paused}})); });
    window.addEventListener('dashboard:motion', event => {
        energy = Math.max(0, Math.min(1, Number(event.detail.level) || 0));
        paused = !!event.detail.stopped || systemReduction(); sync();
    });
    policy.addEventListener('change', () => { if (document.documentElement.dataset.motionPolicy !== 'full') { paused = policy.matches; sync(); } });
    goTo('sync'); sync();
    const visibility = new IntersectionObserver(entries => {
        visible = entries[0].isIntersecting;
        if (!visible) { cancelAnimationFrame(raf); raf = 0; }
        last = 0; requestFrame();
    });
    visibility.observe(hero);
    document.addEventListener('visibilitychange', () => {
        cancelAnimationFrame(raf); raf = 0; last = 0; requestFrame();
    });
    hero.addEventListener('pointermove', event => {
        if (paused || systemReduction() || event.pointerType === 'touch') return;
        const rect = hero.getBoundingClientRect();
        pointer.x = (event.clientX - rect.left) / rect.width - .5;
        pointer.y = (event.clientY - rect.top) / rect.height - .5;
    });
    hero.addEventListener('pointerleave', () => { pointer.x = pointer.y = 0; });
    const resources = [];
    let resize;
    function fallback() {
        host.classList.add('technology-fallback');
        host.dataset.engine = 'static'; hero.dataset.ready = 'fallback';
        cancelAnimationFrame(raf); raf = 0;
    }
    function frame(now) {
        raf = 0;
        if (paused || !visible || document.hidden || disposed) return;
        if (last && now - last < 32) { requestFrame(); return; }
        elapsed += last ? Math.min((now - last) / 1000, .06) : 0;
        last = now; frames++; render(); requestFrame();
    }
    try {
        const T = window.THREE;
        if (!T) throw Error('3D library unavailable');
        const renderer = new T.WebGLRenderer({ alpha: true, antialias: devicePixelRatio < 2, powerPreference: 'low-power' });
        renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
        renderer.setClearColor(0x030c16, 0);
        host.append(renderer.domElement);
        renderer.domElement.addEventListener('webglcontextlost', e => { e.preventDefault(); fallback(); });
        const scene = new T.Scene();
        scene.fog = new T.FogExp2(0x040d17, .035);
        const camera = new T.PerspectiveCamera(39, 1, .1, 80);
        camera.position.set(0, .5, 12.4);
        scene.add(new T.AmbientLight(0x8fdbf4, 1.1));
        const light = new T.PointLight(0x52e9d0, 2, 20); light.position.set(3, 4, 4); scene.add(light);
        const group = new T.Group(); scene.add(group);
        const cyan = 0x63deef, green = 0x55ecc0, amber = 0xf1bb65;
        function material(color, opacity) { const m = new T.MeshBasicMaterial({color, transparent: true, opacity, depthWrite: false}); resources.push(m); return m; }
        const sphereGeo = new T.SphereGeometry(2.12, 30, 20); resources.push(sphereGeo);
        const shell = new T.Mesh(sphereGeo, new T.MeshBasicMaterial({color: cyan, wireframe: true, transparent: true, opacity: .035}));
        resources.push(shell.material); group.add(shell);
        // Deterministic particle sphere: illustrative topology, never employee data.
        const vertices = [], colors = [], total = innerWidth<700?2400:5600;particleCount=total;
        for (let i = 0; i < total; i++) {
            const y = 1 - (i / (total - 1)) * 2, radius = Math.sqrt(1 - y * y);
            const angle = i * Math.PI * (3 - Math.sqrt(5));
            const ripple = 1 + .22 * Math.sin(angle * 5 + y * 9) + .06*Math.cos(angle*11);
            const x = Math.cos(angle) * radius * 1.95 * ripple;
            // Two connected lobes suggest a processing brain without claiming a model architecture.
            vertices.push(x + Math.sign(x) * .14, y * 1.68, Math.sin(angle) * radius * 1.6 * ripple);
            const c = new T.Color(Math.sin(angle*2+y*6)>.45?0xec6e94:i%17===0?0xf1e9bd:i%3?0x7dffb1:cyan); colors.push(c.r, c.g, c.b);
        }
        const pointGeo = new T.BufferGeometry(); pointGeo.setAttribute('position', new T.Float32BufferAttribute(vertices, 3)); pointGeo.setAttribute('color', new T.Float32BufferAttribute(colors, 3)); resources.push(pointGeo);
        const glowCanvas=document.createElement('canvas');glowCanvas.width=32;glowCanvas.height=32;
        const glowCtx=glowCanvas.getContext('2d'),glow=glowCtx.createRadialGradient(16,16,1,16,16,16);
        glow.addColorStop(0,'#ffffff');glow.addColorStop(.2,'#ffffffe0');glow.addColorStop(1,'#ffffff00');glowCtx.fillStyle=glow;glowCtx.fillRect(0,0,32,32);
        const particleTexture=new T.CanvasTexture(glowCanvas);resources.push(particleTexture);
        const baseVertices=new Float32Array(vertices);
        const pointMat = new T.PointsMaterial({size: .055,map:particleTexture, vertexColors: true, transparent: true, opacity: .95, blending: T.AdditiveBlending, depthWrite: false}); resources.push(pointMat);
        const points = new T.Points(pointGeo, pointMat); group.add(points);
        const orbitRings=[];
        for (let i = 0; i < 3; i++) {
            const geo = new T.TorusGeometry(2.35 + i * .25, .006, 5, 140); resources.push(geo);
            const ring = new T.Mesh(geo, material(i === 2 ? amber : cyan, i === 2 ? .1 : .16));
            ring.rotation.set(.8 + i * .5, i * .6, .2); group.add(ring);orbitRings.push(ring);
        }
        const panelGroup = new T.Group(); scene.add(panelGroup);
        panelGroup.visible = !document.querySelector('#control-dashboard');
        const labels = [['01', 'CHATWORK API', 'Tin nhắn / Source ID'], ['02', 'AI EXTRACTION', 'Người · ngày · số phút'], ['03', 'EMPLOYEE MATCH', 'Đối chiếu danh sách'], ['04', 'EXCEL EXPORT', '5 sheet / Truy vết']];
        const panels = [];
        labels.forEach((label, i) => {
            const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 240;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#091c2bea'; ctx.fillRect(0, 0, 640, 240);
            ctx.strokeStyle = '#365f74'; ctx.lineWidth = 3; ctx.strokeRect(2, 2, 636, 236);
            ctx.fillStyle = '#6ae9d2'; ctx.font = '22px Segoe UI'; ctx.fillText(label[0] + ' / DATA LAYER', 28, 44);
            ctx.fillStyle = '#e1f3fa'; ctx.font = 'bold 35px Segoe UI'; ctx.fillText(label[1], 28, 106);
            ctx.fillStyle = '#9ab8c8'; ctx.font = '25px Segoe UI'; ctx.fillText(label[2], 28, 152);
            for (let n = 0; n < 12; n++) { ctx.fillStyle = n < 7 ? '#51cdbb' : '#214252'; ctx.fillRect(28 + n * 48, 191, 32, 5); }
            const tex = new T.CanvasTexture(canvas); resources.push(tex);
            const mat = new T.MeshBasicMaterial({map: tex, transparent: true, opacity: .94, side: T.DoubleSide}); resources.push(mat);
            const geo = new T.PlaneGeometry(2.35, .88); resources.push(geo);
            const panel = new T.Mesh(geo, mat);
            const x = i % 2 ? 2.55 : -2.55, y = i < 2 ? 1.6 : -1.6;
            panel.position.set(x, y, .9); panel.rotation.y = x > 0 ? -.16 : .16;
            panelGroup.add(panel); panels.push(panel);
        });
        const paths = [], pulses = [],transmissionLines=[];
        panels.forEach((panel, i) => {
            const start = panel.position.clone(); start.x += start.x > 0 ? -1.18 : 1.18;
            const end = new T.Vector3(start.x > 0 ? .8 : -.8, start.y * .35, .1);
            const curve = new T.CatmullRomCurve3([start, new T.Vector3(start.x * .65, start.y, .6), end]);
            paths.push(curve);
            const geo = new T.BufferGeometry().setFromPoints(curve.getPoints(36)); resources.push(geo);
            const mat = new T.LineBasicMaterial({color: i === 3 ? amber : cyan, transparent: true, opacity: .35}); resources.push(mat);
            const transmission=new T.Line(geo, mat);scene.add(transmission);transmissionLines.push(transmission);
            for (let n = 0; n < 5; n++) {
                const ballGeo = new T.SphereGeometry(.032 + (n === 0 ? .014 : 0), 7, 6); resources.push(ballGeo);
                const ball = new T.Mesh(ballGeo, material(i === 3 ? amber : green, 1));
                ball.userData = {path:i, offset:n / 5}; scene.add(ball); pulses.push(ball);
            }
        });
        const grid = new T.GridHelper(24, 32, 0x184659, 0x0c2536); grid.position.y = -3.1; scene.add(grid);
        resources.push(grid.geometry, ...(Array.isArray(grid.material) ? grid.material : [grid.material]));
        const studio=null;
        let neuralDistance=7.9;
        render = () => {
            const inStudio=sceneView==='studio'&&!!studio;
            shell.visible=!document.querySelector('.reference-console');
            group.scale.set(document.querySelector('.reference-console')?1.3:1,1,1);
            group.visible=!inStudio;grid.visible=!inStudio;if(studio){studio.group.visible=inStudio;if(inStudio)studio.update(elapsed,processState,energy);}
            transmissionLines.forEach(line=>line.visible=!inStudio);
            group.rotation.y = elapsed * (.10 + energy * .15) + pointer.x * .2;
            orbitRings.forEach((ring,i)=>{ring.rotation.z=elapsed*(.12+i*.06)*(i%2?-1:1);});
            group.rotation.x = -.12 + Math.sin(elapsed * .16) * .06 + pointer.y * .08;
            const thinking=processState.status==='analyzing';
            const breath = 1 + Math.sin(elapsed * (thinking?3.8:1.1)) * (thinking?.045:.018) * energy; points.scale.setScalar(breath);
            pointMat.size = .063 + energy * .043;
            if(!inStudio){const position=pointGeo.attributes.position;for(let i=0;i<position.array.length;i+=3){const wave=1+.045*Math.sin(elapsed*1.4+baseVertices[i+1]*4+i*.011);position.array[i]=baseVertices[i]*wave;position.array[i+2]=baseVertices[i+2]*wave;}position.needsUpdate=true;}
            panelGroup.position.y = paused ? 0 : Math.sin(elapsed * .55) * .045;
            panelGroup.visible = !document.querySelector('#control-dashboard');
            panels.forEach((panel, i) => { panel.material.opacity = i === shot ? 1 : .72; });
            pulses.forEach(pulse => { const i = pulse.userData.path; pulse.visible=!inStudio&&(i>1?processState.complete:processState.hasSources); const progress = (elapsed * (.06 + energy * (thinking?.3:.13)) + pulse.userData.offset) % 1; pulse.position.copy(paths[i].getPoint(i > 1 ? 1-progress : progress)); });
            camera.position.x += ((inStudio?3.2:0)+pointer.x*.35-camera.position.x)*.07;
            camera.position.y += ((inStudio?5.2:.5)-camera.position.y)*.07;
            camera.position.z += ((inStudio?Math.max(10.5,7/camera.aspect):neuralDistance)-camera.position.z)*.07;
            camera.lookAt(0, inStudio?-.6:.12, 0); renderer.render(scene, camera);
        };
        resize = new ResizeObserver(() => {
            const w = host.clientWidth, h = host.clientHeight;
            if (!w || !h) return;
            renderer.setSize(w, h); camera.aspect = w / h;
            neuralDistance=document.querySelector('#control-dashboard') ? Math.max(7.9, 5.1 / camera.aspect) : Math.max(11.7, 7.7 / camera.aspect);
            camera.position.z=sceneView==='studio'?Math.max(10.5,7/camera.aspect):neuralDistance;
            camera.updateProjectionMatrix(); render();
        }); resize.observe(host);
        host.dataset.engine = 'webgl'; hero.dataset.ready = 'true'; render(); requestFrame();
        window.addEventListener('pagehide', event => {
            if (event.persisted) return;
            disposed = true; cancelAnimationFrame(raf); visibility.disconnect(); resize.disconnect();
            resources.forEach(resource => resource.dispose()); renderer.dispose();
        });
    } catch (error) { fallback(); console.warn('Technology visualization fallback:', error.message); }
})();
