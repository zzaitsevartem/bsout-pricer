import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import tgStatic from '@/shared/assets/images/icons/logo-tg-static.svg';
import tgHover from '@/shared/assets/images/icons/logo-tg-hover.webp';
import vkStatic from '@/shared/assets/images/icons/logo-vk-static.svg';
import vkHover from '@/shared/assets/images/icons/logo-vk-hover.webp';
import { HoverIcon } from '@/shared/ui/HoverIcon';

const Footer: React.FC<{ variant?: 'guest-home' }> = ({ variant }) => {
  if (variant === 'guest-home') {
    return <footer id="footer" className="relative min-h-[70svh] border-t border-border-light-subtle bg-ivory py-20 text-slate">
      <div className="mx-auto flex min-h-[55svh] max-w-[1200px] flex-col justify-between px-6">
        <div className="grid gap-12 md:grid-cols-[2fr_1fr_1fr_1fr]">
          <div><Link href="/" className="inline-flex items-center"><Image src="/Logo.svg" alt="BScout" width={160} height={55} className="h-14 w-auto dark:invert" /></Link><p className="mt-5 max-w-[34ch] text-body-subtle">Поиск и сравнение предложений запчастей для электроники в магазинах Ставрополя.</p></div>
          <div><h2 className="mb-5 font-semibold">Продукт</h2><nav className="flex flex-col gap-3 text-sm text-body-subtle"><Link href="/register">Начать поиск</Link><Link href="/tariffs">Тарифы</Link><a href="/#how-it-works">Как это работает</a></nav></div>
          <div><h2 className="mb-5 font-semibold">Информация</h2><nav className="flex flex-col gap-3 text-sm text-body-subtle"><Link href="/faq">FAQ</Link><Link href="/contacts">Контакты</Link><Link href="/privacy">Политика данных</Link><Link href="/terms">Условия использования</Link></nav></div>
          <div><h2 className="mb-5 font-semibold">Связаться</h2><div className="flex flex-col gap-3 text-sm text-body-subtle"><a href="mailto:hello@bscout.ru">hello@bscout.ru</a><a href="mailto:support@bscout.ru">support@bscout.ru</a></div></div>
        </div>
        <div className="mt-16 flex flex-wrap justify-between gap-4 border-t border-border-light-subtle pt-6 text-sm text-body-muted"><span>© {new Date().getFullYear()} BScout</span><div className="flex gap-5"><Link href="/terms">Условия использования</Link><Link href="/privacy">Политика данных</Link></div></div>
      </div>
    </footer>;
  }
  return (
    <footer className="bg-ivory border-t border-border-light-subtle py-[61px] pb-8 max-md:py-12 max-md:pb-6">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[2fr_1fr_1fr_1fr] gap-12 max-md:grid-cols-2 max-md:gap-8 max-[480px]:grid-cols-1">
          <div className="max-md:col-span-2 max-[480px]:col-span-1">
            <Link href="/" className="flex items-center gap-2 no-underline text-slate">
              <Image
                src="/Logo.svg"
                alt="BScout"
                width={140}
                height={48}
                className="h-12 w-auto"
                style={{ filter: 'brightness(0) contrast(100)' }}
              />
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
            <div key={col.title}>
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
            <a href="#" aria-label="Telegram" className="w-14 h-14 flex items-center justify-center no-underline">
              <HoverIcon staticIcon={tgStatic} hoverIcon={tgHover} replayIntervalMs={3000} width={40} height={40} />
            </a>
            <a href="#" aria-label="VK" className="w-14 h-14 flex items-center justify-center no-underline">
              <HoverIcon staticIcon={vkStatic} hoverIcon={vkHover} replayIntervalMs={3000} width={40} height={40} />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export { Footer };
