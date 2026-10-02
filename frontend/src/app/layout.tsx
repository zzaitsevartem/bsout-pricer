import type { Metadata } from 'next';
import { Providers } from '@/shared/providers/Providers';
import './globals.css';

// Абсолютный адрес сайта. Нужен, чтобы Next превращал относительные ссылки
// (og:image, canonical, sitemap) в абсолютные. Задаётся на СБОРКЕ —
// поэтому в docker-compose.prod.yml это build.args, а не environment.
// `||`, а не `??`: пустая FRONTEND_BASE_URL упала бы в new URL('') и
// повалила бы всю сборку.
const siteUrl = process.env.FRONTEND_BASE_URL || 'http://localhost:3000';

const SITE_NAME = 'BScout';
const SITE_TITLE = 'BScout — Поиск запчастей для электроники';
const SITE_DESCRIPTION =
  'Сравнивайте цены на запчасти для телефонов, ноутбуков и электроники в магазинах города.';

export const metadata: Metadata = {
  // Относительные ссылки ниже резолвятся отсюда.
  metadataBase: new URL(siteUrl),
  // Страницы задают только смысловую часть — суффикс добавляет шаблон.
  title: {
    default: SITE_TITLE,
    template: `%s — ${SITE_NAME}`,
  },
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  icons: { icon: '/logo1.webp' },
  openGraph: {
    type: 'website',
    siteName: SITE_NAME,
    locale: 'ru_RU',
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
  },
  twitter: {
    card: 'summary_large_image',
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
  },
  // Канонические URL намеренно не задаются глобально: alternates.canonical
  // в root layout применился бы ко всем страницам и свёл бы их к главной.
};

const themeInitScript = `(function(){try{var t=localStorage.getItem('bscout-theme');if(!t){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}if(t==='dark'){document.documentElement.classList.add('dark');}}catch(e){}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
