'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { CircleQuestionMark } from '../../../../shared/ui/IconSVG';

interface Plan {
  name: string;
  price: string;
  period: string;
  discount: string | null;
  featured: boolean;
  features: string[];
  tooltip: string[];
}

const plans: Plan[] = [
  {
    name: 'Базовый',
    price: '399',
    period: '/ месяц',
    discount: '−20% на первый платёж',
    featured: false,
    features: [
      'Все 5 магазинов',
      'Точный + частичный поиск',
      'До 100 товаров',
      'История цен — 3 месяца',
    ],
    tooltip: [
      'Точное + частичное совпадение',
      'До 100 отслеживаемых товаров',
      'История цен — 3 месяца',
      'Без уведомлений о падении цен',
      'Без экспорта отчётов',
      'Поддержка в рабочие часы',
    ],
  },
  {
    name: 'Продвинутый',
    price: '499',
    period: '/ месяц',
    discount: '−20% на первый платёж',
    featured: true,
    features: [
      'Все 5 магазинов',
      'Умный поиск (fuzzy)',
      'До 500 товаров',
      'Уведомления о снижении цен',
      'Экспорт PDF/CSV',
      'Поддержка 24/7',
    ],
    tooltip: [
      'Умный поиск (fuzzy) — находит при опечатках, транслитерации, другой раскладке',
      'До 500 отслеживаемых товаров',
      'Уведомления о снижении цен',
      'Экспорт отчётов PDF/CSV',
      'Поддержка 24/7',
    ],
  },
  {
    name: 'Пробный',
    price: '0',
    period: '/ 7 дней',
    discount: 'Бесплатно',
    featured: false,
    features: [
      'Все 5 магазинов',
      'Точный + частичный поиск',
      'До 10 товаров',
      'История цен — 3 месяца',
    ],
    tooltip: [
      'Точное + частичное совпадение',
      'До 10 отслеживаемых товаров',
      'История цен — 3 месяца',
      '7 дней бесплатного доступа',
      'После окончания — автоматическое продление',
    ],
  },
];

const Prices: React.FC = () => {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  const handleTooltipToggle = (name: string) => {
    setActiveTooltip((prev) => (prev === name ? null : name));
  };

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
            Попробуйте бесплатно в течение 7 дней. Далее выберите тариф под свои
            задачи.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-6 items-start max-lg:grid-cols-1 max-lg:max-w-[480px] max-lg:mx-auto">
          {plans.map((plan) => {
            const isAdvanced = plan.featured;

            return (
              <div
                key={plan.name}
                className={`relative rounded-[24px] flex flex-col ${
                  isAdvanced
                    ? 'bg-slate text-ivory p-[31px] pt-[48px] z-10 -my-4 max-lg:my-0 max-lg:pt-[31px]'
                    : 'bg-ivory-elevated p-[31px]'
                }`}
              >
                {/* Green badge — only for advanced */}
                {isAdvanced && (
                  <div className="absolute -top-[8px] left-1/2 -translate-x-1/2 bg-green-discount text-white text-[13px] font-semibold px-4 py-[6px] rounded-full whitespace-nowrap shadow-md max-lg:static max-lg:translate-x-0 max-lg:mb-4 max-lg:rounded-lg max-lg:text-center">
                    Выбирают чаще
                  </div>
                )}

                {/* Tooltip trigger */}
                <div className="absolute top-[24px] right-[24px] z-10 max-lg:relative max-lg:top-0 max-lg:right-0 max-lg:float-right max-lg:-mt-[28px]">
                  <div className="relative group">
                    <button
                      type="button"
                      className={`p-1 rounded-full transition-colors cursor-pointer ${
                        isAdvanced
                          ? 'text-ivory/50 hover:text-ivory'
                          : 'text-body-muted hover:text-body'
                      }`}
                      onClick={() => handleTooltipToggle(plan.name)}
                      aria-label={`Подробнее о тарифе ${plan.name}`}
                    >
                      <CircleQuestionMark width={18} height={18} />
                    </button>

                    <div
                      className={`absolute right-0 top-full mt-2 w-[280px] p-3 rounded-xl text-[13px] leading-[1.5] shadow-lg border pointer-events-none opacity-0 scale-95 transition-all duration-200 origin-top-right group-hover:opacity-100 group-hover:scale-100 ${
                        activeTooltip === plan.name
                          ? '!opacity-100 !scale-100'
                          : ''
                      } ${
                        isAdvanced
                          ? 'bg-ivory text-body border-border-light'
                          : 'bg-white text-body border-border-light'
                      }`}
                      role="tooltip"
                    >
                      <ul className="list-none m-0 p-0">
                        {plan.tooltip.map((item) => (
                          <li key={item} className="py-[2px]">
                            — {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Label */}
                <span
                  className={`block font-montserrat text-[11px] uppercase tracking-[0.08em] mb-4 pb-3 border-b ${
                    isAdvanced
                      ? 'text-ivory/60 border-ivory/15'
                      : 'text-body-muted border-border-light'
                  }`}
                >
                  {isAdvanced ? 'Продвинутый' : plan.name}
                </span>

                {/* Price */}
                <div
                  className={`text-[40px] font-bold leading-none mb-2 ${
                    isAdvanced ? 'text-ivory' : 'text-slate'
                  }`}
                >
                  {plan.price} ₽{' '}
                  <span className="text-base font-normal text-body-subtle">
                    {plan.period}
                  </span>
                </div>

                {/* Discount */}
                {plan.discount && (
                  <span className="inline-block text-[13px] font-semibold text-green-discount mt-2">
                    {plan.discount}
                  </span>
                )}

                {/* Features */}
                <ul className="my-6 flex-1">
                  {plan.features.map((feature) => (
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

                {/* CTA */}
                {isAdvanced ? (
                  <Link
                    href="/register?plan=advanced"
                    className="block w-full text-center py-3 text-[15px] font-medium no-underline bg-ivory text-slate border border-ivory transition-colors hover:bg-ivory-elevated"
                  >
                    Выбрать Продвинутый
                  </Link>
                ) : plan.name === 'Пробный' ? (
                  <Link
                    href="/register"
                    className="block w-full text-center py-3 text-[15px] font-medium no-underline bg-transparent text-slate border border-slate transition-colors hover:bg-ivory-elevated"
                  >
                    Выбрать Пробный
                  </Link>
                ) : (
                  <Link
                    href="/register?plan=basic"
                    className="block w-full text-center py-3 text-[15px] font-medium no-underline bg-transparent text-slate border border-slate transition-colors hover:bg-ivory-elevated"
                  >
                    Выбрать Базовый
                  </Link>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Prices;
