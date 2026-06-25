'use client';

import React, { useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';

const MASK = '250, 249, 245';
const R_START = 8;
const R_END = 128;
const R_VARY = 0.45;
const LIFETIME = 520;
const FADE_LIFETIME = 1800;
const STAMP_STEP = 12;
const MAX_STAMPS = 160;

interface Stamp {
  x: number;
  y: number;
  born: number;
  seed: number;
  rmax: number;
}

function initCanvas(heroEl: HTMLElement, canvasEl: HTMLCanvasElement, carveInk: Function) {
  const canHover = window.matchMedia('(hover: hover)').matches;
  if (!canHover) return;

  const context = canvasEl.getContext('2d')!;

  const DPR = Math.min(window.devicePixelRatio || 1, 2);
  let w = 0;
  let h = 0;
  const stamps: Stamp[] = [];
  let lastX: number | null = null;
  let lastY: number | null = null;
  let running = false;
  let animFrame = 0;

  function resize() {
    const rect = heroEl.getBoundingClientRect();
    w = rect.width;
    h = rect.height;
    canvasEl.width = Math.round(w * DPR);
    canvasEl.height = Math.round(h * DPR);
    canvasEl.style.width = w + 'px';
    canvasEl.style.height = h + 'px';
    context.setTransform(DPR, 0, 0, DPR, 0, 0);
    context.globalCompositeOperation = 'source-over';
    context.fillStyle = `rgb(${MASK})`;
    context.fillRect(0, 0, w, h);
  }
  resize();
  window.addEventListener('resize', resize);

  function addStamp(x: number, y: number) {
    if (stamps.length >= MAX_STAMPS) stamps.shift();
    stamps.push({
      x, y,
      born: performance.now(),
      seed: Math.random() * Math.PI * 2,
      rmax: R_END * (1 - R_VARY + Math.random() * R_VARY),
    });
  }

  function stampAlong(x: number, y: number) {
    const lx = lastX;
    const ly = lastY;
    if (lx === null || ly === null) {
      addStamp(x, y);
    } else {
      const dx = x - lx;
      const dy = y - ly;
      const dist = Math.hypot(dx, dy);
      const steps = Math.max(1, Math.ceil(dist / STAMP_STEP));
        for (let i = 1; i <= steps; i++) {
          addStamp(lx + (dx * i) / steps, ly + (dy * i) / steps);
      }
    }
    lastX = x;
    lastY = y;
  }

  function loop() {
    const now = performance.now();
    const totalLife = LIFETIME + FADE_LIFETIME;

    context.globalCompositeOperation = 'source-over';
    context.fillStyle = `rgb(${MASK})`;
    context.fillRect(0, 0, w, h);

    context.globalCompositeOperation = 'destination-out';
    for (let i = stamps.length - 1; i >= 0; i--) {
      const age = now - stamps[i].born;
      if (age >= totalLife) {
        stamps.splice(i, 1);
        continue;
      }
      const tExpand = Math.min(age / LIFETIME, 1);
      const ease = 1 - Math.pow(1 - tExpand, 3);
      const r = R_START + (stamps[i].rmax - R_START) * ease;
      let alpha: number;
      if (age < LIFETIME) {
        alpha = 1;
      } else {
        const tFade = (age - LIFETIME) / FADE_LIFETIME;
        alpha = 1 - tFade * tFade;
      }
      carveInk(context, stamps[i].x, stamps[i].y, r, alpha, stamps[i].seed);
    }

    if (stamps.length) {
      animFrame = requestAnimationFrame(loop);
    } else {
      running = false;
    }
  }

  function start() {
    if (!running) {
      running = true;
      animFrame = requestAnimationFrame(loop);
    }
  }

  function handleMouseEnter(e: MouseEvent) {
    const rect = heroEl.getBoundingClientRect();
    lastX = e.clientX - rect.left;
    lastY = e.clientY - rect.top;
    stampAlong(lastX, lastY);
    start();
  }

  function handleMouseMove(e: MouseEvent) {
    const rect = heroEl.getBoundingClientRect();
    stampAlong(e.clientX - rect.left, e.clientY - rect.top);
    start();
  }

  function handleMouseLeave() {
    lastX = null;
    lastY = null;
  }

  heroEl.addEventListener('mouseenter', handleMouseEnter);
  heroEl.addEventListener('mousemove', handleMouseMove);
  heroEl.addEventListener('mouseleave', handleMouseLeave);

  return () => {
    window.removeEventListener('resize', resize);
    heroEl.removeEventListener('mouseenter', handleMouseEnter);
    heroEl.removeEventListener('mousemove', handleMouseMove);
    heroEl.removeEventListener('mouseleave', handleMouseLeave);
    cancelAnimationFrame(animFrame);
  };
}

const Hero: React.FC = () => {
  const heroRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const carveInk = useCallback((
    context: CanvasRenderingContext2D,
    x: number, y: number, r: number, alpha: number, seed: number
  ) => {
    const g = context.createRadialGradient(x, y, r * 0.25, x, y, r);
    g.addColorStop(0, `rgba(0, 0, 0, ${0.95 * alpha})`);
    g.addColorStop(0.55, `rgba(0, 0, 0, ${0.88 * alpha})`);
    g.addColorStop(1, 'rgba(0, 0, 0, 0)');
    context.fillStyle = g;
    context.beginPath();
    const segs = 32;
    for (let i = 0; i <= segs; i++) {
      const a = (i / segs) * Math.PI * 2;
      const wob =
        0.78 +
        0.14 * Math.sin(a * 3 + seed) +
        0.08 * Math.sin(a * 7 + seed * 2.1) +
        0.05 * Math.sin(a * 13 + seed * 0.7);
      const rr = r * wob;
      const px = x + Math.cos(a) * rr;
      const py = y + Math.sin(a) * rr;
      if (i === 0) context.moveTo(px, py);
      else context.lineTo(px, py);
    }
    context.closePath();
    context.fill();
  }, []);

  useEffect(() => {
    const heroEl = heroRef.current;
    const canvasEl = canvasRef.current;
    if (!heroEl || !canvasEl) return;
    return initCanvas(heroEl, canvasEl, carveInk);
  }, [carveInk]);

  return (
    <section
      ref={heroRef}
      className="relative h-[656px] pt-16 overflow-hidden isolate max-md:h-auto max-md:min-h-[425px]"
    >
      <div className="absolute inset-0 bg-[url('/background.webp')] bg-cover bg-center bg-no-repeat z-0" />

      <canvas
        ref={canvasRef}
        className="absolute inset-0 z-[1] pointer-events-none max-md:hidden"
      />

      <div className="relative z-[2] max-w-[1200px] mx-auto px-6 h-full flex flex-col justify-center">
        <div>
          <h1 className="text-[61px] font-bold leading-[1.1] tracking-[-0.02em] mb-6 text-slate max-md:text-[44px] max-[480px]:text-[36px]">
            Поиск запчастей для<br />
            <span className="underline underline-offset-[6px] decoration-[3px]">электроники</span>{' '}
            в<br />
            Ставрополе
          </h1>
          <p className="text-lg leading-[1.4] text-body mb-8 max-w-[50ch]">
            Сравнивайте цены на запчасти для телефонов, ноутбуков и электроники в 5 магазинах города. Находите самые выгодные предложения за секунды.
          </p>
          <div className="flex gap-4 items-center flex-wrap">
            <Link href="/register" className="btn-primary btn-lg">Начать бесплатно</Link>
            <Link href="/search" className="btn-arrow">Попробовать поиск</Link>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
