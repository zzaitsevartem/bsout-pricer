'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { CircleQuestionMark } from '@/shared/ui/IconSVG';
import { usePlans } from '@/models/payment';
import type { PlanResponse } from '@/models/payment';

const ORDER: Record<string, number> = { basic: 0, advanced: 1, trial: 2 };

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

function planFeatures(plan: PlanResponse): string[] {
  const features = [
    `${plan.stores} магазинов в поиске`,
    plan.fuzzySearch ? 'Умный поиск (fuzzy)' : 'Точный и частичный поиск',
    `До ${plan.trackedProducts} отслеживаемых товаров`,
  ];
  if (plan.priceAlerts) {
    features.push('Уведомления о снижении цен');
  }
  if (plan.exportReports) {
    features.push('Экспорт отчётов PDF/CSV');
  }
  if (plan.supportRu && plan.supportRu !== '—') {
    features.push(`Поддержка: ${plan.supportRu}`);
  }
  return features;
}

function planTooltip(plan: PlanResponse): string[] {
  const items = [...planFeatures(plan)];
  if (!plan.priceAlerts) {
    items.push('Без уведомлений о снижении цен');
  }
  if (!plan.exportReports) {
    items.push('Без экспорта отчётов');
  }
  items.push(
    plan.price === 0
      ? `${formatDays(plan.durationDays)} бесплатного доступа`
      : `Период оплаты — ${formatDays(plan.durationDays)}`,
  );
  return items;
}

const Prices: React.FC = () => {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);
  const plans = usePlans();

  const handleTooltipToggle = (name: string) => {
    setActiveTooltip((prev) => (prev === name ? null : name));
  };

  const trial = plans.data?.find((plan) => plan.plan === 'trial');
  const ordered = plans.data
    ? [...plans.data].sort((a, b) => (ORDER[a.plan] ?? 99) - (ORDER[b.plan] ?? 99))
    : [];

  return (
    <section className="bg-ivory py-[84px] max-md:py-[61px] max-[480px]:py-[48px]">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="text-center mb-24">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Тарифы
          </p>
          <h2 className="text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] mb-6 text-slate max-md:text-[32px]">
            Выберите подходящий план
          </h2>
          <p className="text-lg leading-[1.4] text-body max-w-[64ch] mx-auto max-md:text-base">
            {trial
              ? `Попробуйте бесплатно в течение ${formatDays(trial.durationDays)}. Далее выберите тариф под свои задачи.`
              : 'Выберите тариф под свои задачи.'}
          </p>
        </div>

        {plans.isLoading && (
          <p className="text-center text-[15px] text-body-subtle">Загружаем тарифы…</p>
        )}

        {plans.isError && (
          <p className="text-center text-[15px] text-body-subtle">
            Не удалось загрузить тарифы.{' '}
            <Link href="/tariffs" className="text-slate font-medium no-underline hover:underline">
              Открыть страницу тарифов
            </Link>
          </p>
        )}

        {ordered.length > 0 && (
          <div className="grid grid-cols-3 gap-6 items-start max-lg:grid-cols-1 max-lg:max-w-[480px] max-lg:mx-auto">
            {ordered.map((plan) => {
              const isAdvanced = plan.plan === 'advanced';
              const isFree = plan.price === 0;
              const href = plan.plan === 'trial' ? '/register' : `/register?plan=${plan.plan}`;

              return (
                <div
                  key={plan.plan}
                  className={`relative rounded-[24px] flex flex-col ${
                    isAdvanced
                      ? 'bg-slate text-ivory p-[31px] pt-[48px] z-10 -my-4 max-lg:my-0 max-lg:pt-[31px]'
                      : 'bg-ivory-elevated p-[31px]'
                  }`}
                >
                  {isAdvanced && (
                    <div className="absolute -top-[8px] left-1/2 -translate-x-1/2 bg-green-discount text-white text-[13px] font-semibold px-4 py-[6px] rounded-full whitespace-nowrap shadow-md max-lg:static max-lg:translate-x-0 max-lg:mb-4 max-lg:rounded-lg max-lg:text-center">
                      Выбирают чаще
                    </div>
                  )}

                  <div className="absolute top-[24px] right-[24px] z-10 max-lg:relative max-lg:top-0 max-lg:right-0 max-lg:float-right max-lg:-mt-[28px]">
                    <div className="relative group">
                      <button
                        type="button"
                        className={`p-1 rounded-full transition-colors cursor-pointer ${
                          isAdvanced
                            ? 'text-ivory/50 hover:text-ivory'
                            : 'text-body-muted hover:text-body'
                        }`}
                        onClick={() => handleTooltipToggle(plan.plan)}
                        aria-label={`Подробнее о тарифе ${plan.nameRu}`}
                      >
                        <CircleQuestionMark width={18} height={18} />
                      </button>

                      <div
                        className={`absolute right-0 top-full mt-2 w-[280px] p-3 rounded-xl text-[13px] leading-[1.5] shadow-lg border pointer-events-none opacity-0 scale-95 transition-all duration-200 origin-top-right group-hover:opacity-100 group-hover:scale-100 ${
                          activeTooltip === plan.plan ? '!opacity-100 !scale-100' : ''
                        } ${
                          isAdvanced
                            ? 'bg-ivory text-body border-border-light'
                            : 'bg-white text-body border-border-light'
                        }`}
                        role="tooltip"
                      >
                        <ul className="list-none m-0 p-0">
                          {planTooltip(plan).map((item) => (
                            <li key={item} className="py-[2px]">
                              — {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  <span
                    className={`block font-montserrat text-[11px] uppercase tracking-[0.08em] mb-4 pb-3 border-b ${
                      isAdvanced
                        ? 'text-ivory/60 border-ivory/15'
                        : 'text-body-muted border-border-light'
                    }`}
                  >
                    {plan.nameRu}
                  </span>

                  <div
                    className={`text-[40px] font-bold leading-none mb-2 ${
                      isAdvanced ? 'text-ivory' : 'text-slate'
                    }`}
                  >
                    {formatAmount(plan.price)} ₽{' '}
                    <span className="text-base font-normal text-body-subtle">
                      / {formatDays(plan.durationDays)}
                    </span>
                  </div>

                  <span className="inline-block text-[13px] font-semibold text-green-discount mt-2">
                    {isFree
                      ? 'Бесплатно'
                      : plan.firstPaymentPrice < plan.price
                        ? `Первый платёж — ${formatAmount(plan.firstPaymentPrice)} ₽ (−20%)`
                        : ''}
                  </span>

                  <ul className="my-6 flex-1">
                    {planFeatures(plan).map((feature) => (
                      <li
                        key={feature}
                        className={`flex items-start gap-3 py-[6px] text-[15px] ${
                          isAdvanced ? 'text-[#D1CFC5]' : 'text-body'
                        }`}
                      >
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 16 16"
                          fill="none"
                          className="flex-shrink-0 mt-0.5"
                        >
                          <path
                            d="M13.5 4.5L6 12L2.5 8.5"
                            stroke="#788C5D"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Link
                    href={href}
                    className={`block w-full text-center py-3 text-[15px] font-medium no-underline transition-colors ${
                      isAdvanced
                        ? 'bg-ivory text-slate border border-ivory hover:bg-ivory-elevated'
                        : 'bg-transparent text-slate border border-slate hover:bg-ivory-elevated'
                    }`}
                  >
                    Выбрать {plan.nameRu}
                  </Link>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
};

export default Prices;
