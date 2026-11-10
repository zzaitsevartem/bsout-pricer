'use client';

import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import type { Group, Mesh, Object3D, WebGLRenderer } from 'three';

type Pose = 'hero' | 'calm' | 'pointing' | 'presenting';

/** A real articulated glTF rabbit. The head is a separate object; the body never follows the pointer. */
export function GuestMascot({ pose, className = '', mirrored = false }: { pose: Pose; className?: string; mirrored?: boolean }) {
  const root = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [blinking, setBlinking] = useState(false);

  useEffect(() => {
    const node = root.current;
    if (!node || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), { rootMargin: '80px' });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || !root.current) return;
    const container = root.current;
    const section = container.closest('section');
    if (!section) return;
    let cancelled = false;
    let renderer: WebGLRenderer | undefined;
    let sceneModel: Group | undefined;
    let head: Object3D | undefined;
    let animationFrame = 0;
    let blinkTimer: ReturnType<typeof setTimeout>;
    let reopenTimer: ReturnType<typeof setTimeout>;
    let resizeObserver: ResizeObserver | undefined;
    let aimX = 0;
    let aimY = 0;
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)');
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
    const eyelids: Object3D[] = [];
    const openEyes: Object3D[] = [];
    const setEyes = (closed: boolean) => {
      for (const part of eyelids) part.visible = closed;
      for (const part of openEyes) part.visible = !closed;
      setBlinking(closed);
    };
    const center = () => { aimX = 0; aimY = 0; };
    const onMove = (event: Event) => {
      const pointer = event as PointerEvent;
      if (!fine.matches || reduce.matches || (pointer.pointerType && pointer.pointerType !== 'mouse')) return;
      const rect = section.getBoundingClientRect();
      aimX = Math.max(-1, Math.min(1, ((pointer.clientX - rect.left) / rect.width - .5) * 2));
      aimY = Math.max(-1, Math.min(1, ((pointer.clientY - rect.top) / rect.height - .5) * 2));
    };
    const blinkLater = () => {
      if (cancelled || document.hidden || reduce.matches) return;
      blinkTimer = setTimeout(() => {
        if (cancelled || document.hidden) return;
        setEyes(true);
        reopenTimer = setTimeout(() => { setEyes(false); blinkLater(); }, 125);
      }, 3000 + Math.random() * 3000);
    };
    const onVisibility = () => {
      clearTimeout(blinkTimer); clearTimeout(reopenTimer);
      setEyes(false); center();
      if (!document.hidden) blinkLater();
    };
    section.addEventListener('pointermove', onMove);
    section.addEventListener('pointerleave', center);
    document.addEventListener('visibilitychange', onVisibility);

    (async () => {
      try {
        const [THREE, { GLTFLoader }] = await Promise.all([import('three'), import('three/addons/loaders/GLTFLoader.js')]);
        if (cancelled) return;
        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.7;
        renderer.domElement.className = 'guest-mascot-canvas';
        renderer.domElement.setAttribute('aria-hidden', 'true');
        container.appendChild(renderer.domElement);
        const scene = new THREE.Scene();
        scene.add(new THREE.HemisphereLight(0xffffff, 0xb8c9bd, 2.5));
        const key = new THREE.DirectionalLight(0xffffff, 2.8); key.position.set(3, 5, 5); scene.add(key);
        const rim = new THREE.DirectionalLight(0xc9ffe2, 1.7); rim.position.set(-3, 4, -2); scene.add(rim);
        const camera = new THREE.PerspectiveCamera(32, 1, .1, 30);
        camera.position.set(mirrored ? -1.5 : 1.5, 2.45, 6.8);
        camera.lookAt(0, 1.58, 0);
        const model = await new GLTFLoader().loadAsync('/redesign/3d/rabbit.glb');
        if (cancelled) { renderer.dispose(); renderer.domElement.remove(); return; }
        sceneModel = model.scene;
        scene.add(sceneModel);
        sceneModel.rotation.y = mirrored ? -.18 : .18;
        const rightArm = sceneModel.getObjectByName('RightArmPivot');
        const leftArm = sceneModel.getObjectByName('LeftArmPivot');
        if (rightArm) rightArm.rotation.z = { hero: 0, calm: -.65, pointing: .28, presenting: .08 }[pose];
        if (leftArm) leftArm.rotation.z = { hero: 0, calm: -.12, pointing: .12, presenting: .1 }[pose];
        head = sceneModel.getObjectByName('HeadPivot');
        sceneModel.traverse((part) => {
          if (part.name.startsWith('ClosedLash')) { part.visible = false; eyelids.push(part); }
          if (/^(Left|Right)(EyeWhite|Iris|Pupil|EyeGlint)$/.test(part.name)) openEyes.push(part);
        });
        const resize = () => {
          if (!renderer) return;
          const width = container.clientWidth;
          const height = container.clientHeight;
          renderer.setSize(width, height, false);
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
        };
        resize();
        resizeObserver = new ResizeObserver(resize);
        resizeObserver.observe(container);
        const tick = () => {
          if (cancelled || !renderer) return;
          if (head) {
            const yaw = reduce.matches || !fine.matches ? 0 : aimX * (mirrored ? -.22 : .22);
            const pitch = reduce.matches || !fine.matches ? 0 : -aimY * .09;
            head.rotation.y += (yaw - head.rotation.y) * .12;
            head.rotation.x += (pitch - head.rotation.x) * .12;
            const displayedYaw = head.rotation.y.toFixed(2);
            if (container.dataset.headYaw !== displayedYaw) container.dataset.headYaw = displayedYaw;
          }
          renderer.render(scene, camera);
          animationFrame = requestAnimationFrame(tick);
        };
        tick();
        setReady(true);
        blinkLater();
      } catch (error) {
        console.error('Could not load the 3D mascot', error);
        renderer?.dispose();
        renderer?.domElement.remove();
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
      section.removeEventListener('pointermove', onMove);
      section.removeEventListener('pointerleave', center);
      document.removeEventListener('visibilitychange', onVisibility);
      clearTimeout(blinkTimer); clearTimeout(reopenTimer);
      cancelAnimationFrame(animationFrame);
      resizeObserver?.disconnect();
      renderer?.dispose();
      renderer?.domElement.remove();
      if (sceneModel) sceneModel.traverse((part) => {
        const mesh = part as Mesh;
        mesh.geometry?.dispose();
        if (Array.isArray(mesh.material)) mesh.material.forEach((material) => material.dispose());
        else mesh.material?.dispose();
      });
      setReady(false);
      setBlinking(false);
    };
  }, [visible, mirrored, pose]);

  return <div ref={root} data-testid="guest-mascot" data-pose={pose} data-ready={ready} data-blinking={blinking} aria-hidden="true" className={`guest-mascot pointer-events-none select-none ${className}`}>
    {failed && <Image src="/redesign/mascot-hero.png" alt="" width={1024} height={1536} unoptimized className="h-full w-full object-contain" />}
  </div>;
}
