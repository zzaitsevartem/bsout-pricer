'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useSubscription } from '@/models/user';
import { useSubscribe, useCancelSubscription } from '@/models/payment';
import type { Plan } from '@/models/user';
import { formatDate, planLabel, planPrice } from '@/shared/lib/format';

const PLANS: {
  plan: Plan;
  name: string;
  price: string;
  period: string;
  features: string[];
  featured: boolean;
}[] = [
  { plan: 'trial', name: 'Пробный', price: '0', period: '', features: ['До 10 товаров', '2 поставщика', 'Обновление 24ч'], featured: false },
  { plan: 'basic', name: 'Базовый', price: '399', period: '/ мес', features: ['До 100 товаров', '15+ поставщиков', 'Обновление 6ч', 'Экспорт PDF/CSV', 'Поддержка 24/7'], featured: true },
  { plan: 'advanced', name: 'Продвинутый', price: '499', period: '/ мес', features: ['Безлимитный поиск', '50+ поставщиков', 'Real-time обновление', 'Нечёткий поиск', 'API-доступ', 'Персональный менеджер'], featured: false },
];

function SubscriptionContent() {
  const subscription = useSubscription();
  const subscribe = useSubscribe();
  const cancel = useCancelSubscription();

  const currentPlan = subscription.data?.plan;

  const handleSubscribe = (plan: Plan) => {
    subscribe.mutate({ plan, payment_method: 'card' });
  };

  const handleCancel = () => {
    if (window.confirm('Отменить подписку? Тариф будет действовать до конца оплаченного периода.')) {
      cancel.mutate();
    }
  };

  return (
    <>
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main>
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Управление подпиской</h2>

              <div className="rounded-[24px] p-[31px] bg-ivory-elevated mb-8">
                {subscription.isLoading ? (
                  <p className="text-body-subtle mb-0">Загрузка…</p>
                ) : subscription.data ? (
                  <div className="flex justify-between items-start flex-wrap gap-4">
                    <div>
                      <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Текущий тариф</p>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="inline-flex items-center px-4 py-[6px] text-[14px] font-semibold bg-ivory-elevated text-slate border border-slate">{planLabel(subscription.data.plan)}</span>
                        <span className="text-[14px] text-body-subtle">{planPrice(subscription.data.plan)}</span>
                      </div>
                      <p className="text-[15px] text-body-subtle mt-2 mb-0">
                        Действует до {formatDate(subscription.data.end_date)} · {subscription.data.auto_renew ? 'Автопродление включено' : 'Автопродление выключено'}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-center flex-wrap gap-4">
                    <p className="text-[15px] text-body-subtle mb-0">У вас нет активной подписки. Выберите тариф ниже.</p>
                  </div>
                )}
              </div>

              <h3 className="text-2xl font-semibold text-slate mb-4">{currentPlan ? 'Сменить тариф' : 'Выбрать тариф'}</h3>

              {subscribe.isError && (
                <p className="text-[14px] text-clay mb-4">Не удалось изменить тариф. Попробуйте позже.</p>
              )}

              <div className="grid grid-cols-3 gap-6 items-start mb-8 max-lg:grid-cols-1 max-lg:max-w-[480px] max-lg:mx-auto">
                {PLANS.map((planItem) => {
                  const isCurrent = currentPlan === planItem.plan;
                  const isPending = subscribe.isPending && subscribe.variables?.plan === planItem.plan;
                  return (
                    <div key={planItem.plan} className={`rounded-[24px] p-[31px] flex flex-col ${planItem.featured ? 'bg-slate text-ivory' : 'bg-ivory-elevated'}`}>
                      <span className={`inline-block font-montserrat text-xs uppercase tracking-[0.04em] px-2 py-1 mb-4 ${planItem.featured ? 'bg-clay text-ivory' : 'bg-ivory-warm text-body-muted'}`}>
                        {isCurrent ? 'Ваш план' : planItem.name}
                      </span>
                      <div className={`text-[40px] font-bold leading-none mb-2 ${planItem.featured ? 'text-ivory' : 'text-slate'}`}>
                        {planItem.price} ₽ {planItem.period && <span className="text-base font-normal text-body-subtle">{planItem.period}</span>}
                      </div>
                      <ul className="my-6 flex-1">
                        {planItem.features.map((f) => (
                          <li key={f} className={`flex items-start gap-3 py-[6px] text-[15px] ${planItem.featured ? 'text-[#D1CFC5]' : 'text-body'}`}>
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="flex-shrink-0 mt-0.5">
                              <path d="M13.5 4.5L6 12L2.5 8.5" stroke="#788C5D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                            {f}
                          </li>
                        ))}
                      </ul>
                      {isCurrent ? (
                        <button disabled className={`w-full py-3 text-[15px] font-medium opacity-50 cursor-not-allowed ${planItem.featured ? 'bg-ivory text-slate border border-ivory' : 'bg-transparent text-body-muted border border-border-default'}`}>Текущий тариф</button>
                      ) : (
                        <button
                          onClick={() => handleSubscribe(planItem.plan)}
                          disabled={subscribe.isPending}
                          className={`w-full py-3 text-[15px] font-medium transition-colors disabled:opacity-60 ${planItem.featured ? 'bg-ivory text-slate border border-ivory hover:opacity-90' : 'bg-transparent text-slate border border-slate hover:bg-ivory-elevated'}`}
                        >
                          {isPending ? 'Оформляем…' : `Перейти на ${planItem.name}`}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              {subscription.data && (
                <div className="rounded-[24px] p-[31px] bg-ivory-warm mt-12">
                  <h4 className="text-xl font-semibold text-[#C6613F] mb-2">Отмена подписки</h4>
                  <p className="text-[15px] text-body-subtle">После отмены ваш тариф будет действовать до конца оплаченного периода.</p>
                  {cancel.isError && (
                    <p className="text-[14px] text-clay mt-2">Не удалось отменить подписку</p>
                  )}
                  <button onClick={handleCancel} disabled={cancel.isPending} className="btn-danger btn-sm mt-4 disabled:opacity-60">
                    {cancel.isPending ? 'Отменяем…' : 'Отменить подписку'}
                  </button>
                </div>
              )}

              <p className="text-center text-[14px] text-body-muted mt-8">
                Сравнение всех возможностей — на странице <Link href="/tariffs" className="text-slate font-medium no-underline hover:underline">тарифов</Link>.
              </p>
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}

export default function SubscriptionPage() {
  return (
    <>
      <Header />
      <RequireAuth>
        <SubscriptionContent />
      </RequireAuth>
    </>
  );
}
