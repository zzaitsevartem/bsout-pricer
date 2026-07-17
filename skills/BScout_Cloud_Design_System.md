# BScout Cloud Design System v2

## Концепция

Дизайн выполнен в стиле **Cloud SaaS / Cloud Code**:
- Светлая облачная эстетика
- Glassmorphism
- Soft UI (Soft Shadows)
- Минимализм уровня Stripe, Linear, Vercel, Clerk, Supabase Cloud
- Воздушные белые фоны
- Голубые и фиолетовые акценты
- Большие скругления
- Полупрозрачные карточки
- Эффект облаков на фоне
- Максимум свободного пространства

---

# Визуальное позиционирование

BScout должен выглядеть не как каталог запчастей, а как:

> Облачная AI-платформа для поиска и аналитики рынка запчастей.

Ощущение:

- современно
- дорого
- технологично
- премиально
- легко
- безопасно
- cloud-native

---

# Цветовая система

## Primary

```css
--primary: #386BFF;
--primary-hover: #2858E8;
--primary-light: #EEF4FF;
```

## Secondary

```css
--secondary: #8B5CF6;
--secondary-light: #F4EFFF;
```

## Text

```css
--text-primary: #0F172A;
--text-secondary: #64748B;
```

## Surface

```css
--surface: #FFFFFF;
--surface-secondary: #F8FAFC;
```

## Borders

```css
--border: rgba(15,23,42,0.08);
```

---

# Фон

Основной фон:

```css
background:
linear-gradient(
180deg,
#F8FAFF 0%,
#FFFFFF 30%,
#F6F9FF 100%
);
```

Дополнительно:

- размытые облака
- blur circles
- soft gradients

---

# Типографика

## Основной шрифт

Inter

Вес:

- 400
- 500
- 600
- 700

## Альтернативы

- Geist
- Plus Jakarta Sans
- Manrope

Рекомендуется:

```tsx
import { Inter } from "next/font/google"
```

---

# Стек UI

## Framework

- Next.js 15
- React 19
- TypeScript

## Styling

- Tailwind CSS v4
- tailwind-merge
- clsx

## Components

- shadcn/ui

## Animations

- Framer Motion

## Icons

- Lucide React

## Charts

- Recharts

## Forms

- React Hook Form
- Zod

---

# Архитектура

Feature Sliced Design

```text
src/

app/
widgets/
features/
entities/
shared/
```

---

# Header

Высота:

```css
72px
```

Стиль:

```css
background: rgba(255,255,255,.75);
backdrop-filter: blur(20px);
```

Содержимое:

- Логотип
- Возможности
- Тарифы
- Магазины
- API
- Поддержка

Справа:

- Войти
- Попробовать бесплатно

---

# Hero

Левая колонка:

Заголовок:

```text
Найдите лучшую цену
на запчасти для электроники
```

Подзаголовок:

```text
Сравнивайте цены среди локальных магазинов
и экономьте время и деньги
```

Карточки преимуществ:

- 5 магазинов
- Актуальные цены
- Умный поиск

Кнопки:

Primary:

```text
Попробовать бесплатно
```

Secondary:

```text
Как это работает
```

---

# Правая часть Hero

Большой Cloud Dashboard.

Размер:

```css
720x430
```

Карточка:

```css
border-radius: 32px;
background: rgba(255,255,255,.85);
backdrop-filter: blur(24px);
```

Внутри:

- поиск
- категории
- результаты
- фильтры
- карточки товаров

---

# Карточка лучшего предложения

Стиль:

```css
border: 2px solid #386BFF;
box-shadow:
0 10px 40px rgba(56,107,255,.15);
```

Плашка:

```text
Самый дешёвый
```

Цвет:

```css
#FFD54A
```

---

# Блок магазинов

Карточки:

```css
height: 72px;
border-radius: 20px;
```

Логотипы:

- ТГСМ
- Профи
- Liberty
- GreenSpark
- Дивизион

---

# Блок преимуществ

3 карточки

Размер:

```css
320x240
```

Эффект:

```css
background: rgba(255,255,255,.8);
backdrop-filter: blur(20px);
```

Иконки:

- Search
- Shield
- Sparkles

---

# Тарифы

3 карточки

## Trial

0 ₽

## Basic

990 ₽

## Pro

2490 ₽

Популярный:

```css
border: 2px solid #8B5CF6;
```

Кнопка:

```css
background:
linear-gradient(
135deg,
#386BFF,
#8B5CF6
);
```

---

# Dashboard

Сетка:

```text
┌─────────┬─────────┬─────────┬─────────┐
│ KPI     │ KPI     │ KPI     │ KPI     │
├─────────┴─────────┬─────────┴─────────┤
│ График            │ Поиски            │
├───────────────────┴───────────────────┤
│ Последние товары                      │
└───────────────────────────────────────┘
```

Карточки:

```css
border-radius: 24px;
```

---

# Личный кабинет

Меню:

- Главная
- Поиск
- Избранное
- История
- Подписка
- API
- Настройки

Стиль:

Cloud Sidebar

```css
width: 260px;
```

---

# Glassmorphism правила

Все карточки:

```css
background:
rgba(255,255,255,.8);

backdrop-filter:
blur(24px);

border:
1px solid rgba(255,255,255,.6);
```

---

# Тени

Маленькая

```css
0 4px 20px rgba(15,23,42,.06)
```

Средняя

```css
0 10px 40px rgba(15,23,42,.08)
```

Большая

```css
0 20px 60px rgba(15,23,42,.12)
```

---

# Скругления

```css
button: 14px;
card: 24px;
dashboard: 32px;
hero: 32px;
```

---

# Анимации

Framer Motion

Hover:

```tsx
whileHover={{
  y: -4,
  scale: 1.01
}}
```

Появление:

```tsx
initial={{ opacity:0,y:20 }}
animate={{ opacity:1,y:0 }}
```

---

# Cloud UI элементы

Обязательно использовать:

- Cloud background blobs
- Floating gradients
- Blur circles
- Glass cards
- Soft shadows
- Floating dashboard mockups

Запрещено:

- тёмный фон
- киберпанк
- кислотные цвета
- тяжёлые рамки
- резкие тени

---

# Референсы

Дизайн должен визуально находиться между:

- Stripe
- Linear
- Vercel
- Clerk
- Notion
- Raycast
- Supabase
- Dropbox Dash

Цель:

Создать ощущение облачной AI-платформы стоимостью десятки миллионов рублей, а не обычного агрегатора запчастей.
