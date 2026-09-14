'use client';

import React from 'react';
import axios from 'axios';
import Link from 'next/link';
import { useSubscription } from '@/models/user';
import { useTrackingUsage } from '@/models/tracking';
import { formatDate, planLabel, plural } from '@/shared/lib/format';

const DAY_MS = 86_400_000;

function daysUntil(iso: string): number {
  const end = new Date(iso).getTime();
  if (Number.isNaN(end)) {
    return 0;
  }
  return Math.max(0, Math.ceil((end - Date.now()) / DAY_MS));
}

const TariffStrip: React.FC = () => {
  const { data: subscription, isPending, error } = useSubscription();
  const { data: usage } = useTrackingUsage();

  if (isPending) {
    return null;
  }

  const subscriptionMissing = axios.isAxiosError(error) && error.response?.status === 404;
  if (subscriptionMissing) {
    return (
      <div className="mx-auto mt-10 w-full max-w-[1200px] px-6">
        <div className="flex flex-wrap items-center gap-4 rounded-full bg-ivory-elevated px-7 py-3 max-sm:rounded-3xl">
          <span className="inline-flex items-center gap-2 rounded-full bg-ivory-warm px-[14px] py-1.5 text-[14px] font-semibold text-slate">
            <span className="h-2 w-2 rounded-full bg-border-subtle" />
            Без тарифа
          </span>
          <span className="min-w-[200px] flex-1 text-[15px] text-body-subtle">
            Доступ к отслеживанию ограничен. Подключите тариф, чтобы пользоваться сервисом.
          </span>
          <Link href="/tariffs" className="btn-secondary btn-sm">
            Выбрать тариф
          </Link>
        </div>
      </div>
    );
  }

  if (!subscription) {
    return null;
  }

  const isTrial = subscription.plan === 'trial';
  const daysLeft = daysUntil(subscription.end_date);

  const description = isTrial
    ? [
        `Пробный период до ${formatDate(subscription.end_date)}.`,
        daysLeft > 0 ? `Осталось ${daysLeft} ${plural(daysLeft, 'день', 'дня', 'дней')}.` : null,
        `Отслеживание до ${usage?.limit ?? '—'} позиций.`,
      ]
        .filter(Boolean)
        .join(' ')
    : `Активен до ${formatDate(subscription.end_date)} · обновление цен раз в сутки · безлимитный поиск`;

  return (
    <div className="mx-auto mt-10 w-full max-w-[1200px] px-6">
      <div className="flex flex-wrap items-center gap-4 rounded-full bg-ivory-elevated px-7 py-3 max-sm:rounded-3xl">
        <span className="inline-flex items-center gap-2 rounded-full bg-ivory-warm px-[14px] py-1.5 text-[14px] font-semibold text-slate">
          <span className="h-2 w-2 rounded-full bg-green-discount" />
          {planLabel(subscription.plan)}
        </span>
        <span className="min-w-[200px] flex-1 text-[15px] text-body-subtle">{description}</span>
        <Link href="/tariffs" className="btn-arrow">
          Управление тарифом →
        </Link>
      </div>
    </div>
  );
};

export { TariffStrip };
