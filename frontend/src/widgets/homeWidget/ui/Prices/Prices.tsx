import React from 'react';
import Link from 'next/link';

const plans = [
  {
    name: 'Пробный',
    price: '0',
    period: '/ 10 дней',
    discount: null,
    featured: false,
    features: ['До 10 товаров в поиске', 'До 2 поставщиков', 'Обновление цен — 24ч', 'История цен — 1 месяц'],
  },
  {
    name: 'Базовый',
    price: '399',
    period: '/ месяц',
    discount: '−20% на первый платёж',
    featured: true,
    features: ['До 100 товаров в поиске', 'До 15+ поставщиков', 'Обновление цен — 6ч', 'История цен — 6 месяцев', 'Экспорт PDF/CSV', 'Поддержка 24/7'],
  },
  {
    name: 'Продвинутый',
    price: '499',
    period: '/ месяц',
    discount: '−20% на первый платёж',
    featured: false,
    features: ['Безлимитный поиск', '50+ поставщиков', 'Обновление в real-time', 'История цен — 12+ месяцев', 'Нечёткий поиск (fuzzy)', 'API-доступ', 'Расширенная аналитика', 'Персональный менеджер'],
  },
];

const Prices: React.FC = () => {
  return (
    <section className="bg-ivory py-[84px] max-md:py-[61px] max-[480px]:py-[48px]">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="text-center mb-8">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Тарифы</p>
          <h2 className="text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] mb-6 text-slate">
            Выберите подходящий план
          </h2>
          <p className="text-lg leading-[1.4] text-body max-w-[64ch] mx-auto">
            Попробуйте бесплатно в течение 10 дней. Далее выберите тариф под свои задачи.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-6 items-start max-lg:grid-cols-1 max-lg:max-w-[480px] max-lg:mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-[24px] p-[31px] flex flex-col ${
                plan.featured ? 'bg-slate text-ivory' : 'bg-ivory-elevated'
              }`}
            >
              <span className={`inline-block font-montserrat text-xs uppercase tracking-[0.04em] px-2 py-1 mb-4 ${
                plan.featured ? 'bg-ivory-warm text-slate' : 'bg-ivory-warm text-body-muted'
              }`}>
                {plan.featured ? 'Популярный' : plan.name}
              </span>
              <div className={`text-[40px] font-bold leading-none mb-2 ${
                plan.featured ? 'text-ivory' : 'text-slate'
              }`}>
                {plan.price} ₽{' '}
                <span className="text-base font-normal text-body-subtle">{plan.period}</span>
              </div>
              {plan.discount && (
                <span className="inline-block text-[13px] font-semibold text-green-discount mt-2">
                  {plan.discount}
                </span>
              )}
              <ul className="my-6 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className={`flex items-start gap-3 py-[6px] text-[15px] ${
                    plan.featured ? 'text-[#D1CFC5]' : 'text-body'
                  }`}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="flex-shrink-0 mt-0.5">
                      <path d="M13.5 4.5L6 12L2.5 8.5" stroke="#788C5D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
              {plan.featured ? (
                <Link
                  href="/register?plan=basic"
                  className="block w-full text-center py-3 text-[15px] font-medium no-underline bg-ivory text-slate border border-ivory transition-colors hover:bg-ivory-elevated"
                >
                  Выбрать Базовый
                </Link>
              ) : (
                <Link
                  href="/register"
                  className="block w-full text-center py-3 text-[15px] font-medium no-underline bg-transparent text-slate border border-slate transition-colors hover:bg-ivory-elevated"
                >
                  {plan.name === 'Пробный' ? 'Попробовать' : 'Выбрать Продвинутый'}
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Prices;
