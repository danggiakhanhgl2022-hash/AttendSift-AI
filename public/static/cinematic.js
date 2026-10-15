/* Procedural scene: no remote assets, no business API calls, no form navigation. */
(() => {
    'use strict';
    const hero = document.querySelector('.intro');
    const host = hero.querySelector('.cinematic-viewport');
    const toggle = hero.querySelector('.cinematic-toggle');
    const systemMotion = matchMedia('(prefers-reduced-motion: reduce)');
    // This workspace explicitly requests automatic cinematic motion. The pause
    // button remains available, even when Windows disables system animations.
    const motion = { get matches() { return document.documentElement.dataset.motionPolicy !== 'full' && systemMotion.matches; } };
    const keys = ['sync', 'export', 'history', 'settings'];
    const dots = [...hero.querySelectorAll('.cinematic-dot')];
    let shot = 0, paused = motion.matches, visible = true, heldShot = false;
    let renderScene = null;
    function updateCopy(index) {
        hero.dataset.shot = keys[index];
        dots.forEach((dot, i) => dot.setAttribute('aria-pressed', String(i === index)));
    }
    function syncToggle() {
        toggle.textContent = paused ? '▶ Tiếp tục' : 'Ⅱ Tạm dừng';
        toggle.setAttribute('aria-pressed', String(paused));
        toggle.setAttribute('aria-label', paused ? 'Tiếp tục cảnh chuyển động' : 'Tạm dừng cảnh chuyển động');
        hero.dataset.playing = String(!paused);
        document.documentElement.dataset.motion = paused ? 'paused' : 'running';
        if (renderScene) renderScene.invalidate();
    }
    function goTo(key, hold = true) {
        const index = keys.indexOf(key);
        if (index < 0) return;
        shot = index;
        heldShot = hold;
        updateCopy(shot);
        if (renderScene) renderScene.goTo(shot, motion.matches);
    }
    window.CinematicScene = { goTo, getState: () => ({ shot: keys[shot], paused, heldShot, ready: hero.dataset.ready === 'true', ...(renderScene ? renderScene.state() : {}) }) };
    toggle.addEventListener('click', () => { paused = !paused; if (paused && renderScene) renderScene.pause(); syncToggle(); });
    dots.forEach((dot, i) => dot.addEventListener('click', () => goTo(keys[i])));
    systemMotion.addEventListener('change', () => { if (document.documentElement.dataset.motionPolicy === 'full') return; paused = motion.matches; syncToggle(); if (renderScene) renderScene.goTo(shot, motion.matches); });
    syncToggle();
    updateCopy(0);
    const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; }, { threshold: .01 });
    observer.observe(hero);
    try {
        if (!window.THREE) throw new Error('3D library unavailable');
        const T = window.THREE;
        const renderer = new T.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
        renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
        renderer.outputColorSpace = T.SRGBColorSpace;
        renderer.toneMapping = T.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.02;
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = T.PCFSoftShadowMap;
        host.append(renderer.domElement);
        renderer.domElement.setAttribute('aria-hidden', 'true');
        // A final film pass grades the entire 3D scene consistently. Highlights
        // bloom softly; dark regions retain blue detail instead of grey wash.
        const filmTarget=new T.WebGLRenderTarget(1,1,{type:T.HalfFloatType});
        filmTarget.samples=4;
        const filmScene=new T.Scene(),filmCamera=new T.OrthographicCamera(-1,1,1,-1,0,1);
        const filmMaterial=new T.ShaderMaterial({
            uniforms:{image:{value:filmTarget.texture},pixel:{value:new T.Vector2(1,1)},roundFrame:{value:0},frameAspect:{value:1}},
            vertexShader:'varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',
            fragmentShader:`uniform sampler2D image;uniform vec2 pixel;uniform float roundFrame;uniform float frameAspect;varying vec2 vUv;
                void main(){
                    vec3 c=texture2D(image,vUv).rgb;
                    vec3 glow=vec3(0.);
                    for(int x=-2;x<=2;x++)for(int y=-2;y<=2;y++){
                        vec3 s=texture2D(image,vUv+vec2(float(x),float(y))*pixel*3.).rgb;
                        glow+=max(s-vec3(1.15),vec3(0.))/25.;
                    }
                    c=c*.78+glow*.22;
                    float l=dot(c,vec3(.2126,.7152,.0722));
                    c=mix(vec3(l),c,.86);
                    c*=mix(vec3(.76,.94,1.08),vec3(1.04,1.02,.99),smoothstep(.08,.8,l));
                    vec2 q=(vUv-.5)*vec2(1.,.8);
                    c*=1.-smoothstep(.18,.66,length(q))*.32;
                    vec2 corner=abs((vUv-.5)*vec2(frameAspect,1.))-vec2(frameAspect*.5-.055,.445);
                    float edge=length(max(corner,vec2(0.)))-.055;
                    float alpha=mix(1.,1.-smoothstep(-.002,.002,edge),roundFrame);
                    gl_FragColor=vec4(c,alpha);
                    #include <tonemapping_fragment>
                    #include <colorspace_fragment>
                }`,depthTest:false,depthWrite:false,transparent:true
        });
        filmScene.add(new T.Mesh(new T.PlaneGeometry(2,2),filmMaterial));
        function drawFilm(){
            const size=renderer.getSize(new T.Vector2());
            // Render the environment around the floating inner shot with the
            // same WebGL canvas. The outer region is geometry, not a blurred copy.
            const framed=window.innerWidth>700;
            if(framed){
                car.visible=false;reflection.visible=false;environmentFill.visible=true;skyDome.material.color.setScalar(1.7);
                environmentCamera.position.x=-6.5+Math.sin(time*.08)*.28;
                environmentCamera.lookAt(0,1.8,0);
                environmentCamera.aspect=host.clientWidth/host.clientHeight;environmentCamera.updateProjectionMatrix();
                renderer.setRenderTarget(filmTarget);renderer.render(scene,environmentCamera);
                renderer.setRenderTarget(null);renderer.setViewport(0,0,size.x,size.y);renderer.render(filmScene,filmCamera);
                car.visible=true;reflection.visible=true;environmentFill.visible=false;skyDome.material.color.setScalar(1);
            }
            renderer.setRenderTarget(filmTarget);renderer.render(scene,camera);renderer.setRenderTarget(null);
            if(framed){
                const x=Math.round(size.x*.03),y=Math.round(size.y*.22),w=Math.round(size.x*.94),h=Math.round(size.y*.56);
                filmMaterial.uniforms.roundFrame.value=1;filmMaterial.uniforms.frameAspect.value=w/h;renderer.autoClear=false;
                renderer.setViewport(x,y,w,h);renderer.setScissor(x,y,w,h);renderer.setScissorTest(true);
            }
            renderer.render(filmScene,filmCamera);renderer.autoClear=true;filmMaterial.uniforms.roundFrame.value=0;renderer.setScissorTest(false);renderer.setViewport(0,0,size.x,size.y);
        }
        const scene = new T.Scene();
        scene.fog = new T.FogExp2(0x07121d, .065);
        const camera = new T.PerspectiveCamera(43, 1, .1, 100);
        // A complete sky dome fills every camera angle; its horizon blends into
        // the ground instead of leaving a flat empty rectangle above the car.
        const environmentCamera=new T.PerspectiveCamera(48,1,.1,100);
        environmentCamera.position.set(-6.5,2.2,8.5);environmentCamera.lookAt(0,1.8,0);
        const skyCanvas=document.createElement('canvas');skyCanvas.width=1024;skyCanvas.height=512;
        const skyContext=skyCanvas.getContext('2d');
        const skyBase=skyContext.createLinearGradient(0,0,0,512);
        [[0,'#01040a'],[.32,'#071322'],[.48,'#203b50'],[.62,'#102536'],[.78,'#08131f'],[1,'#03080e']].forEach(([p,c])=>skyBase.addColorStop(p,c));
        skyContext.fillStyle=skyBase;skyContext.fillRect(0,0,1024,512);
        skyContext.filter='blur(18px)';
        for(let i=0;i<80;i++) {
            const x=(i*137.53)%1024,y=145+(Math.sin(i*3.17)+1)*45,r=35+(i%7)*12;
            const g=skyContext.createRadialGradient(x,y,0,x,y,r);
            g.addColorStop(0,i%3===0?'rgba(134,177,208,.13)':'rgba(1,5,12,.4)');g.addColorStop(1,'rgba(0,0,0,0)');
            skyContext.fillStyle=g;skyContext.fillRect(0,0,1024,512);
        }
        skyContext.filter='none';
        const skyTexture=new T.CanvasTexture(skyCanvas);skyTexture.colorSpace=T.SRGBColorSpace;
        const skyDome=new T.Mesh(new T.SphereGeometry(45,48,24),new T.MeshBasicMaterial({map:skyTexture,side:T.BackSide,fog:false,depthWrite:false}));
        skyDome.renderOrder=-10;scene.add(skyDome);
        const envCanvas = document.createElement('canvas');
        envCanvas.width = 512; envCanvas.height = 256;
        const ec = envCanvas.getContext('2d');
        const sky = ec.createLinearGradient(0, 0, 0, 256);
        [[0, '#111c2c'], [.25, '#03070d'], [.39, '#121d2a'], [.44, '#edf4f8'], [.47, '#344557'], [.53, '#060b13'], [.74, '#243449'], [1, '#02040a']].forEach(([p, c]) => sky.addColorStop(p, c));
        ec.fillStyle = sky; ec.fillRect(0, 0, 512, 256);
        ec.fillStyle = '#f1f5f8'; ec.fillRect(40, 28, 24, 120); ec.fillRect(280, 18, 12, 130);
        ec.fillStyle = '#748ea9'; ec.fillRect(380, 65, 70, 12);
        const environment = new T.CanvasTexture(envCanvas);
        environment.mapping = T.EquirectangularReflectionMapping;
        environment.colorSpace = T.SRGBColorSpace;
        const pmrem = new T.PMREMGenerator(renderer);
        scene.environment = pmrem.fromEquirectangular(environment).texture;
        pmrem.dispose(); environment.dispose();
        scene.add(new T.HemisphereLight(0x9db9d3, 0x010205, .18));
        const environmentFill=new T.DirectionalLight(0x97b8d4,1.8);
        environmentFill.position.set(-5,3,5);environmentFill.visible=false;scene.add(environmentFill);
        const moon = new T.DirectionalLight(0xf5f5f2, 2.1);
        moon.position.set(-3, 8, 5); moon.castShadow = true;
        moon.shadow.mapSize.set(1024, 1024);
        Object.assign(moon.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8 });
        moon.shadow.bias = -.001;
        scene.add(moon);
        const rim = new T.DirectionalLight(0x78aaca, 1.5);
        rim.position.set(5, 4, -6); scene.add(rim);
        const softbox=new T.DirectionalLight(0xffffff,.65);
        softbox.position.set(-5,3,-2);scene.add(softbox);
        const studioKey=new T.SpotLight(0xf2f6ff,26,20,.48,1,1.4);
        studioKey.position.set(-3,5,4);studioKey.target.position.set(0,.8,0);scene.add(studioKey,studioKey.target);
        // Fine anisotropic-looking grain is baked locally, with no texture download.
        const metalCanvas=document.createElement('canvas');metalCanvas.width=512;metalCanvas.height=256;
        const metalContext=metalCanvas.getContext('2d');metalContext.fillStyle='#c5c9ce';metalContext.fillRect(0,0,512,256);
        for(let i=0;i<256;i++) {
            const shade=180+Math.round((Math.sin(i*13.17)+1)*22);
            metalContext.strokeStyle=`rgba(${shade},${shade},${shade},.2)`;
            metalContext.beginPath();metalContext.moveTo(0,i+.5);metalContext.lineTo(512,i+.5);metalContext.stroke();
        }
        const brushedMetal=new T.CanvasTexture(metalCanvas);brushedMetal.colorSpace=T.SRGBColorSpace;
        brushedMetal.wrapS=brushedMetal.wrapT=T.RepeatWrapping;brushedMetal.repeat.set(2,2);
        const silver = new T.MeshPhysicalMaterial({ color: 0xc5cdd4, map:brushedMetal, metalness: .85, roughness: .21, envMapIntensity: 2.7, clearcoat: .22, clearcoatRoughness: .24 });
        const dark = new T.MeshStandardMaterial({ color: 0x070b10, metalness: .4, roughness: .56 });
        const glass = new T.MeshPhysicalMaterial({ color: 0x020812, metalness: .72, roughness: .055, envMapIntensity: 1.35, clearcoat: 1, clearcoatRoughness:.06 });
        const brakeSteel=new T.MeshStandardMaterial({color:0x48535e,metalness:.8,roughness:.42});
        const rubber = new T.MeshStandardMaterial({ color: 0x050709, roughness: .92 });
        const car = new T.Group(); scene.add(car);
        function mesh(geometry, material, parent = car) {
            const result = new T.Mesh(geometry, material); result.castShadow = true; result.receiveShadow = true; parent.add(result); return result;
        }
        function box(size, position, material, parent = car) {
            const item = mesh(new T.BoxGeometry(...size), material, parent); item.position.set(...position); return item;
        }
        function panel(points, material, parent = car) {
            const geometry = new T.BufferGeometry();
            const data = [];
            for (let i = 1; i < points.length - 1; i++) data.push(...points[0], ...points[i], ...points[i + 1]);
            geometry.setAttribute('position', new T.Float32BufferAttribute(data, 3)); geometry.computeVertexNormals();
            const m = material.clone(); m.side = T.DoubleSide;
            return mesh(geometry, m, parent);
        }
        const shape = new T.Shape();
        [[-2.65,.72],[-2.58,1.02],[-1.75,1.22],[-.35,1.95],[2.55,1.28],[2.62,.66],[2.30,.48]].forEach(([x,y], i) => i ? shape.lineTo(x,y) : shape.moveTo(x,y));
        // Actual wheel openings, not wheels pasted over a solid body slab.
        shape.lineTo(2.27,.48);shape.absarc(1.72,.52,.55,-.073,Math.PI+.073,false);
        shape.lineTo(-1.13,.48);shape.absarc(-1.68,.52,.55,-.073,Math.PI+.073,false);
        shape.lineTo(-2.25,.48);
        shape.closePath();
        const body = new T.ExtrudeGeometry(shape, { depth: 1.87, bevelEnabled: true, bevelThickness: .035, bevelSize: .035, bevelSegments: 6, steps: 1 }); body.translate(0,0,-.935);
        mesh(body, silver);
        const seamMaterial=new T.LineBasicMaterial({color:0x273442,transparent:true,opacity:.55});
        for(const side of [-1,1]) {
            const z=side*1.014;
            for(const x of [-.85,.85,1.88]) {
                const top=x<0?1.53:x<1?1.55:1.31;
                const line=new T.Line(new T.BufferGeometry().setFromPoints([new T.Vector3(x,.62,z),new T.Vector3(x,top,z)]),seamMaterial);car.add(line);
            }
            const belt=new T.Line(new T.BufferGeometry().setFromPoints([new T.Vector3(-1.72,1.23,z),new T.Vector3(2.48,1.23,z)]),seamMaterial);car.add(belt);
        }
        // Flush glass panels and sharp roof lines, rather than a rectangular placeholder.
        panel([[-1.72,1.235,-.87],[-1.72,1.235,.87],[-.35,1.965,.87],[-.35,1.965,-.87]], glass);
        panel([[-.3,1.965,-.86],[-.3,1.965,.86],[.78,1.715,.86],[.78,1.715,-.86]], glass);
        for (const side of [-1,1]) {
            const z = side * .984;
            panel([[-1.58,1.25,z],[-.31,1.88,z],[.82,1.61,z],[.82,1.25,z]], glass);
            panel([[.88,1.25,z],[.88,1.59,z],[1.85,1.36,z],[1.85,1.25,z]], glass);
            box([.025,.66,.015],[.84,1.14,z*1.002],dark);
            box([.15,.025,.018],[.65,1.19,z*1.005],dark);
            box([.15,.025,.018],[1.65,1.19,z*1.005],dark);
            box([4.75,.16,.08],[0,.48,side*1.015],dark);
            for (const x of [-1.68,1.72]) {
                const fender = new T.MeshStandardMaterial({ color: 0x121b23, roughness: .75 });
                const arch = mesh(new T.TorusGeometry(.535,.07,12,48,Math.PI),fender);
                arch.position.set(x,.57,side*1.02);
                const wheel = mesh(new T.CylinderGeometry(.50,.50,.29,48),rubber);
                wheel.rotation.x = Math.PI/2; wheel.position.set(x,.52,side*1.04);
                const hub = mesh(new T.CylinderGeometry(.34,.34,.315,48),dark);
                hub.rotation.x = Math.PI/2; hub.position.copy(wheel.position);
                const disc=mesh(new T.CylinderGeometry(.285,.285,.018,48),brakeSteel);
                disc.rotation.x=Math.PI/2;disc.position.set(x,.52,side*1.198);
                const tread=new T.InstancedMesh(new T.BoxGeometry(.052,.018,.265),rubber,48);
                const treadTransform=new T.Object3D();
                for(let i=0;i<48;i++) {
                    const a=i*Math.PI*2/48;
                    treadTransform.position.set(x+Math.sin(a)*.5,.52+Math.cos(a)*.5,side*1.04);
                    treadTransform.rotation.set(0,0,-a);treadTransform.updateMatrix();tread.setMatrixAt(i,treadTransform.matrix);
                }
                tread.castShadow=true;tread.receiveShadow=true;car.add(tread);
                const cap = mesh(new T.CylinderGeometry(.12,.12,.325,32),silver);
                cap.rotation.x = Math.PI/2; cap.position.copy(wheel.position);
                const rimRing = mesh(new T.TorusGeometry(.32,.018,10,48), silver);
                rimRing.position.set(x,.52,side*1.207);
                for(let spoke=0;spoke<10;spoke++) {
                    const angle=spoke*Math.PI*2/10;
                    const arm=box([.045,.245,.026],[x+Math.sin(angle)*.20,.52+Math.cos(angle)*.20,side*1.211],silver);
                    arm.rotation.z=-angle;
                }
                const sidewall = mesh(new T.TorusGeometry(.39,.075,8,40),rubber);
                sidewall.position.set(x,.52,side*1.19);
                for(let n=0;n<7;n++) {
                    const a=n*Math.PI*2/7;
                    box([.055,.055,.02],[x+Math.cos(a)*.25,.52+Math.sin(a)*.25,side*1.21],dark);
                }
            }
        }
        // Lower intake, LED modules and mirrors give the silhouette readable detail.
        for(const side of [-1,1]) {
            const mirror=mesh(new T.SphereGeometry(1,20,12),silver);
            mirror.scale.set(.17,.065,.13);mirror.position.set(-1.02,1.32,side*1.14);
            box([.28,.015,.024],[-.92,1.16,side*.998],silver);
            box([.11,.055,.30],[-2.655,.83,side*.66],new T.MeshBasicMaterial({color:0xd5eaff}));
        }
        box([.12,.18,1.94],[-2.62,.63,0],dark);
        box([.12,.20,1.94],[2.62,.58,0],dark);
        const white = new T.MeshBasicMaterial({ color: 0xe2f6ff });
        const red = new T.MeshBasicMaterial({ color: 0xff1836 });
        box([.025,.035,1.84],[-2.66,1.01,0],white);
        box([.03,.045,1.85],[2.615,1.225,0],red);
        const glowCanvas=document.createElement('canvas');glowCanvas.width=64;glowCanvas.height=64;
        const gc=glowCanvas.getContext('2d'), glowGradient=gc.createRadialGradient(32,32,0,32,32,32);
        glowGradient.addColorStop(0,'rgba(255,255,255,1)');glowGradient.addColorStop(.12,'rgba(255,255,255,.6)');glowGradient.addColorStop(1,'rgba(255,255,255,0)');
        gc.fillStyle=glowGradient;gc.fillRect(0,0,64,64);
        const glowTexture=new T.CanvasTexture(glowCanvas);
        for(const z of [-.75,.75]) {
            for(const rear of [false,true]) {
                const glow=new T.Sprite(new T.SpriteMaterial({map:glowTexture,color:rear?0xff1232:0xc8ebff,transparent:true,opacity:.55,depthWrite:false,blending:T.AdditiveBlending}));
                glow.position.set(rear?2.65:-2.69,rear?1.225:1.01,z);glow.scale.set(.75,.22,1);car.add(glow);
            }
        }
        const bedMaterial=new T.MeshStandardMaterial({color:0x04090e,metalness:.45,roughness:.38});
        panel([[.84,1.717,-.87],[.84,1.717,.87],[2.48,1.337,.87],[2.48,1.337,-.87]],bedMaterial);
        for(let i=0;i<14;i++) {
            const x=.9+i*.112,y=1.718-(x-.84)*.232;
            const slat=box([.018,.012,1.72],[x,y,0],dark);slat.rotation.z=-.228;
        }
        for (const z of [-.7,.7]) {
            const light = new T.SpotLight(0xd4e5ef, 1.6, 12, .3, 1, 1);
            light.position.set(-2.68, .95, z); light.target.position.set(-10,.15,z*1.6);
            scene.add(light,light.target);
        }
        const tail = new T.PointLight(0xff1734, 2.3, 5); tail.position.set(2.8,1.1,0); scene.add(tail);
        // Keep the studio key on the vehicle, rather than bleaching the floor.
        car.traverse(object=>object.layers.enable(1));studioKey.layers.set(1);
        const surfaceCanvas=document.createElement('canvas');surfaceCanvas.width=256;surfaceCanvas.height=256;
        const surfaceContext=surfaceCanvas.getContext('2d'),surfacePixels=surfaceContext.createImageData(256,256);
        for(let y=0;y<256;y++)for(let x=0;x<256;x++){
            const grain=Math.sin(x*12.9898+y*78.233)*43758.5453;
            const v=110+Math.sin(y*.8+Math.sin(x*.07))*22+(grain-Math.floor(grain))*35;
            const i=(y*256+x)*4;surfacePixels.data[i]=surfacePixels.data[i+1]=surfacePixels.data[i+2]=v;surfacePixels.data[i+3]=255;
        }
        surfaceContext.putImageData(surfacePixels,0,0);
        const groundBump=new T.CanvasTexture(surfaceCanvas);groundBump.wrapS=groundBump.wrapT=T.RepeatWrapping;groundBump.repeat.set(60,60);
        // Variation in wetness breaks the broad, uniform pool of blue glare.
        const wetCanvas=document.createElement('canvas');wetCanvas.width=128;wetCanvas.height=128;
        const wc=wetCanvas.getContext('2d'),wetPixels=wc.createImageData(128,128);
        for(let y=0;y<128;y++)for(let x=0;x<128;x++) {
            const value=190+Math.sin(x*.09+Math.sin(y*.13))*Math.cos(y*.07)*40;
            const i=(y*128+x)*4;wetPixels.data[i]=wetPixels.data[i+1]=wetPixels.data[i+2]=value;wetPixels.data[i+3]=255;
        }
        wc.putImageData(wetPixels,0,0);
        const wetness=new T.CanvasTexture(wetCanvas);wetness.wrapS=wetness.wrapT=T.RepeatWrapping;wetness.repeat.set(12,12);
        const ground = mesh(new T.PlaneGeometry(150,150),new T.MeshStandardMaterial({ color: 0x03080e, bumpMap:groundBump,bumpScale:.035, roughnessMap:wetness, metalness: .25, roughness: .9, transparent: true, opacity: .97 }),scene);
        ground.rotation.x=-Math.PI/2; ground.position.y=-.02; ground.castShadow=false;
        // Soft contact shadows anchor the tires and chassis to the wet floor.
        const contactCanvas=document.createElement('canvas');contactCanvas.width=128;contactCanvas.height=128;
        const contactContext=contactCanvas.getContext('2d');
        const contactGradient=contactContext.createRadialGradient(64,64,10,64,64,64);
        contactGradient.addColorStop(0,'rgba(0,0,0,.85)');contactGradient.addColorStop(.55,'rgba(0,0,0,.5)');contactGradient.addColorStop(1,'rgba(0,0,0,0)');
        contactContext.fillStyle=contactGradient;contactContext.fillRect(0,0,128,128);
        const contactTexture=new T.CanvasTexture(contactCanvas);
        const contactMaterial=new T.MeshBasicMaterial({map:contactTexture,transparent:true,depthWrite:false,opacity:.92});
        const chassisShadow=new T.Mesh(new T.PlaneGeometry(5.2,2.4),contactMaterial);
        chassisShadow.rotation.x=-Math.PI/2;chassisShadow.position.y=-.009;scene.add(chassisShadow);
        for(const x of [-1.68,1.72])for(const z of [-1.04,1.04]) {
            const patch=new T.Mesh(new T.PlaneGeometry(1.1,.7),contactMaterial);
            patch.rotation.x=-Math.PI/2;patch.position.set(x,-.006,z);scene.add(patch);
        }
        const reflection = car.clone();
        reflection.scale.y=-1; reflection.position.y=-.06;
        reflection.traverse(item=> { if(item.isMesh) {item.material=item.material.clone();item.material.transparent=true;item.material.opacity=.065;item.material.depthWrite=false;item.castShadow=false;} });
        scene.add(reflection);
        let seed=1649;
        function random() { seed=(seed*1664525+1013904223)>>>0; return seed/4294967296; }
        const rocks = new T.Group(); scene.add(rocks);
        const rockCanvas=document.createElement('canvas');rockCanvas.width=256;rockCanvas.height=256;
        const rockContext=rockCanvas.getContext('2d'),rockPixels=rockContext.createImageData(256,256);
        for(let y=0;y<256;y++)for(let x=0;x<256;x++) {
            const noise=Math.sin(x*127.1+y*311.7)*43758.5453;
            const value=100+Math.sin(x*.11)*Math.cos(y*.17)*28+(noise-Math.floor(noise))*65;
            const n=(y*256+x)*4;rockPixels.data[n]=rockPixels.data[n+1]=rockPixels.data[n+2]=value;rockPixels.data[n+3]=255;
        }
        rockContext.putImageData(rockPixels,0,0);
        const rockBump=new T.CanvasTexture(rockCanvas);rockBump.wrapS=rockBump.wrapT=T.RepeatWrapping;rockBump.repeat.set(2,2);
        const rockMaterial = new T.MeshStandardMaterial({ color: 0x242831, roughness: .92, metalness: .025,bumpMap:rockBump,bumpScale:.09 });
        for(let i=0;i<15;i++) {
            const geometry = new T.SphereGeometry(.4+random()*.7,32,24);
            const vertices = geometry.attributes.position;
            for(let n=0;n<vertices.count;n++) {
                const x=vertices.getX(n),y=vertices.getY(n),z=vertices.getZ(n);
                const scale=1+.19*Math.sin(x*7+y*4)*Math.cos(z*9)+.06*Math.sin(y*19+z*13);
                vertices.setXYZ(n,x*scale,y*scale,z*scale);
            }
            geometry.computeVertexNormals();
            const rock=mesh(geometry,rockMaterial,rocks);
            const angle=random()*Math.PI*2, radius=5.5+random()*8;
            rock.position.set(Math.cos(angle)*radius,-.2+random()*.3,Math.sin(angle)*radius);
            rock.scale.set(1+random(),.6+random()*1.8,1+random()); rock.rotation.set(random()*2,random()*3,random());
        }
        const mountainMaterial=new T.MeshStandardMaterial({color:0x385367,roughness:.96,emissive:0x102030,emissiveIntensity:.12});
        for(let i=0;i<16;i++) {
            const angle=i*Math.PI*2/16;
            const mountain=mesh(new T.SphereGeometry(1,24,18),mountainMaterial,scene);
            const v=mountain.geometry.attributes.position;
            for(let n=0;n<v.count;n++) {
                const x=v.getX(n),y=v.getY(n),z=v.getZ(n),warp=1+.17*Math.sin(x*12+z*7)*Math.cos(y*10);
                v.setXYZ(n,x*warp,y*warp,z*warp);
            }
            mountain.geometry.computeVertexNormals();mountain.position.set(Math.cos(angle)*19,-.3,Math.sin(angle)*19);
            mountain.scale.set(3+random()*3, .8+random()*1.3,3+random()*3);mountain.castShadow=false;
        }
        for(const [x,z,size] of [[-4.3,2.9,.95],[3.8,3.4,1.1],[-3.7,-3.6,.8],[4.2,-3.3,.9]]) {
            const stone=mesh(new T.SphereGeometry(size,28,20),rockMaterial,scene);
            const v=stone.geometry.attributes.position;
            for(let n=0;n<v.count;n++) {
                const x=v.getX(n),y=v.getY(n),z=v.getZ(n),warp=1+.2*Math.sin(x*7+y*5)*Math.cos(z*8);
                // Broad fracture faces give rocks a silhouette unlike rounded pebbles.
                const cut=1-.14*Math.max(0,Math.sin(x*3+z*2));
                v.setXYZ(n,x*warp*cut,Math.min(y*warp,size*.7),z*warp);
            }
            stone.geometry.computeVertexNormals();stone.position.set(x,-.12,z);stone.scale.set(.9,.62,.85);
        }
        const fogCanvas=document.createElement('canvas');fogCanvas.width=256;fogCanvas.height=128;
        const fc=fogCanvas.getContext('2d');
        for(let i=0;i<32;i++) {
            const x=random()*256,y=40+random()*55,r=15+random()*40,g=fc.createRadialGradient(x,y,0,x,y,r);
            g.addColorStop(0,'rgba(175,209,231,.16)');g.addColorStop(1,'rgba(175,209,231,0)');fc.fillStyle=g;fc.fillRect(0,0,256,128);
        }
        // Fade every edge of the cloud atlas; otherwise transparent planes
        // reveal rectangular borders when several layers overlap.
        fc.save();fc.globalCompositeOperation='destination-in';
        fc.translate(128,64);fc.scale(1,.5);
        const fogMask=fc.createRadialGradient(0,0,12,0,0,128);
        fogMask.addColorStop(0,'rgba(255,255,255,1)');fogMask.addColorStop(.5,'rgba(255,255,255,.8)');fogMask.addColorStop(1,'rgba(255,255,255,0)');
        fc.fillStyle=fogMask;fc.fillRect(-128,-128,256,256);fc.restore();
        const fogTexture=new T.CanvasTexture(fogCanvas);
        const skyClouds=[];
        for(let i=0;i<12;i++) {
            const angle=i*Math.PI*2/12;
            const cloud=new T.Sprite(new T.SpriteMaterial({map:fogTexture,color:0x96b9d1,transparent:true,opacity:.45,depthWrite:false,fog:true}));
            cloud.position.set(Math.cos(angle)*15,4+(i%3)*1.2,Math.sin(angle)*15);cloud.scale.set(14,5,1);
            cloud.userData={angle,y:cloud.position.y};scene.add(cloud);skyClouds.push(cloud);
        }
        const fogPlanes=[];
        for(let i=0;i<8;i++) {
            const plane=mesh(new T.PlaneGeometry(16,4),new T.MeshBasicMaterial({map:fogTexture,transparent:true,opacity:.28+i*.025,depthWrite:false,side:T.DoubleSide,color:0x9cbad1}),scene);
            plane.position.set(i-2,.25+i*.10,-3+i*1.4);plane.rotation.x=-Math.PI*.2;plane.castShadow=false;fogPlanes.push(plane);
        }
        const beamMaterial=new T.MeshBasicMaterial({map:fogTexture,color:0xc0e5ff,transparent:true,opacity:.14,depthWrite:false,blending:T.AdditiveBlending,side:T.DoubleSide});
        for(const z of [-.7,.7]) {
            const beam=mesh(new T.PlaneGeometry(7,2.7),beamMaterial,scene);
            beam.rotation.x=-Math.PI/2;beam.position.set(-5.8,.3,z);beam.castShadow=false;
        }
        // Billboards drift through world space, so smoke occludes foreground
        // rocks and catches the headlamp glow rather than moving as a flat overlay.
        const smoke = [];
        for(let i=0;i<34;i++) {
            const material=new T.SpriteMaterial({map:fogTexture,color:i%3===0?0xadcfe3:0x688da9,transparent:true,opacity:.2,depthWrite:false});
            const puff=new T.Sprite(material);
            const x=-7+random()*14,z=-5+random()*10,scale=2+random()*3;
            puff.position.set(x,.3+random()*.8,z);puff.scale.set(scale,scale*.58,1);
            puff.userData={x,z,scale,phase:random()*Math.PI*2};scene.add(puff);smoke.push(puff);
        }
        const storm = new T.Group();scene.add(storm);
        const lightning=new T.Group();storm.add(lightning);
        const boltMaterial=new T.LineBasicMaterial({color:0xd3edff,transparent:true,opacity:0,blending:T.AdditiveBlending,depthWrite:false});
        const boltPoints=[];
        for(let i=0;i<12;i++) boltPoints.push(new T.Vector3(4+Math.sin(i*2.3)*.45,9-i*.65,-8));
        lightning.add(new T.Line(new T.BufferGeometry().setFromPoints(boltPoints),boltMaterial));
        for(const branch of [3,6]) {
            const points=[boltPoints[branch].clone()];
            for(let i=1;i<5;i++)points.push(new T.Vector3(4+i*.36+Math.sin(i*3)*.12,boltPoints[branch].y-i*.42,-8));
            lightning.add(new T.Line(new T.BufferGeometry().setFromPoints(points),boltMaterial));
        }
        const stormLight=new T.PointLight(0xbedfff,0,45,1.2);stormLight.position.set(3,7,-6);scene.add(stormLight);
        const cloudGlow=new T.Sprite(new T.SpriteMaterial({map:glowTexture,color:0x83b9ef,transparent:true,opacity:0,depthWrite:false,blending:T.AdditiveBlending}));
        cloudGlow.position.set(4,5,-9);cloudGlow.scale.set(14,9,1);scene.add(cloudGlow);
        const underglow=new T.PointLight(0x5aaaff,.12,4,2);underglow.position.set(0,.25,0);scene.add(underglow);
        // The beams share the smoke texture: soft edges, visible only in mist.
        const headlightMist=[];
        for(const z of [-.72,.72]) {
            const plume=new T.Sprite(new T.SpriteMaterial({map:fogTexture,color:0xdde7ef,transparent:true,opacity:.13,depthWrite:false,blending:T.AdditiveBlending}));
            plume.position.set(-5.4,.42,z);plume.scale.set(6,1.05,1);scene.add(plume);headlightMist.push(plume);
        }
        const poses=[
            {p:[-1.8,1.65,8.2],target:[0,.9,0],fov:38,key:23,moon:1.2,rim:1.7},
            {p:[-4.2,3.1,4.9],target:[-.65,1.05,0],fov:43,key:32,moon:1.3,rim:1.1},
            {p:[4.8,3.15,4.3],target:[.65,1.02,0],fov:43,key:9,moon:.75,rim:1.8},
            {p:[-5.7,1.9,4.1],target:[-.75,1.0,0],fov:46,key:30,moon:1.0,rim:2}
        ];
        const target=new T.Vector3(...poses[0].target);
        camera.position.set(...poses[0].p);camera.lookAt(target);
        let transition=null, age=0, time=0, last=performance.now(), pointer={x:0,y:0}, raf=0, dirty=true;
        const holds=[5,4.5,5.5,7];
        renderScene={goTo(index,instant=false) {
            age=0;dirty=true;
            const pose=poses[index];
            if(instant) { camera.position.set(...pose.p);target.set(...pose.target);camera.fov=pose.fov;transition=null; }
            else transition={start:time,duration:2.15,from:camera.position.clone(),to:new T.Vector3(...pose.p),targetFrom:target.clone(),targetTo:new T.Vector3(...pose.target),fovFrom:camera.fov,fovTo:pose.fov};
        }, pause() {transition=null;dirty=true;}, invalidate() {dirty=true;}, state() {return {camera:camera.position.toArray(),time,transitioning:!!transition,visible};}};
        function resize() {
            const {width,height}=host.getBoundingClientRect();
            renderer.setSize(width,height,false);
            const pixels=renderer.getDrawingBufferSize(new T.Vector2());filmTarget.setSize(pixels.x,pixels.y);filmMaterial.uniforms.pixel.value.set(1/pixels.x,1/pixels.y);camera.aspect=(window.innerWidth>700?width*.94/Math.max(height*.56,1):width/Math.max(height,1));camera.updateProjectionMatrix();
            dirty=true;
        }
        const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(host);resize();
        hero.addEventListener('pointermove',event=> {
            if(event.pointerType==='touch'||motion.matches)return;
            const bounds=hero.getBoundingClientRect();pointer.x=((event.clientX-bounds.left)/bounds.width-.5)*2;pointer.y=((event.clientY-bounds.top)/bounds.height-.5)*2;
        });
        hero.addEventListener('pointerleave',()=>{pointer.x=0;pointer.y=0;});
        const position=new T.Vector3();
        function frame(now) {
            raf=requestAnimationFrame(frame);
            const dt=Math.min((now-last)/1000,.25);last=now;
            if(document.hidden||!visible)return;
            const moving=!paused||transition;
            if (!moving && !dirty) return;
            dirty=false;
            if(moving)time+=dt;
            if(!paused)age+=dt;
            if(age>=holds[shot]&&!motion.matches&&!heldShot)goTo(keys[(shot+1)%4],false);
            if(transition) {
                let t=Math.min((time-transition.start)/transition.duration,1);t=t*t*t*(t*(t*6-15)+10);
                camera.position.lerpVectors(transition.from,transition.to,t);target.lerpVectors(transition.targetFrom,transition.targetTo,t);camera.fov=T.MathUtils.lerp(transition.fovFrom,transition.fovTo,t);
                if(t>=1)transition=null;
            }
            position.copy(camera.position);
            if(camera.aspect<1.05)camera.position.sub(target).multiplyScalar(1.05/camera.aspect).add(target);
            if(!paused&&!motion.matches) {camera.position.x+=Math.sin(time*.25)*.48+pointer.x*.20;camera.position.y+=Math.sin(time*.32)*.12-pointer.y*.10;}
            const lens=camera.fov;
            if(!paused&&!motion.matches)camera.fov=lens+Math.sin(time*.25)*1.25;
            camera.lookAt(target);camera.updateProjectionMatrix();
            fogPlanes.forEach((plane,i)=> {plane.position.x=Math.sin(time*.18+i)*1.8;
                plane.material.opacity=(i<3?.11:.028)+Math.sin(time*.35+i)*.012;});
            headlightMist.forEach((plume,i)=> {
                plume.material.opacity=(shot===2?.025:.12)+Math.sin(time*.5+i)*.015;
                plume.position.y=.4+Math.sin(time*.3+i)*.06;
            });
            skyClouds.forEach((cloud,i)=> {
                const a=cloud.userData.angle+Math.sin(time*.045)*.1;
                cloud.position.x=Math.cos(a)*15;cloud.position.z=Math.sin(a)*15;
                cloud.position.y=cloud.userData.y+Math.sin(time*.15+i)*.25;
                cloud.material.opacity=.34+Math.sin(time*.2+i)*.1;
            });
            smoke.forEach(puff=> {
                const d=puff.userData,phase=time*.32+d.phase;
                puff.position.x=d.x+Math.sin(phase)*2;
                puff.position.y=.55+Math.sin(phase*.7)*.3;
                puff.position.z=d.z+Math.cos(phase*.6)*.6;
                puff.material.opacity=(d.z<0?.065:.015)+(Math.sin(phase)+1)*.025;
                puff.material.rotation=Math.sin(phase*.4)*.22;
                puff.scale.set(d.scale*(1+Math.sin(phase)*.12),d.scale*.58,1);
            });
            // One distant storm event per 11 seconds, with a restrained second
            // pulse; no rapid strobe and no full-screen white flash.
            const stormPhase=time%11;
            const flash=Math.max(0,1-Math.abs(stormPhase-4.8)/.35)*.8+Math.max(0,1-Math.abs(stormPhase-5.6)/.45)*.45;
            // Each shot has its own lighting hierarchy; the rear shot gives
            // priority to the red strip instead of illuminating every panel.
            const lighting=poses[shot],lightEase=Math.min(dt*1.5,1);
            studioKey.intensity+=(lighting.key-studioKey.intensity)*lightEase;
            moon.intensity+=(lighting.moon-moon.intensity)*lightEase;
            rim.intensity+=(lighting.rim-rim.intensity)*lightEase;
            boltMaterial.opacity=flash;stormLight.intensity=flash*5;cloudGlow.material.opacity=flash*.22;
            hero.style.setProperty('--storm-flash',String(flash*.18));
            rocks.rotation.y=Math.sin(time*.08)*.018;
            tail.intensity=shot===2?5.2+Math.sin(time*1.4)*.7:1.1;
            const progress=heldShot?(Math.sin(time*.3)*.5+.5):Math.min(age/holds[shot],1);
            hero.style.setProperty('--scene-progress',`${progress*100}%`);
            drawFilm();camera.position.copy(position);camera.fov=lens;
        }
        drawFilm();
        hero.dataset.ready='true';
        host.dataset.engine='webgl';
        raf=requestAnimationFrame(frame);
        window.addEventListener('pagehide',()=>{cancelAnimationFrame(raf);observer.disconnect();resizeObserver.disconnect();filmTarget.dispose();filmMaterial.dispose();renderer.dispose();},{once:true});
    } catch(error) {
        hero.dataset.ready='fallback';
        host.classList.add('cinematic-fallback');
        console.warn('Cinematic scene uses static fallback:',error.message);
    }
})();
