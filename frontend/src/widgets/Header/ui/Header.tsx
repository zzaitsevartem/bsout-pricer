'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';

interface HeaderProps {
  navCta?: 'login' | 'register' | 'logout' | 'profile';
  showProfileIcon?: boolean;
  adminBadge?: boolean;
}

const Header: React.FC<HeaderProps> = ({
  navCta = 'both',
  showProfileIcon = false,
  adminBadge = false,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = isMenuOpen ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isMenuOpen]);

  const closeMenu = () => setIsMenuOpen(false);

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
          {navCta === 'login' && (
            <Link href="/login" className="btn-secondary btn-sm">Войти</Link>
          )}
          {navCta === 'register' && (
            <Link href="/register" className="btn-primary btn-sm">Регистрация</Link>
          )}
          {navCta === 'both' && (
            <>
              <Link href="/login" className="btn-secondary btn-sm">Войти</Link>
              <Link href="/register" className="btn-primary btn-sm">Регистрация</Link>
            </>
          )}
          {navCta === 'logout' && (
            <Link href="/login" className="btn-secondary btn-sm">Выйти</Link>
          )}
          {navCta === 'profile' && (
            <Link href="/login" className="btn-secondary btn-sm">Выйти</Link>
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
