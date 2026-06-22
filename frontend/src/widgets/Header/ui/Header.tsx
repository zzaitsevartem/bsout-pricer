'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { PersonIcon } from '../../../shared/ui/IconSVG';

interface HeaderProps {
  navCta?: 'login' | 'register' | 'logout' | 'profile';
  showProfileIcon?: boolean;
  adminBadge?: boolean;
}

const Header: React.FC<HeaderProps> = ({
  navCta = 'login',
  showProfileIcon = false,
  adminBadge = false,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = isMenuOpen ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isMenuOpen]);

  const closeMenu = () => setIsMenuOpen(false);

  return (
    <header
      className={`sticky top-0 z-50 w-full bg-ivory transition-shadow
        ${isScrolled ? 'shadow-[0_1px_0_0_#E8E6DC]' : ''}`}
    >
      <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between max-md:px-5">
        <Link href="/" className="flex items-center no-underline text-slate hover:text-slate">
          <Image src="/Logo.svg" alt="BScout" width={140} height={70} className="h-7 w-auto" priority />
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
              className="px-3 py-2 text-[15px] text-body no-underline rounded-none transition-colors hover:bg-ivory-elevated hover:text-slate"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          {showProfileIcon && (
            <Link href="/account" className="w-10 h-10 flex items-center justify-center text-body-subtle rounded-none hover:bg-ivory-elevated hover:text-slate transition-colors" aria-label="Личный кабинет">
              <PersonIcon width="20" height="20" />
            </Link>
          )}
          {adminBadge && (
            <span className="text-xs font-mono uppercase tracking-wider px-2 py-0.5 text-clay border border-clay bg-transparent">
              Админ
            </span>
          )}
          {navCta === 'login' && (
            <Link href="/login" className="btn-secondary">Войти</Link>
          )}
          {navCta === 'register' && (
            <Link href="/register" className="btn-primary">Регистрация</Link>
          )}
          {navCta === 'logout' && (
            <Link href="/login" className="btn-secondary">Выйти</Link>
          )}
          {navCta === 'profile' && (
            <>
              <Link href="/account" className="w-10 h-10 flex items-center justify-center text-body-subtle rounded-none hover:bg-ivory-elevated hover:text-slate transition-colors" aria-label="Личный кабинет">
                <PersonIcon width="20" height="20" />
              </Link>
              <Link href="/login" className="btn-secondary">Выйти</Link>
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
