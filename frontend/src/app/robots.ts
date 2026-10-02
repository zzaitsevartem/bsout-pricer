import type { MetadataRoute } from 'next';

// `||`, а не `??`: пустая переменная окружения тоже должна давать fallback,
// иначе получим host: '' и new URL('') в layout.
const siteUrl = process.env.FRONTEND_BASE_URL || 'http://localhost:3000';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        // Личные кабинеты, админка и служебные маршруты в индекс не идут.
        // /api закрыт дополнительно на уровне nginx.
        disallow: ['/account', '/admin', '/api/', '/subscription', '/verify-email', '/reset-password'],
      },
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
    host: siteUrl,
  };
}
