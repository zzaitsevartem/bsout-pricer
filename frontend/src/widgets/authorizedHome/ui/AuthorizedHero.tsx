'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ProductSearchField } from '@/widgets/ProductSearch/ui/ProductSearchField';
import { plural } from '@/shared/lib/format';
import type { UserResponse } from '@/models/user';
import { HeroArtwork } from '@/shared/ui/HeroArtwork';

type AuthorizedHeroProps = {
  me?: UserResponse;
  used?: number;
  unread?: number;
};

function firstNameOf(me?: UserResponse): string {
  const fullName = me?.full_name?.trim();
  if (fullName) {
    return fullName.split(/\s+/)[0] ?? '';
  }
  const username = me?.username?.trim();
  if (username) {
    return username;
  }
  const email = me?.email?.trim();
  if (email) {
    return email.split('@')[0] ?? '';
  }
  return '';
}

const AuthorizedHero: React.FC<AuthorizedHeroProps> = ({ me, used, unread }) => {
  const router = useRouter();
  const [query, setQuery] = useState('');

  const search = (query: string) => {
    const q = query.trim();
    router.push(q ? `/search?q=${encodeURIComponent(q)}` : '/search');
  };

  const hasTracked = typeof used === 'number' && used > 0;
  const hasUnread = typeof unread === 'number' && unread > 0;

  const lead = hasTracked
    ? [
        `Под контролем ${used} ${plural(used, 'позиция', 'позиции', 'позиций')}.`,
        hasUnread
          ? `${unread} ${plural(unread, 'новое уведомление', 'новых уведомления', 'новых уведомлений')}.`
          : null,
      ]
        .filter(Boolean)
        .join(' ')
    : 'Сравнивайте цены на запчасти для электроники в 5 магазинах Ставрополя. Начните с поиска — выгодные предложения за секунды.';

  const name = firstNameOf(me);

  return (
    <section className="relative z-10 isolate bg-ivory">
      <div className="mx-auto flex min-h-[656px] w-full max-w-[1280px] flex-col justify-center px-6 py-12 lg:py-14">
        <div className="relative z-[1] min-w-0 lg:max-w-[54%]">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Личный кабинет
          </p>
          <h1 className="mb-6 text-[44px] font-bold leading-[1.1] tracking-[-0.02em] text-slate max-[480px]:text-[36px] lg:text-[48px] xl:text-[54px]">
            С возвращением,
            <br />
            <span className="underline decoration-[3px] underline-offset-[6px]">
              {name || 'добро пожаловать'}
            </span>
          </h1>
          <p className="mb-8 max-w-[50ch] text-lg leading-[1.4] text-body">{lead}</p>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              search(query);
            }}
            role="search"
            className="max-w-[620px]"
          >
            <label htmlFor="home-search" className="sr-only">
              Артикул, название или бренд
            </label>
            <div className="field-shell flex items-center rounded-full border border-border-input bg-ivory p-[6px] pl-7 transition-colors focus-within:border-border-default">
              <ProductSearchField
                id="home-search"
                value={query}
                onValueChange={setQuery}
            onDeviceSelect={(device) => {
              setQuery('');
              router.push(`/search?device_id=${device.id}`);
            }}
                onSelect={(selected) => {
                  setQuery(selected);
                  search(selected);
                }}
            label="Модель устройства, артикул или запчасть"
            placeholder="Модель устройства, например iPhone 13…"
                className="flex-1"
                inputClassName="h-[52px] w-full min-w-0 border-none bg-transparent text-[18px] text-slate placeholder:text-body-muted focus:outline-none [&::-webkit-search-cancel-button]:appearance-none"
              />
              <button type="submit" className="btn-primary btn-lg home-search-submit shrink-0">
                Найти
              </button>
            </div>
          </form>

          <div className="mt-7 flex flex-wrap gap-8">
            <Link href="/account/tracking" className="btn-arrow">
              Мои отслеживаемые{typeof used === 'number' ? ` (${used})` : ''}
            </Link>
            <Link href="/account/notifications" className="btn-arrow">
              Уведомления{typeof unread === 'number' ? ` (${unread})` : ''}
            </Link>
          </div>
        </div>
        <HeroArtwork />
      </div>
    </section>
  );
};

export { AuthorizedHero };
