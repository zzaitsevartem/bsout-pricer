'use client';

import React from 'react';
import Link from 'next/link';
import { plural } from '@/shared/lib/format';

type QuickAccessProps = {
  used?: number;
};

const QuickAccess: React.FC<QuickAccessProps> = ({ used }) => {
  const trackingDescription =
    typeof used === 'number' && used > 0
      ? `${used} ${plural(used, 'позиция', 'позиции', 'позиций')} под контролем. Изменения цен — уведомлением.`
      : 'Возьмите первую позицию под контроль из поиска.';

  const cards = [
    {
      href: '/search',
      title: 'Поиск по артикулу',
      description:
        'Точное совпадение, частичное и нечёткий поиск с автодополнением по 5 магазинам города.',
      icon: (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.3-4.3" />
        </svg>
      ),
    },
    {
      href: '/account/tracking',
      title: 'Мои отслеживаемые',
      description: trackingDescription,
      icon: (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </svg>
      ),
    },
    {
      href: '/account/settings',
      title: 'Настройки',
      description: 'Профиль, смена логина и email, тариф и тема оформления — в одном месте.',
      icon: (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        >
          <circle cx="12" cy="12" r="3.5" />
          <path d="M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.6a7 7 0 0 0-2 1.2L5.1 5.8l-2 3.4 2 1.6A7 7 0 0 0 5 12" />
        </svg>
      ),
    },
  ];

  return (
    <section aria-label="Быстрый доступ" className="pb-[84px] max-md:pb-[61px]">
      <div className="mx-auto max-w-[1200px] px-6">
        <div className="mb-8 max-w-[640px]">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Быстрый доступ
          </p>
          <h2 className="mb-4 text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] text-slate max-md:text-[32px] max-[480px]:text-[28px]">
            Заняться делом
          </h2>
        </div>
        <div className="grid grid-cols-3 gap-6 max-md:grid-cols-1">
          {cards.map((card) => (
            <Link
              key={card.href}
              href={card.href}
              className="rounded-[24px] bg-ivory-elevated p-[31px] transition-colors duration-150 hover:bg-ivory-warm"
            >
              <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-ivory-warm text-slate">
                {card.icon}
              </span>
              <h4 className="mb-3 text-xl leading-[1.4] text-slate font-semibold">{card.title}</h4>
              <p className="text-[15px] leading-[1.4] text-body-subtle">{card.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};

export { QuickAccess };
