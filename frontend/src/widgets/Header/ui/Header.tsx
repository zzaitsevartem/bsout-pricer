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
import { CircleQuestionMark, SearchIcon } from '@/shared/ui/IconSVG';
import { ThemeToggle } from './ThemeToggle';
import { HeaderSearch } from './HeaderSearch';
import { UserMenu } from './UserMenu';

const navItems = [
  { href: '/tariffs', label: 'Тарифы' },
  { href: '/contacts', label: 'Контакты' },
];

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
      <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center gap-4 max-md:px-5 max-md:gap-2">
        <Link href="/" className="flex items-center no-underline shrink-0">
          <Image
            src="/Logo.svg"
            alt="BScout"
            width={140}
            height={48}
            className="h-12 w-auto brightness-0 contrast-100 dark:invert"
            priority
            unoptimized
          />
        </Link>

        <nav className="hidden lg:flex items-center gap-1 shrink-0">
          {navItems.map((item) => (
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

        <HeaderSearch className="hidden lg:block flex-1 min-w-0 max-w-[420px]" />

        <div className="hidden lg:flex items-center gap-2 ml-auto shrink-0">
          <ThemeToggle />
          {!isAuth && (
            <>
              <Link href="/login" className="btn-secondary btn-sm h-11">Войти</Link>
              <Link href="/register" className="btn-primary btn-sm h-11 rounded-b-[8px]">Регистрация</Link>
            </>
          )}
          {isAuth && <UserMenu />}
          <span aria-hidden="true" className="w-px h-6 bg-border-light-subtle mx-1" />
          <Link href="/faq" className="btn-icon" aria-label="Частые вопросы" title="Частые вопросы">
            <CircleQuestionMark />
          </Link>
        </div>

        <div className="flex lg:hidden items-center gap-1 ml-auto shrink-0">
          <Link href="/search" className="btn-icon" aria-label="Поиск запчастей" title="Поиск запчастей">
            <SearchIcon width={20} height={20} />
          </Link>
          <Link href="/faq" className="btn-icon" aria-label="Частые вопросы" title="Частые вопросы">
            <CircleQuestionMark />
          </Link>
          <button
            className={`flex flex-col justify-center items-center w-9 h-9 bg-transparent border-none cursor-pointer gap-[5px] z-50 ${isMenuOpen ? 'fixed right-5 top-5' : 'relative'}`}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label={isMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
            aria-expanded={isMenuOpen}
          >
            <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? 'rotate-45 translate-y-[7px]' : ''}`} />
            <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? 'opacity-0' : ''}`} />
            <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? '-rotate-45 -translate-y-[7px]' : ''}`} />
          </button>
        </div>

        <div className={`fixed inset-0 bg-ivory z-40 transition-transform duration-300 lg:hidden
          ${isMenuOpen ? 'translate-x-0' : 'translate-x-full'}`}
        >
          <div className="flex flex-col items-center justify-center h-full gap-8 px-8">
            <HeaderSearch className="w-full max-w-[320px]" onSubmitted={closeMenu} />
            <nav>
              <ul className="flex flex-col items-center gap-8 list-none p-0">
                {[...navItems, { href: '/faq', label: 'FAQ' }].map((item) => (
                  <li key={item.href}>
                    <Link href={item.href} className="text-2xl text-body no-underline hover:text-slate transition-colors" onClick={closeMenu}>
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <div className="flex flex-col items-center gap-4">
              <ThemeToggle />
              {!isAuth && (
                <>
                  <Link href="/login" className="btn-secondary" onClick={closeMenu}>Войти</Link>
                  <Link href="/register" className="btn-primary rounded-b-[8px]" onClick={closeMenu}>Регистрация</Link>
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
          className={`fixed inset-0 bg-black/50 z-30 transition-opacity duration-300 lg:hidden
            ${isMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
          onClick={closeMenu}
        />
      </div>
    </header>
  );
};

export { Header };
