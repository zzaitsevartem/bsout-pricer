# AGENTS.md — app/

Слой **app/** — 11 страниц Next.js App Router. Каждая страница — только композиция виджетов/фич, никакой логики.

## Структура

```
app/
├── layout.tsx              # Корневой layout: QueryProvider + AuthGate + globals.css
├── page.tsx                # Главная: Header + HomeWidget + Footer
├── globals.css             # Tailwind directives, CSS-переменные, Google Fonts, btn-* классы
├── login/page.tsx          # Вход: Header + LoginForm + соц.кнопки
├── register/page.tsx       # Регистрация: Header + RegisterForm
├── search/page.tsx         # Поиск: SearchBar + SearchFilters + SearchResults (useSearchParams)
├── product/page.tsx        # Товар: Header + ProductDetail + Footer
├── tariffs/page.tsx        # Тарифы: Header + PlanComparison + Footer
├── faq/page.tsx            # FAQ: Header + FaqAccordion + Footer
├── contacts/page.tsx       # Контакты: Header + ContactInfo + ContactForm + Footer
├── account/page.tsx        # Аккаунт: ProtectedRoute → AccountSidebar + AccountProfile
├── subscription/page.tsx   # Подписка: ProtectedRoute → AccountSidebar + SubscriptionManager
└── admin/page.tsx          # Админка: ProtectedRoute → Header(adminBadge) + AdminSidebar + AdminDashboard
```

## Соглашения

- **"use client"** — только если есть React-хуки (useState, useEffect, usePathname). Все остальные — Server Components
- **Импорты** — через `@/` алиас
- **Страницы** — только композиция, никакой логики. Вся логика в виджетах/фичах/моделях
- **useSearchParams** — обёрнут в Suspense (Next.js 14 требование)
- **ProtectedRoute** — для /account, /subscription, /admin
