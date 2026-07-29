# AGENTS.md — widgets/

Слой **widgets/** — композиционные блоки (самодостаточные секции страниц). Каждый виджет — отдельная папка с `ui/`.

## Структура

```
widgets/
├── Header/ui/Header.tsx                    # Auth-aware шапка: usePathname, useUnit($isAuth) → условный рендер
├── Footer/ui/Footer.tsx                    # Server component
├── homeWidget/ui/                          # Виджет главной страницы
│   ├── index.tsx                           # HomeWidget — композиция 6 компонентов
│   ├── Hero/Hero.tsx                       # Hero-секция (DecorativeLines + текст)
│   ├── Carousel/Carousel.tsx               # Карусель преимуществ
│   ├── Advantages/Advantages.tsx           # Сетка преимуществ
│   ├── Dashboard/Dashboard.tsx             # useProductSearch (live /api/products)
│   ├── Prices/Prices.tsx                   # usePlans + useSubscription
│   └── BannerAccount/BannerAccount.tsx     # Баннер регистрации
├── AccountSidebar/ui/AccountSidebar.tsx     # Навигация: profile | subscription | history | settings
├── AccountProfile/ui/AccountProfile.tsx     # Профиль: view/edit + тариф + история + недавние
├── PlanComparison/ui/PlanComparison.tsx     # Таблица сравнения тарифов (usePlans)
├── FaqAccordion/ui/FaqAccordion.tsx         # Аккордеон FAQ (статический контент)
├── ContactWidget/ui/ContactWidget.tsx       # ContactInfo (статический) + ContactForm (react-hook-form)
├── ProductDetail/ui/ProductDetail.tsx       # Детальная товара (заглушка, useProduct)
├── AdminSidebar/ui/AdminSidebar.tsx         # Навигация админ-панели
├── AdminDashboard/ui/AdminDashboard.tsx     # Дашборд + таблицы пользователей/парсеров (заглушка)
├── SubscriptionManager/ui/SubscriptionManager.tsx  # Управление подпиской (заглушка)
└── SearchResults/ui/SearchResults.tsx       # Список + пагинация + сортировка (useProductSearch)
```

## Соглашения

- Каждый виджет — папка: `{Name}/ui/{Name}.tsx`
- Виджеты импортируют хуки из `models/` и фичи из `features/`
- Виджеты не импортируют друг друга напрямую (только через страницу в app/)
- Исключение: `homeWidget/ui/index.tsx` собирает 6 подкомпонентов в один HomeWidget
- **"use client"** — на уровне каждого файла, если нужны React-хуки
- Server Component — только Footer (нет состояния, нет событий)
- Виджеты с заглушками: ProductDetail, AdminDashboard, SubscriptionManager
