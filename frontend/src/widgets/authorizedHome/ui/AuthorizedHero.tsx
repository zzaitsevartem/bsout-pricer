'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { plural } from '@/shared/lib/format';
import type { UserResponse } from '@/models/user';

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

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
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
    <section className="relative isolate min-h-[656px] overflow-hidden">
      <div
        aria-hidden="true"
        className="absolute inset-0 z-0 bg-[url('/background.webp')] bg-cover bg-center bg-no-repeat dark:brightness-[0.35]"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 z-[1] bg-gradient-to-r from-ivory via-ivory/80 to-ivory/25"
      />
      <div className="relative z-[2] mx-auto flex min-h-[656px] w-full max-w-[1200px] flex-col justify-center px-6 py-16 max-md:min-h-0">
        <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
          Личный кабинет
        </p>
        <h1 className="mb-6 text-[61px] font-bold leading-[1.1] tracking-[-0.02em] text-slate max-md:text-[44px] max-[480px]:text-[36px]">
          С возвращением,
          <br />
          <span className="underline decoration-[3px] underline-offset-[6px]">
            {name || 'добро пожаловать'}
          </span>
        </h1>
        <p className="mb-8 max-w-[50ch] text-lg leading-[1.4] text-body">{lead}</p>

        <form onSubmit={handleSubmit} role="search" className="max-w-[620px]">
          <label htmlFor="home-search" className="sr-only">
            Артикул, название или бренд
          </label>
          <div className="flex items-center rounded-full border border-border-input bg-ivory p-[6px] pl-7 transition-colors focus-within:border-border-default">
            <input
              id="home-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Артикул, название или бренд…"
              className="h-[52px] w-full min-w-0 border-none bg-transparent text-[18px] text-slate placeholder:text-body-muted focus:outline-none [&::-webkit-search-cancel-button]:appearance-none"
            />
            <button type="submit" className="btn-primary btn-lg shrink-0">
              Найти
            </button>
          </div>
        </form>

        <div className="mt-7 flex flex-wrap gap-8">
          <Link href="/account/tracking" className="btn-arrow">
            Мои отслеживаемые{typeof used === 'number' ? ` (${used})` : ''} →
          </Link>
          <Link href="/account/notifications" className="btn-arrow">
            Уведомления{typeof unread === 'number' ? ` (${unread})` : ''} →
          </Link>
        </div>
      </div>
    </section>
  );
};

export { AuthorizedHero };
