'use client';

import React from 'react';
import { TariffPlans } from '@/widgets/TariffPlans';
import { usePlans } from '@/models/payment';

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

const Prices: React.FC = () => {
  const plans = usePlans();

  const trial = plans.data?.find((plan) => plan.plan === 'trial');

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

        <TariffPlans action="register" />
      </div>
    </section>
  );
};

export default Prices;
