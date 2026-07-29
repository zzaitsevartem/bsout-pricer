'use client';

import React from 'react';
import Link from 'next/link';
import { useUnit } from 'effector-react';
import { $isAuth } from '../../models/auth/store';
import { useSubscription } from '../../models/user';
import { usePlans } from '../../models/plan';
import type { PlanResponse } from '../../models/plan';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

const FALLBACK_PLANS: PlanResponse[] = [
  {
    slug: 'trial',
    name: 'Пробный',
    price: '0',
    period: '/ 10 дней',
    discount: 'Бесплатно',
    featured: false,
    features: [],
    tooltips: [],
  },
  {
    slug: 'basic',
    name: 'Базовый',
    price: '399',
    period: '/ месяц',
    discount: '−20% на первый платёж',
    featured: false,
    features: [],
    tooltips: [],
  },
  {
    slug: 'advanced',
    name: 'Продвинутый',
    price: '499',
    period: '/ месяц',
    discount: '−20% на первый платёж',
    featured: false,
    features: [],
    tooltips: [],
  },
];

interface ComparisonRow {
  label: string;
  values: Record<string, string>;
  bold?: boolean;
}

const COMPARISON_ROWS: ComparisonRow[] = [
  {
    label: 'Цена',
    values: { trial: '0 ₽ / 10 дней', basic: '399 ₽ / месяц', advanced: '499 ₽ / месяц' },
    bold: true,
  },
  {
    label: 'Количество товаров',
    values: { trial: 'до 10', basic: 'до 100', advanced: 'безлимит' },
  },
  {
    label: 'Количество поставщиков',
    values: { trial: '2', basic: '15+', advanced: '50+' },
  },
  {
    label: 'Обновление цен',
    values: { trial: '24ч', basic: '6ч', advanced: 'real-time' },
  },
  {
    label: 'История цен',
    values: { trial: '1 месяц', basic: '6 месяцев', advanced: '12+ месяцев' },
  },
  {
    label: 'Экспорт отчётов (PDF/CSV)',
    values: { trial: '—', basic: '✓', advanced: '✓' },
  },
  {
    label: 'Нечёткий поиск (fuzzy)',
    values: { trial: '—', basic: '—', advanced: '✓' },
  },
  {
    label: 'API-доступ',
    values: { trial: '—', basic: '—', advanced: '✓' },
  },
  {
    label: 'Расширенная аналитика',
    values: { trial: '—', basic: '—', advanced: '✓' },
  },
  {
    label: 'Поддержка',
    values: { trial: '—', basic: '24/7', advanced: '24/7 + менеджер' },
  },
];

const SLUGS = ['trial', 'basic', 'advanced'] as const;

const planNameMap: Record<string, string> = {
  trial: 'Пробный',
  basic: 'Базовый',
  advanced: 'Продвинутый',
};

export default function TariffsPage() {
  const isAuth = useUnit($isAuth);
  const { data: subscription } = useSubscription({ enabled: isAuth });
  const { data: plansData, isLoading } = usePlans();

  const plans = plansData ?? FALLBACK_PLANS;
  const plansBySlug = Object.fromEntries(plans.map((p) => [p.slug, p]));
  const currentPlanSlug = subscription?.is_active ? subscription.plan : null;

  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">
            Главная
          </a>
          <span className="text-body-muted">/</span>
          <span>Тарифы</span>
        </div>

        <div className="text-center border-b-0 pt-0 max-w-[600px] mx-auto mb-12">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Тарифы
          </p>
          <h1 className="text-[40px] font-semibold text-slate mb-2">Выберите свой план</h1>
          <p className="text-lg text-body">
            Начните с бесплатного пробного периода на 10 дней. Затем выберите тариф,
            который подходит вашим задачам.
          </p>

          {isLoading && (
            <p className="mt-4 text-sm text-body-muted">Загрузка тарифов…</p>
          )}

          {currentPlanSlug && (
            <p className="mt-4 text-sm text-body-muted">
              Ваш текущий тариф:{' '}
              <span className="font-semibold text-slate">
                {planNameMap[currentPlanSlug] ?? currentPlanSlug}
              </span>
            </p>
          )}
        </div>

        <div className="overflow-x-auto border border-slate bg-ivory mb-12">
          <table className="w-full border-collapse text-[15px]">
            <thead>
              <tr className="bg-ivory-elevated border-b border-slate">
                <th className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap w-[30%]">
                  Возможности
                </th>
                {SLUGS.map((slug, idx) => {
                  const plan = plansBySlug[slug];
                  const isCurrent = slug === currentPlanSlug;
                  return (
                    <th
                      key={slug}
                      className={`font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-center px-4 py-3 whitespace-nowrap ${
                        idx === 1
                          ? 'bg-slate text-ivory'
                          : 'text-body-muted'
                      } ${isCurrent ? 'ring-2 ring-green-discount ring-inset' : ''}`}
                      style={{ width: '23.33%' }}
                    >
                      {plan?.name ?? planNameMap[slug]}{' '}
                      {isCurrent && (
                        <span className="block text-[11px] font-normal mt-0.5 text-green-discount">
                          • ваш план
                        </span>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row, i) => (
                <tr key={i}>
                  <td className="px-4 py-[14px] border-b border-border-light-subtle font-medium text-body">
                    {row.label}
                  </td>
                  {SLUGS.map((slug, j) => {
                    const val = row.values[slug] ?? '—';
                    const isDimmed =
                      val === '—' && slug !== 'trial';
                    return (
                      <td
                        key={slug}
                        className={`px-4 py-[14px] border-b border-border-light-subtle text-center ${
                          j === 1 ? 'bg-ivory-elevated' : ''
                        } ${row.bold ? 'font-bold' : ''} ${
                          isDimmed ? 'text-body-muted' : 'text-body'
                        }`}
                      >
                        {val}
                      </td>
                    );
                  })}
                </tr>
              ))}
              <tr>
                <td className="px-4 py-[14px] border-b border-border-light-subtle" />
                {SLUGS.map((slug, j) => {
                  const isCurrent = slug === currentPlanSlug;
                  let href: string;
                  let label: string;
                  let btnClass: string;

                  if (isCurrent) {
                    href = '/subscription';
                    label = 'Управлять';
                    btnClass = 'btn-secondary btn-sm no-underline';
                  } else if (slug === 'trial') {
                    href = '/register';
                    label = 'Попробовать';
                    btnClass = 'btn-secondary btn-sm no-underline';
                  } else {
                    href = `/register?plan=${slug}`;
                    label = 'Выбрать';
                    btnClass = j === 1 ? 'btn-primary btn-sm no-underline' : 'btn-secondary btn-sm no-underline';
                  }

                  return (
                    <td
                      key={slug}
                      className={`px-4 py-5 text-center ${j === 1 ? 'bg-ivory-elevated' : ''}`}
                    >
                      <Link href={href} className={btnClass}>
                        {label}
                      </Link>
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>

        <p className="text-center text-[14px] text-body-muted max-w-[500px] mx-auto">
          Скидка 20% на первый платёж любого платного тарифа. Отмена подписки в любой момент.
        </p>
      </div>
      <Footer />
    </>
  );
}
