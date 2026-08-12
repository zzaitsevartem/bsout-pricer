'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { useMe } from '@/models/user';
import { useLogout } from '@/models/auth';
import { useUnreadNotificationCount } from '@/models/notification';
import { cn } from '@/shared/lib/utils';
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
  const pathname = usePathname();
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
    <header className="sticky top-0 z-50 w-full border-b border-border-light-subtle bg-ivory">
      <div className="mx-auto flex h-[72px] max-w-[1280px] items-center gap-5 px-6 max-md:h-16 max-md:gap-2 max-md:px-5">
        <Link href="/" className="flex shrink-0 items-center rounded-md no-underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-slate">
          <Image
            src="/Logo.svg"
            alt="BScout"
            width={140}
            height={48}
            className="h-11 w-auto brightness-0 contrast-100 dark:invert"
            priority
            unoptimized
          />
        </Link>

        <nav className="hidden shrink-0 items-center gap-1 rounded-full border border-border-light-subtle bg-ivory-elevated p-1 lg:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'rounded-full px-4 py-2 text-[15px] font-medium no-underline transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate',
                pathname === item.href
                  ? 'bg-ivory text-slate shadow-sm'
                  : 'text-body hover:bg-ivory-warm hover:text-slate',
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <HeaderSearch className="hidden min-w-0 max-w-[480px] flex-1 lg:block" />

        <div className="ml-auto hidden shrink-0 items-center gap-2 lg:flex">
          <ThemeToggle />
          {!isAuth && (
            <>
              <Link href="/login" className="btn-secondary btn-sm h-10 rounded-full">Войти</Link>
              <Link href="/register" className="btn-primary btn-sm h-10 rounded-full">Регистрация</Link>
            </>
          )}
          {isAuth && <UserMenu />}
          <span aria-hidden="true" className="mx-1 h-6 w-px bg-border-light-subtle" />
          <Link href="/faq" className="btn-icon rounded-full" aria-label="Частые вопросы" title="Частые вопросы">
            <CircleQuestionMark />
          </Link>
        </div>

        <div className="ml-auto flex shrink-0 items-center gap-1 lg:hidden">
          <Link href="/search" className="btn-icon rounded-full" aria-label="Поиск запчастей" title="Поиск запчастей">
            <SearchIcon width={20} height={20} />
          </Link>
          <Link href="/faq" className="btn-icon rounded-full" aria-label="Частые вопросы" title="Частые вопросы">
            <CircleQuestionMark />
          </Link>
          <button
            className={cn(
              'z-50 flex h-10 w-10 flex-col items-center justify-center gap-[5px] rounded-full border border-border-default bg-transparent',
              isMenuOpen ? 'fixed right-5 top-5' : 'relative',
            )}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label={isMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
            aria-expanded={isMenuOpen}
          >
            <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? 'rotate-45 translate-y-[7px]' : ''}`} />
            <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? 'opacity-0' : ''}`} />
            <span className={`block w-6 h-[2px] bg-slate transition-all duration-300 ${isMenuOpen ? '-rotate-45 -translate-y-[7px]' : ''}`} />
          </button>
        </div>

        <div className={cn(
          'fixed inset-0 z-40 bg-ivory transition-transform duration-300 lg:hidden',
          isMenuOpen ? 'translate-x-0' : 'translate-x-full',
        )}
        >
          <div className="flex flex-col items-center justify-center h-full gap-8 px-8">
            <HeaderSearch className="w-full max-w-[320px]" onSubmitted={closeMenu} />
            <nav>
              <ul className="flex flex-col items-center gap-8 list-none p-0">
                {[...navItems, { href: '/faq', label: 'FAQ' }].map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        'text-2xl no-underline transition-colors focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-slate',
                        pathname === item.href ? 'font-bold text-slate' : 'text-body hover:text-slate',
                      )}
                      onClick={closeMenu}
                    >
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
                  <Link href="/register" className="btn-primary rounded-full" onClick={closeMenu}>Регистрация</Link>
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
