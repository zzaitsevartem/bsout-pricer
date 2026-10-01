import type { Metadata } from 'next';
import { Providers } from '@/shared/providers/Providers';
import './globals.css';

export const metadata: Metadata = {
  title: 'BScout — Поиск запчастей для электроники',
  description: 'Сравнивайте цены на запчасти для телефонов, ноутбуков и электроники в магазинах города.',
  icons: { icon: '/logo1.webp' },
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
