import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { TgIcon, VkIcon } from '../../../shared/ui/IconSVG';

const Footer: React.FC = () => {
  return (
    <footer className="bg-ivory border-t border-border-light-subtle py-[61px] pb-8 max-md:py-12 max-md:pb-6">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[2fr_1fr_1fr_1fr] gap-12 max-md:grid-cols-2 max-md:gap-8 max-[480px]:grid-cols-1">
          <div className="max-md:col-span-2 max-[480px]:col-span-1">
            <Link href="/" className="flex items-center gap-3 no-underline text-slate">
              <div className="relative w-14 h-14 rounded-[10px] overflow-hidden flex-shrink-0">
                <div className="absolute inset-0 animate-shimmer" style={{ background: 'conic-gradient(#D97757, #788C5D, #6A9BCC, #C46686, #BCD1CA, #D97757)' }} />
                <div className="absolute inset-[2px] bg-ivory rounded-[8px] flex items-center justify-center">
                  <Image src="/logo1.webp" alt="BScout" width={36} height={36} className="w-9 h-9" />
                </div>
              </div>
              <span className="text-xl font-bold">BScout</span>
            </Link>
            <p className="text-[15px] text-body-subtle max-w-[40ch] mt-3">
              Единая платформа для поиска и сравнения цен на запчасти для электроники среди магазинов Ставрополя.
            </p>
          </div>
          {[
            { title: 'Продукт', links: [
              { href: '/search', label: 'Поиск' },
              { href: '/tariffs', label: 'Тарифы' },
              { href: '/faq', label: 'FAQ' },
            ]},
            { title: 'Компания', links: [
              { href: '/contacts', label: 'Контакты' },
              { href: '/about', label: 'О проекте' },
            ]},
            { title: 'Юридическая', links: [
              { href: '/privacy', label: 'Политика данных' },
              { href: '/terms', label: 'Условия использования' },
            ]},
          ].map((col) => (
            <div key={col.title} className="footer-col">
              <h5 className="text-[15px] font-semibold text-slate mb-4">{col.title}</h5>
              {col.links.map((link) => (
                <Link key={link.href} href={link.href} className="block text-[15px] text-body-subtle no-underline py-1 transition-colors hover:text-slate">
                  {link.label}
                </Link>
              ))}
            </div>
          ))}
        </div>
        <div className="mt-12 pt-6 border-t border-border-light-subtle flex justify-between items-center text-[15px] text-body-muted max-md:flex-col max-md:gap-4 max-md:text-center">
          <span>&copy; 2026 BScout. Все права защищены.</span>
          <div className="flex gap-3">
            <a href="#" aria-label="Telegram" className="w-9 h-9 flex items-center justify-center border border-border-default text-body-subtle no-underline text-sm transition-colors hover:border-slate hover:text-slate">
              <TgIcon width="16" height="16" />
            </a>
            <a href="#" aria-label="VK" className="w-9 h-9 flex items-center justify-center border border-border-default text-body-subtle no-underline text-sm transition-colors hover:border-slate hover:text-slate">
              <VkIcon width="16" height="16" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export { Footer };
