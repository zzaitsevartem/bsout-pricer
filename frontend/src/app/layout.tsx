import type { Metadata } from 'next';
import { Providers } from '@/shared/providers/Providers';
import './globals.css';

export const metadata: Metadata = {
  title: 'BScout — Поиск запчастей для электроники',
  description: 'Сравнивайте цены на запчасти для телефонов, ноутбуков и электроники в магазинах города.',
  icons: { icon: '/logo1.webp' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
