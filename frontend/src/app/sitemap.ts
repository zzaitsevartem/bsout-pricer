import type { MetadataRoute } from 'next';

const siteUrl = process.env.FRONTEND_BASE_URL || 'http://localhost:3000';

// Только публичные страницы. Личный кабинет, админка и страницы с формой
// входа в карту не попадают: они закрыты RequireAuth/RequireAdmin и для
// robots.txt закрыты disallow.
// /product/[id] тоже не перечисляем — id офферов известны только из БД,
// а статическая карта не должна ни содержать их, ни подставлять пустые.
const PUBLIC_ROUTES: { path: string; priority: number; changeFrequency: MetadataRoute.Sitemap[number]['changeFrequency'] }[] = [
  { path: '/', priority: 1, changeFrequency: 'daily' },
  { path: '/search', priority: 0.9, changeFrequency: 'daily' },
  { path: '/tariffs', priority: 0.8, changeFrequency: 'monthly' },
  { path: '/contacts', priority: 0.5, changeFrequency: 'yearly' },
  { path: '/faq', priority: 0.5, changeFrequency: 'monthly' },
  { path: '/privacy', priority: 0.3, changeFrequency: 'yearly' },
  { path: '/terms', priority: 0.3, changeFrequency: 'yearly' },
];

export default function sitemap(): MetadataRoute.Sitemap {
  return PUBLIC_ROUTES.map((route) => ({
    url: `${siteUrl}${route.path}`,
    changeFrequency: route.changeFrequency,
    priority: route.priority,
  }));
}
