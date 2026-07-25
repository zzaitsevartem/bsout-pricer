'use client';

import React from 'react';
import Link from 'next/link';
import { useUnit } from 'effector-react';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { $isAuth } from '@/shared/config/store';
import { usePlans } from '@/models/payment';
import type { PlanResponse } from '@/models/payment';

function formatAmount(value: number): string {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDays(days: number): string {
  const tail = days % 10;
  const teen = days % 100;
  if (teen >= 11 && teen <= 14) {
    return `${days} дней`;
  }
  if (tail === 1) {
    return `${days} день`;
  }
  if (tail >= 2 && tail <= 4) {
    return `${days} дня`;
  }
  return `${days} дней`;
}

function yesNo(value: boolean): string {
  return value ? '✓' : '—';
}

const ROWS: { label: string; value: (plan: PlanResponse) => string; bold?: boolean }[] = [
  {
    label: 'Цена',
    value: (plan) =>
      plan.price === 0 ? 'Бесплатно' : `${formatAmount(plan.price)} ₽ / ${formatDays(plan.durationDays)}`,
    bold: true,
  },
  {
    label: 'Первый платёж',
    value: (plan) =>
      plan.price === 0
        ? '—'
        : plan.firstPaymentPrice < plan.price
          ? `${formatAmount(plan.firstPaymentPrice)} ₽ (−20%)`
          : `${formatAmount(plan.firstPaymentPrice)} ₽`,
  },
  { label: 'Длительность периода', value: (plan) => formatDays(plan.durationDays) },
  { label: 'Отслеживаемые товары', value: (plan) => `до ${plan.trackedProducts}` },
  { label: 'Магазины в поиске', value: (plan) => String(plan.stores) },
  { label: 'Умный поиск (fuzzy)', value: (plan) => yesNo(plan.fuzzySearch) },
  { label: 'Уведомления о снижении цены', value: (plan) => yesNo(plan.priceAlerts) },
  { label: 'Экспорт отчётов (PDF/CSV)', value: (plan) => yesNo(plan.exportReports) },
  { label: 'Поддержка', value: (plan) => plan.supportRu },
];

export default function TariffsPage() {
  const isAuth = useUnit($isAuth);
  const plans = usePlans();

  const trial = plans.data?.find((plan) => plan.plan === 'trial');

  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</a>
          <span className="text-body-muted">/</span>
          <span>Тарифы</span>
        </div>

        <div className="text-center border-b-0 pt-0 max-w-[600px] mx-auto mb-12">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Тарифы</p>
          <h1 className="text-[40px] font-semibold text-slate mb-2">Выберите свой план</h1>
          <p className="text-lg text-body">
            {trial
              ? `Начните с бесплатного пробного периода на ${formatDays(trial.durationDays)}. Затем выберите тариф, который подходит вашим задачам.`
              : 'Выберите тариф, который подходит вашим задачам.'}
          </p>
        </div>

        {plans.isLoading && (
          <p className="text-center text-[15px] text-body-subtle mb-12">Загружаем тарифы…</p>
        )}

        {plans.isError && (
          <div className="border border-slate bg-ivory-elevated p-6 text-center mb-12">
            <p className="text-[15px] text-body mb-4">Не удалось загрузить тарифы. Попробуйте обновить страницу.</p>
            <button onClick={() => plans.refetch()} className="btn btn-secondary btn-sm">
              Повторить
            </button>
          </div>
        )}

        {plans.data && plans.data.length > 0 && (
          <div className="overflow-x-auto border border-slate bg-ivory mb-12">
            <table className="w-full border-collapse text-[15px]">
              <thead>
                <tr className="bg-ivory-elevated border-b border-slate">
                  <th className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap w-[30%]">Возможности</th>
                  {plans.data.map((plan, index) => (
                    <th
                      key={plan.plan}
                      className={`font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-center px-4 py-3 whitespace-nowrap w-[23.33%] ${index === 1 ? 'text-ivory bg-slate' : 'text-body-muted'}`}
                    >
                      {plan.nameRu}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((row) => (
                  <tr key={row.label}>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle font-medium text-body">{row.label}</td>
                    {plans.data.map((plan, index) => {
                      const value = row.value(plan);
                      return (
                        <td
                          key={plan.plan}
                          className={`px-4 py-[14px] border-b border-border-light-subtle text-center ${index === 1 ? 'bg-ivory-elevated' : ''} ${row.bold ? 'font-bold' : ''} ${value === '—' ? 'text-body-muted' : 'text-body'}`}
                        >
                          {value}
                        </td>
                      );
                    })}
                  </tr>
                ))}
                <tr>
                  <td className="px-4 py-[14px] border-b border-border-light-subtle"></td>
                  {plans.data.map((plan, index) => {
                    const href = plan.plan === 'trial' ? '/register' : `/register?plan=${plan.plan}`;
                    return (
                      <td key={plan.plan} className={`px-4 py-5 text-center ${index === 1 ? 'bg-ivory-elevated' : ''}`}>
                        <Link
                          href={isAuth ? '/subscription' : href}
                          className={`btn ${index === 1 ? 'btn-primary' : 'btn-secondary'} btn-sm no-underline`}
                        >
                          {plan.plan === 'trial' ? 'Попробовать' : 'Выбрать'}
                        </Link>
                      </td>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>
        )}

        <p className="text-center text-[14px] text-body-muted max-w-[500px] mx-auto">
          Скидка 20% на первый платёж любого платного тарифа. Отмена подписки в любой момент — доступ сохраняется до конца оплаченного периода.
        </p>
      </div>
      <Footer />
    </>
  );
}
