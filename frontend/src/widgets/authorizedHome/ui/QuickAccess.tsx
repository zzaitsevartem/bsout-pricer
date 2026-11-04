'use client';

import React from 'react';
import Link from 'next/link';
import { SearchIcon } from '@/shared/ui/IconSVG';
import { HoverIcon } from '@/shared/ui/HoverIcon';
import eyeStatic from '@/shared/assets/images/icons/eye-static.svg';
import eyeHover from '@/shared/assets/images/icons/eye-hover.webp';
import settingsStatic from '@/shared/assets/images/icons/settings-static.svg';
import settingsHover from '@/shared/assets/images/icons/settings-hover.webp';
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
      icon: <SearchIcon width={24} height={24} />,
    },
    {
      href: '/account/tracking',
      title: 'Мои отслеживаемые',
      description: trackingDescription,
      icon: <HoverIcon staticIcon={eyeStatic} hoverIcon={eyeHover} replayIntervalMs={3500} />,
    },
    {
      href: '/account/settings',
      title: 'Настройки',
      description: 'Профиль, смена логина и email, тариф и тема оформления — в одном месте.',
      icon: <HoverIcon staticIcon={settingsStatic} hoverIcon={settingsHover} replayIntervalMs={2667} />,
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
              className="quick-access-card rounded-[24px] bg-ivory-elevated p-[31px] transition-colors duration-150 hover:bg-ivory-warm"
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
