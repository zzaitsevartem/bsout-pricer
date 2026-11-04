'use client';

import { useEffect, useRef, useState } from 'react';
import Image, { type StaticImageData } from 'next/image';
import { cn } from '@/shared/lib/utils';

type HoverIconProps = {
  staticIcon: StaticImageData | string;
  hoverIcon: StaticImageData | string;
  /** Time between animation restarts, including playback and a short pause. */
  replayIntervalMs: number;
  width?: number;
  height?: number;
  className?: string;
};

export function HoverIcon({
  staticIcon,
  hoverIcon,
  replayIntervalMs,
  width = 24,
  height = 24,
  className,
}: HoverIconProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const [active, setActive] = useState(false);
  const [animationCycle, setAnimationCycle] = useState(0);

  useEffect(() => {
    const icon = ref.current;
    const host = icon?.closest('button, a') ?? icon?.parentElement;
    if (!host) return;
    let hovered = false;
    let focused = false;
    let isActive = false;
    const update = () => {
      const nextActive =
        (hovered || focused) && !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      if (nextActive && !isActive) setAnimationCycle((cycle) => cycle + 1);
      isActive = nextActive;
      setActive(nextActive);
    };
    const enter = () => {
      hovered = true;
      update();
    };
    const leave = () => {
      hovered = false;
      update();
    };
    const focus = () => {
      focused = true;
      update();
    };
    const blur = () => {
      focused = false;
      update();
    };
    host.addEventListener('pointerenter', enter);
    host.addEventListener('pointerleave', leave);
    host.addEventListener('focusin', focus);
    host.addEventListener('focusout', blur);
    return () => {
      host.removeEventListener('pointerenter', enter);
      host.removeEventListener('pointerleave', leave);
      host.removeEventListener('focusin', focus);
      host.removeEventListener('focusout', blur);
    };
  }, []);

  useEffect(() => {
    if (!active || replayIntervalMs <= 0) return;
    const timeout = window.setTimeout(() => {
      setAnimationCycle((cycle) => cycle + 1);
    }, replayIntervalMs);
    return () => window.clearTimeout(timeout);
  }, [active, animationCycle, replayIntervalMs]);

  const animatedSource = typeof hoverIcon === 'string' ? hoverIcon : hoverIcon.src;
  const cycleQuery = animatedSource.includes('?') ? '&' : '?';
  const replaySource = `${animatedSource}${cycleQuery}cycle=${animationCycle}`;

  return (
    <span
      ref={ref}
      aria-hidden="true"
      className={cn('inline-flex shrink-0 items-center justify-center', className)}
    >
      <Image
        key={active ? `animated-${animationCycle}` : 'static'}
        src={active ? replaySource : staticIcon}
        width={width}
        height={height}
        alt=""
        unoptimized
        className="block object-contain dark:brightness-0 dark:invert"
      />
    </span>
  );
}
