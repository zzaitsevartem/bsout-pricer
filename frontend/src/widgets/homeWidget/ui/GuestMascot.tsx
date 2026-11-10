'use client';

import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';

type Pose = 'hero' | 'calm' | 'pointing' | 'presenting';

export function GuestMascot({ pose, className = '', mirrored = false }: { pose: Pose; className?: string; mirrored?: boolean }) {
  const root = useRef<HTMLDivElement>(null);
  const head = useRef<HTMLImageElement>(null);
  const [visible, setVisible] = useState(false);
  const [blinking, setBlinking] = useState(false);
  const src = `/redesign/mascot-${pose}.png`;

  useEffect(() => {
    const node = root.current;
    if (!node || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), { rootMargin: '120px' });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible) return;
    const node = root.current;
    const section = node?.closest('section');
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!node || !section || !fine.matches || reduced.matches) return;
    let blinkTimer: ReturnType<typeof setTimeout>;
    let reopenTimer: ReturnType<typeof setTimeout>;
    const onMove = (event: Event) => {
      const pointer = event as PointerEvent;
      if (pointer.pointerType && pointer.pointerType !== 'mouse') return;
      const bounds = node.getBoundingClientRect();
      const x = Math.max(-1, Math.min(1, (pointer.clientX - bounds.left - bounds.width / 2) / (bounds.width / 2)));
      const y = Math.max(-1, Math.min(1, (pointer.clientY - bounds.top - bounds.height / 3) / (bounds.height / 2)));
      if (head.current) head.current.style.transform = `rotateY(${x * (mirrored ? -7 : 7)}deg) rotateX(${-y * 4}deg)`;
    };
    const center = () => { if (head.current) head.current.style.transform = 'rotateY(0deg) rotateX(0deg)'; };
    const scheduleBlink = () => {
      blinkTimer = setTimeout(() => {
        if (document.hidden) return;
        setBlinking(true);
        reopenTimer = setTimeout(() => { setBlinking(false); scheduleBlink(); }, 120);
      }, 3000 + Math.random() * 3000);
    };
    const onVisibility = () => {
      clearTimeout(blinkTimer);
      clearTimeout(reopenTimer);
      setBlinking(false);
      center();
      if (!document.hidden) scheduleBlink();
    };
    section.addEventListener('pointermove', onMove);
    section.addEventListener('pointerleave', center);
    document.addEventListener('visibilitychange', onVisibility);
    if (!document.hidden) scheduleBlink();
    return () => {
      section.removeEventListener('pointermove', onMove);
      section.removeEventListener('pointerleave', center);
      document.removeEventListener('visibilitychange', onVisibility);
      clearTimeout(blinkTimer);
      clearTimeout(reopenTimer);
      center();
      setBlinking(false);
    };
  }, [visible, mirrored]);

  return (
    <div ref={root} data-testid="guest-mascot" aria-hidden="true" className={`guest-mascot pointer-events-none select-none ${mirrored ? 'guest-mascot-mirrored' : ''} ${className}`}>
      {/* The original transparent pose stays still; its matching head layer handles pointer response. */}
      <Image src={src} alt="" width={1024} height={1536} unoptimized className="guest-mascot-body" draggable={false} />
      <Image ref={head} src={src} alt="" width={1024} height={1536} unoptimized data-testid="mascot-head" className="guest-mascot-head" draggable={false} />
      <span className="guest-mascot-eyelids" data-blinking={blinking} />
    </div>
  );
}
