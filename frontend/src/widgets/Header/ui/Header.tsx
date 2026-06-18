'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Logo, PersonIcon, SupportIcon } from '../../../shared/ui/IconSVG';
import styles from './Header.module.scss';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const closeMenu = () => setIsMenuOpen(false);

  useEffect(() => {
    if (isMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => { document.body.style.overflow = 'unset'; };
  }, [isMenuOpen]);

  return (
    <header className={`${styles.header} ${isScrolled ? styles.scrolled : ''}`}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo} onClick={closeMenu}>
          <Logo />
        </Link>
        <nav className={styles.nav}>
          <ul className={styles.menu}>
            <li><Link href="/tariffs" className={styles.link} onClick={closeMenu}>Тарифы</Link></li>
            <li><Link href="/contacts" className={styles.link} onClick={closeMenu}>Контакты</Link></li>
            <li><Link href="/faq" className={styles.link} onClick={closeMenu}>FAQ</Link></li>
          </ul>
        </nav>
        <div className={styles.actions}>
          <Link href="/account" className={styles.action} onClick={closeMenu}>
            <PersonIcon /><span>Личный кабинет</span>
          </Link>
          <Link href="/support" className={styles.action} onClick={closeMenu}>
            <SupportIcon /><span>Поддержка</span>
          </Link>
        </div>
        <button className={`${styles.burger} ${isMenuOpen ? styles.burgerOpen : ''}`}
          onClick={toggleMenu} aria-label="Открыть меню">
          <span className={styles.burgerLine}></span>
          <span className={styles.burgerLine}></span>
          <span className={styles.burgerLine}></span>
        </button>
        <div className={`${styles.mobileMenu} ${isMenuOpen ? styles.mobileMenuOpen : ''}`}>
          <div className={styles.mobileMenuContent}>
            <div className={styles.menuCenter}>
              <nav className={styles.mobileNav}>
                <ul className={styles.mobileMenuList}>
                  <li><Link href="/tariffs" className={styles.mobileLink} onClick={closeMenu}><span className={styles.linkText}>Тарифы</span><div className={styles.linkLine}></div></Link></li>
                  <li><Link href="/contacts" className={styles.mobileLink} onClick={closeMenu}><span className={styles.linkText}>Контакты</span><div className={styles.linkLine}></div></Link></li>
                  <li><Link href="/faq" className={styles.mobileLink} onClick={closeMenu}><span className={styles.linkText}>FAQ</span><div className={styles.linkLine}></div></Link></li>
                </ul>
              </nav>
              <div className={styles.mobileActions}>
                <Link href="/account" className={styles.mobileAction} onClick={closeMenu}><PersonIcon /><span>Личный кабинет</span></Link>
                <Link href="/support" className={styles.mobileAction} onClick={closeMenu}><SupportIcon /><span>Поддержка</span></Link>
              </div>
            </div>
          </div>
        </div>
        <div className={`${styles.overlay} ${isMenuOpen ? styles.overlayVisible : ''}`} onClick={closeMenu}></div>
      </div>
    </header>
  );
};
export { Header };
