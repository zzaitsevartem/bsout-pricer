'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { useMe } from '@/models/user';
import { useLogout } from '@/models/auth';
import { useUnreadNotificationCount } from '@/models/notification';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const router = useRouter();
  const isAuth = useUnit($isAuth);
  const { data: me } = useMe({ enabled: isAuth });
  const { data: unread } = useUnreadNotificationCount({ enabled: isAuth });
  const logout = useLogout();
  const unreadCount = unread?.unread_count ?? 0;

  useEffect(() => {
    document.body.style.overflow = isMenuOpen ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isMenuOpen]);

  const closeMenu = () => setIsMenuOpen(false);

  const handleLogout = () => {
    closeMenu();
    logout.mutate(undefined, {
      onSettled: () => router.push('/login'),
    });
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-ivory border-b border-border-light-subtle">
      <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between max-md:px-5">
        <Link href="/" className="flex items-center no-underline">
          <Image
            src="/Logo.svg"
            alt="BScout"
            width={140}
            height={48}
            className="h-12 w-auto"
            priority
            unoptimized
            style={{ filter: 'brightness(0) contrast(100)' }}
          />
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {[
            { href: '/search', label: 'Поиск' },
            { href: '/tariffs', label: 'Тарифы' },
            { href: '/faq', label: 'FAQ' },
            { href: '/contacts', label: 'Контакты' },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="relative px-3 py-2 text-[15px] text-body no-underline rounded-none transition-colors hover:text-slate group"
            >
              {item.label}
              <span className="absolute left-3 right-3 bottom-0.5 h-0.5 bg-[#C6993F] scale-x-0 origin-left transition-transform duration-300 group-hover:scale-x-100" />
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          {!isAuth && (
            <>
              <Link href="/login" className="btn-secondary btn-sm">Войти</Link>
              <Link href="/register" className="btn-primary btn-sm">Регистрация</Link>
            </>
          )}
          {isAuth && (
            <>
              {me?.is_admin && (
                <Link href="/admin" className="btn-ghost btn-sm">Админка</Link>
              )}
              <Link
                href="/account/notifications"
                className="btn-ghost btn-sm relative inline-flex items-center"
                aria-label={unreadCount > 0 ? `Уведомления: ${unreadCount} непрочитанных` : 'Уведомления'}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center text-[11px] font-medium bg-clay text-ivory">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </Link>
              <Link href="/account" className="btn-secondary btn-sm inline-flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                Кабинет
              </Link>
              <button onClick={handleLogout} disabled={logout.isPending} className="btn-primary btn-sm disabled:opacity-60">
                Выйти
              </button>
            </>
          )}
        </div>

        <button
          className={`flex md:hidden flex-col justify-center items-center w-9 h-9 bg-transparent border-none cursor-pointer gap-[5px] z-50 ${isMenuOpen ? 'fixed right-5 top-5' : 'relative'}`}
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Открыть меню"
        >
          <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? 'rotate-45 translate-y-[7px]' : ''}`} />
          <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? 'opacity-0' : ''}`} />
          <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? '-rotate-45 -translate-y-[7px]' : ''}`} />
        </button>

        <div className={`fixed inset-0 bg-ivory z-40 transition-transform duration-300 md:hidden
          ${isMenuOpen ? 'translate-x-0' : 'translate-x-full'}`}
        >
          <div className="flex flex-col items-center justify-center h-full gap-8">
            <nav>
              <ul className="flex flex-col items-center gap-8 list-none p-0">
                {[
                  { href: '/search', label: 'Поиск' },
                  { href: '/tariffs', label: 'Тарифы' },
                  { href: '/faq', label: 'FAQ' },
                  { href: '/contacts', label: 'Контакты' },
                ].map((item) => (
                  <li key={item.href}>
                    <Link href={item.href} className="text-2xl text-body no-underline hover:text-slate transition-colors" onClick={closeMenu}>
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <div className="flex flex-col items-center gap-4">
              {!isAuth && (
                <>
                  <Link href="/login" className="btn-secondary" onClick={closeMenu}>Войти</Link>
                  <Link href="/register" className="btn-primary" onClick={closeMenu}>Регистрация</Link>
                </>
              )}
              {isAuth && (
                <>
                  {me?.is_admin && (
                    <Link href="/admin" className="btn-ghost" onClick={closeMenu}>Админка</Link>
                  )}
                  <Link href="/account/notifications" className="btn-ghost" onClick={closeMenu}>
                    Уведомления{unreadCount > 0 ? ` (${unreadCount > 99 ? '99+' : unreadCount})` : ''}
                  </Link>
                  <Link href="/account" className="btn-secondary" onClick={closeMenu}>Кабинет</Link>
                  <button onClick={handleLogout} disabled={logout.isPending} className="btn-primary disabled:opacity-60">Выйти</button>
                </>
              )}
            </div>
          </div>
        </div>

        <div
          className={`fixed inset-0 bg-black/50 z-30 transition-opacity duration-300 md:hidden
            ${isMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
          onClick={closeMenu}
        />
      </div>
    </header>
  );
};

export { Header };
