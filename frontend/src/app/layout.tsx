import type { Metadata } from 'next';
import { Raleway, DM_Sans, Lexend, Montserrat } from 'next/font/google';
import './globals.css';

const raleway = Raleway({
  subsets: ['cyrillic', 'latin'],
  weight: ['400', '700', '900'],
  variable: '--font-raleway',
});

const dmSans = DM_Sans({
  subsets: ['latin', 'latin-ext'],
  weight: ['100', '200', '300', '400', '500', '600', '700', '800', '900'],
  variable: '--font-dm-sans',
});

const lexend = Lexend({
  subsets: ['latin'],
  weight: ['100', '200', '300', '400', '500', '600', '700', '800', '900'],
  variable: '--font-lexend',
});

const montserrat = Montserrat({
  subsets: ['cyrillic', 'latin'],
  weight: ['100', '200', '300', '400', '500', '600', '700', '800', '900'],
  variable: '--font-montserrat',
});

export const metadata: Metadata = {
  title: 'BScout — мониторинг цен на запчасти',
  description: 'Платформа для мониторинга цен на запчасти для телефонов, ноутбуков и другой техники',
  icons: { icon: '/logo1.webp' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={`${raleway.variable} ${dmSans.variable} ${lexend.variable} ${montserrat.variable}`}>
      <body>{children}</body>
    </html>
  );
}
