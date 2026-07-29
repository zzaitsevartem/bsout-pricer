import type { Metadata } from 'next';
import { Providers } from '@/shared/providers/Providers';
import { ThemeProvider } from '@/shared/providers/ThemeProvider';
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
    <html lang="ru" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('bscout-theme');
                  if (!theme) {
                    theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body>
        <ThemeProvider>
          <Providers>{children}</Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
