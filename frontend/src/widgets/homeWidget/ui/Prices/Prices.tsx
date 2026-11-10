'use client';

import Link from 'next/link';
import { usePlans } from '@/models/payment';
import { planFeatures } from '@/widgets/TariffPlans/ui/TariffPlans';
import { formatTariffAmount } from '@/shared/lib/format';

export default function Prices() {
  const plans = usePlans();
  const ordered = plans.data ? [...plans.data].sort((a, b) => a.sortOrder - b.sortOrder) : [];
  return (
    <section id="tariffs" className="guest-section guest-tariffs relative flex items-center py-24">
      <div className="relative mx-auto w-full max-w-[1200px] px-6">
        <div className="mb-5 text-center"><p className="text-sm font-semibold uppercase tracking-[.15em] text-positive">Выберите план</p><h2 className="sr-only">Тарифы</h2><p className="mt-3 text-body-subtle">Актуальные условия из каталога тарифов BScout</p></div>
        <div className="pointer-events-none text-center text-[clamp(5rem,15vw,12rem)] font-bold leading-none tracking-[-.07em] text-slate/10" aria-hidden="true">Тарифы</div>
        {plans.isLoading && <p className="mt-14 text-center text-body-subtle">Загружаем тарифы…</p>}
        {plans.isError && <p className="mt-14 text-center text-body-subtle">Не удалось загрузить тарифы. <Link href="/tariffs" className="underline">Открыть страницу тарифов</Link></p>}
        {ordered.length > 0 && <div className="relative mt-8 grid gap-6 lg:-mt-12 lg:grid-cols-3">{ordered.map((plan) => <article key={plan.plan} className="tariff-home-card flex min-h-[480px] flex-col rounded-[30px] p-8 text-slate"><p className="text-sm font-bold uppercase tracking-[.1em] text-body-subtle">{plan.nameRu}</p><p className="mt-7 text-[clamp(2.5rem,4vw,4rem)] font-bold leading-none">{formatTariffAmount(plan.price)} ₽</p><p className="mt-2 text-sm text-body-subtle">за {plan.durationDays} дней</p><ul className="my-9 flex-1 space-y-4">{planFeatures(plan).map((feature) => <li key={feature} className="flex gap-3 text-sm leading-snug"><span className="font-bold text-positive" aria-hidden="true">✓</span>{feature}</li>)}</ul><Link href={plan.plan === 'trial' ? '/register' : `/register?plan=${plan.plan}`} className="btn-primary text-center">{plan.price === 0 ? 'Попробовать' : 'Выбрать'}</Link></article>)}</div>}
      </div>
    </section>
  );
}
