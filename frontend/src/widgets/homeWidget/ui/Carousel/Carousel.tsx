'use client';

import React, { useEffect, useRef, useState } from 'react';
import Image from 'next/image';

import taggsm from '@/shared/assets/images/taggsm.webp';
import profi from '@/shared/assets/images/profi.webp';
import liberty from '@/shared/assets/images/liberty.webp';
import divizion from '@/shared/assets/images/divizion.webp';

const partners = [
  { name: 'ТГСМ', src: taggsm.src, href: 'https://taggsm.ru' },
  { name: 'Профи', src: profi.src, href: 'https://siriust.ru' },
  { name: 'Либерти', src: liberty.src, href: 'https://liberti.ru' },
  { name: 'Дивизион', src: divizion.src, href: 'https://www.divizion126.ru' },
];

const duplicatedPartners = [...partners, ...partners, ...partners, ...partners];

const Carousel: React.FC = () => {
  const section = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    const element = section.current;
    if (!element || typeof IntersectionObserver === 'undefined') return;
    let intersecting = false;
    const update = () => setVisible(intersecting && !document.hidden);
    const observer = new IntersectionObserver(([entry]) => {
      intersecting = entry.isIntersecting;
      update();
    });
    observer.observe(element);
    document.addEventListener('visibilitychange', update);
    return () => {
      observer.disconnect();
      document.removeEventListener('visibilitychange', update);
    };
  }, []);

  return (
    <section
      ref={section}
      data-running={visible && !paused}
      data-paused={paused}
      className="partner-carousel overflow-hidden py-12"
    >
      <button
        type="button"
        className="btn-ghost btn-sm mx-6 mb-4 motion-reduce:hidden"
        onClick={() => setPaused((value) => !value)}
      >
        {paused ? 'Продолжить прокрутку магазинов' : 'Приостановить прокрутку магазинов'}
      </button>
      <div className="partner-track flex gap-12 pr-12 motion-reduce:pr-0 animate-scroll w-fit">
        {duplicatedPartners.map((partner, i) => (
          <a
            key={`${partner.name}-${i}`}
            href={partner.href}
            data-partner-copy={i >= partners.length ? '' : undefined}
            aria-hidden={i >= partners.length ? true : undefined}
            tabIndex={i >= partners.length ? -1 : undefined}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 flex items-center justify-center h-12 w-32"
          >
            <Image
              src={partner.src}
              alt={partner.name}
              width={128}
              height={48}
              className="h-full w-auto object-contain grayscale opacity-60 transition-opacity duration-150 hover:grayscale-0 hover:opacity-100"
            />
          </a>
        ))}
      </div>
    </section>
  );
};

export default Carousel;
