'use client';

import { useEffect, useRef, type ComponentPropsWithoutRef } from 'react';
import { usePathname } from 'next/navigation';

/** One content layer per route; children keep their existing identity and focus. */
export function PageTransition({ children, ...props }: ComponentPropsWithoutRef<'div'>) {
  const pathname = usePathname();
  const content = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = content.current;
    if (!element || typeof element.animate !== 'function') return;

    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    let animation: Animation | undefined;
    const cancel = () => animation?.cancel();
    if (!preference.matches && !document.hidden) {
      const tokens = getComputedStyle(document.documentElement);
      animation = element.animate([{ opacity: 0 }, { opacity: 1 }], {
        duration: Number.parseFloat(tokens.getPropertyValue('--motion-page-duration')),
        easing: tokens.getPropertyValue('--ease-out').trim(),
      });
    }
    // A preference change cancels the active effect without replaying it.
    preference.addEventListener('change', cancel);
    document.addEventListener('visibilitychange', cancel);
    return () => {
      cancel();
      preference.removeEventListener('change', cancel);
      document.removeEventListener('visibilitychange', cancel);
    };
  }, [pathname]);

  return (
    <div ref={content} data-page-transition="" {...props}>
      {children}
    </div>
  );
}
