'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { TariffPlans } from '@/widgets/TariffPlans';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useSubscription } from '@/models/user';
import { usePaymentHistory, usePlans, useSubscribe, useCancelSubscription } from '@/models/payment';
import type { PaymentResponse } from '@/models/payment';
import type { Plan } from '@/models/user';
import { formatDate, planLabel } from '@/shared/lib/format';

const STATUS_LABELS: Record<string, string> = {
  pending: 'Ожидает подтверждения',
  succeeded: 'Оплачен',
  canceled: 'Отменён',
  failed: 'Ошибка оплаты',
};

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

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

function PendingPaymentNotice({ payment }: { payment: PaymentResponse }) {
  return (
    <div className="rounded-[24px] p-[31px] bg-ivory-warm mb-8">
      <h4 className="text-xl font-semibold text-[#C6613F] mb-2">Платёж ожидает подтверждения</h4>
      <p className="text-[15px] text-body mb-2">
        Счёт №{payment.id} на {formatAmount(payment.amount)} ₽ создан. Подписка станет активной только
        после подтверждения оплаты — прямо сейчас тариф ещё не подключён.
      </p>
      {payment.confirmationUrl ? (
        <a
          href={payment.confirmationUrl}
          target="_blank"
          rel="noreferrer"
          className="btn btn-primary btn-sm no-underline mt-2"
        >
          Перейти к оплате
        </a>
      ) : (
        <p className="text-[14px] text-body-subtle mb-0">
          Ссылка на оплату пока не выдана платёжным провайдером. Мы подтвердим платёж и активируем
          тариф вручную.
        </p>
      )}
    </div>
  );
}

function SubscriptionContent() {
  const subscription = useSubscription();
  const plans = usePlans();
  const history = usePaymentHistory();
  const subscribe = useSubscribe();
  const cancel = useCancelSubscription();

  const currentPlan = subscription.data?.plan;
  const currentPlanDefinition = plans.data?.find((item) => item.plan === currentPlan);
  const pendingPayment =
    subscribe.data?.status === 'pending'
      ? subscribe.data
      : history.data?.find((payment) => payment.status === 'pending');

  const handleSubscribe = (plan: Plan) => {
    subscribe.mutate({ plan, payment_method: 'card' });
  };

  const handleCancel = () => {
    if (
      window.confirm(
        'Отключить автопродление? Доступ сохранится до конца уже оплаченного периода.',
      )
    ) {
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

              <div className="rounded-[24px] pt-[20px] px-[31px] pb-[31px] bg-ivory-elevated mb-8">
                {subscription.isLoading ? (
                  <p className="text-body-subtle mb-0">Загрузка…</p>
                ) : subscription.data ? (
                  <div className="flex justify-between items-start flex-wrap gap-4">
                    <div>
                      <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Текущий тариф</p>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="inline-flex items-center rounded-full px-4 py-[6px] text-[14px] font-semibold bg-green-discount text-white border border-transparent">
                          {currentPlanDefinition?.nameRu ?? planLabel(subscription.data.plan)}
                        </span>
                        {currentPlanDefinition && (
                          <span className="text-[14px] text-body-subtle">
                            {currentPlanDefinition.price === 0
                              ? 'Бесплатно'
                              : `${formatAmount(currentPlanDefinition.price)} ₽ / ${formatDays(currentPlanDefinition.durationDays)}`}
                          </span>
                        )}
                      </div>
                      <p className="text-[15px] text-body-subtle mt-2 mb-0">
                        Действует до {formatDate(subscription.data.end_date)} · {subscription.data.auto_renew ? 'Автопродление включено' : 'Автопродление выключено'}
                      </p>
                      {currentPlanDefinition && (
                        <p className="text-[14px] text-body-subtle mt-2 mb-0">
                          Лимит отслеживаемых товаров: {currentPlanDefinition.trackedProducts}. Счётчик
                          фактического использования появится позже.
                        </p>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-center flex-wrap gap-4">
                    <p className="text-[15px] text-body-subtle mb-0">У вас нет активной подписки. Выберите тариф ниже — доступ откроется после подтверждения оплаты.</p>
                  </div>
                )}
              </div>

              {pendingPayment && <PendingPaymentNotice payment={pendingPayment} />}

              {cancel.isSuccess && cancel.data && (
                <div className="rounded-[24px] p-[31px] bg-ivory-elevated mb-8">
                  <p className="text-[15px] text-body mb-0">
                    {cancel.data.detail} Доступ сохраняется до {formatDate(cancel.data.accessUntil)}.
                  </p>
                </div>
              )}

              <h3 className="text-2xl font-semibold text-slate mb-4">{currentPlan ? 'Сменить тариф' : 'Выбрать тариф'}</h3>

              {plans.isLoading && <p className="text-[15px] text-body-subtle mb-4">Загружаем тарифы…</p>}

              {plans.isError && (
                <div className="mb-4">
                  <p className="text-[14px] text-clay mb-2">Не удалось загрузить тарифы.</p>
                  <button onClick={() => plans.refetch()} className="btn btn-secondary btn-sm">
                    Повторить
                  </button>
                </div>
              )}

              {subscribe.isError && (
                <p className="text-[14px] text-clay mb-4">Не удалось создать платёж. Попробуйте позже.</p>
              )}

              {plans.data && (
                <div className="mb-8">
                  <TariffPlans
                    onSelect={handleSubscribe}
                    selectedPlan={subscribe.isPending ? subscribe.variables?.plan : undefined}
                    subscribing={subscribe.isPending}
                  />
                </div>
              )}

              <h3 className="text-2xl font-semibold text-slate mb-4">История платежей</h3>

              <div className="rounded-[24px] p-[31px] bg-ivory-elevated mb-8">
                {history.isLoading ? (
                  <p className="text-[15px] text-body-subtle mb-0">Загрузка…</p>
                ) : history.isError ? (
                  <p className="text-[15px] text-body-subtle mb-0">Не удалось загрузить историю платежей.</p>
                ) : history.data && history.data.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-[15px]">
                      <thead>
                        <tr>
                          <th className="font-montserrat text-[13px] font-medium uppercase tracking-[0.04em] text-body-muted text-left py-2">Дата</th>
                          <th className="font-montserrat text-[13px] font-medium uppercase tracking-[0.04em] text-body-muted text-left py-2">Тариф</th>
                          <th className="font-montserrat text-[13px] font-medium uppercase tracking-[0.04em] text-body-muted text-left py-2">Сумма</th>
                          <th className="font-montserrat text-[13px] font-medium uppercase tracking-[0.04em] text-body-muted text-left py-2">Статус</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.data.map((payment) => (
                          <tr key={payment.id}>
                            <td className="py-2 border-t border-border-light-subtle text-body">{formatDate(payment.createdAt)}</td>
                            <td className="py-2 border-t border-border-light-subtle text-body">{planLabel(payment.plan)}</td>
                            <td className="py-2 border-t border-border-light-subtle text-body">{formatAmount(payment.amount)} ₽</td>
                            <td className="py-2 border-t border-border-light-subtle text-body">{statusLabel(payment.status)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-[15px] text-body-subtle mb-0">Платежей пока не было.</p>
                )}
              </div>

              {subscription.data && (
                <div className="rounded-[24px] p-[31px] bg-ivory-warm mt-12">
                  <h4 className="text-xl font-semibold text-[#C6613F] mb-2">Отмена подписки</h4>
                  <p className="text-[15px] text-body-subtle">
                    Отмена отключает автопродление. Доступ к тарифу сохраняется до конца уже оплаченного
                    периода — до {formatDate(subscription.data.end_date)}.
                  </p>
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
