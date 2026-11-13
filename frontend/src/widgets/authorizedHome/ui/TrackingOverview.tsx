'use client';

import React from 'react';
import Link from 'next/link';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { isTrackingGateStatus, trackingGate, useTrackedProducts } from '@/models/tracking';
import { formatMoney, parseMoney } from '@/shared/lib/format';
import type { TrackedProductResponse } from '@/models/tracking';
import { cn } from '@/shared/lib/utils';
import { TrackingPreviewCard, TrackingPreviewRow } from './TrackingPreviewCard';

const PREVIEW_SIZE = 4;

function deltaClass(tracked: TrackedProductResponse): string {
  const delta = parseMoney(tracked.price_delta);
  if (delta === null || delta === 0) {
    return 'text-body-muted';
  }
  return delta < 0 ? 'text-olive font-bold' : 'text-clay';
}

function deltaLabel(tracked: TrackedProductResponse): string {
  const delta = parseMoney(tracked.price_delta);
  if (delta === null) {
    return parseMoney(tracked.current_price) === null ? 'нет данных' : 'нет данных для сравнения';
  }
  if (delta === 0) return 'без изменений';
  const sign = delta > 0 ? '+' : '';
  const pct =
    typeof tracked.price_delta_pct === 'number'
      ? ` (${tracked.price_delta_pct.toLocaleString('ru-RU')}%)`
      : '';
  return `${sign}${formatMoney(tracked.price_delta)}${pct}`;
}

function barColor(tracked: TrackedProductResponse): string {
  const delta = parseMoney(tracked.price_delta);
  if (delta === null) return 'bg-border-subtle';
  if (delta === 0) return 'bg-slate';
  return delta < 0 ? 'bg-olive' : 'bg-clay';
}

const EMPTY_STATE = (
  <div className="flex min-h-[340px] flex-col items-center justify-center gap-3 rounded-[24px] border border-border-light bg-ivory-warm p-6 text-center">
    <p className="text-[15px] font-semibold text-slate">Пока ничего не отслеживается</p>
    <p className="max-w-[34ch] text-[14px] leading-[1.4] text-body-subtle">
      Найдите запчасть и добавьте её в отслеживание — об изменении цены придёт уведомление.
    </p>
    <Link href="/search" className="btn-primary">
      Найти запчасть
    </Link>
  </div>
);

const LOADING_STATE = (
  <div className="flex min-h-[340px] items-center justify-center rounded-[24px] border border-border-light bg-ivory-warm p-6">
    <p className="text-[14px] text-body-muted">Загружаем данные…</p>
  </div>
);

function SubscriptionGateCard({ message }: { message: string }) {
  return (
    <div className="flex min-h-[340px] flex-col items-center justify-center gap-3 rounded-[24px] border border-border-light bg-ivory-warm p-6 text-center">
      <p className="text-[15px] font-semibold text-slate">
        Отслеживание доступно с активным тарифом
      </p>
      <p className="max-w-[40ch] text-[14px] leading-[1.4] text-body-subtle">{message}</p>
      <Link href="/tariffs" className="btn-primary">
        Выбрать тариф
      </Link>
    </div>
  );
}

function TrackedCard({ items }: { items: TrackedProductResponse[] }) {
  return (
    <TrackingPreviewCard
      header={
        <>
          <span className="flex-1 text-[13px] font-semibold">Товар</span>
          <span className="h-2 w-[60px] flex-none bg-slate" />
          <span className="w-20 text-right font-montserrat text-[13px]">Цена</span>
        </>
      }
    >
      {items.map((tracked) => (
        <TrackingPreviewRow key={tracked.id}>
          <Link
            href={`/product/${tracked.product_id}`}
            className="flex-1 truncate text-[14px] text-slate hover:underline"
            title={tracked.canonical_name}
          >
            {tracked.canonical_name}
          </Link>
          <div className="flex flex-1 gap-1" aria-hidden="true">
            {[0, 1, 2, 3].map((i) => (
              <span key={i} className={cn('h-2 flex-1', barColor(tracked))} />
            ))}
          </div>
          <span className="w-20 text-right font-montserrat text-[14px] leading-[1.3] text-slate">
            {formatMoney(tracked.current_price)}
            <small className={cn('block font-sans text-[12px]', deltaClass(tracked))}>
              {deltaLabel(tracked)}
            </small>
          </span>
        </TrackingPreviewRow>
      ))}
    </TrackingPreviewCard>
  );
}

const TrackingOverview: React.FC = () => {
  const isAuth = useUnit($isAuth);
  const {
    data: tracked,
    isPending,
    error,
  } = useTrackedProducts({ is_active: true, page: 1, per_page: PREVIEW_SIZE }, { enabled: isAuth });

  const isGate = isTrackingGateStatus(error);
  const total = tracked?.total ?? 0;

  return (
    <section className="py-[84px] max-md:py-[61px] max-[480px]:py-[48px]">
      <div className="mx-auto grid max-w-[1200px] grid-cols-[minmax(0,55fr)_minmax(0,45fr)] items-center gap-12 px-6 max-md:grid-cols-1 max-md:gap-8">
        <div>
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Отслеживание цен
          </p>
          <h2 className="mb-6 text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] text-slate max-md:text-[32px] max-[480px]:text-[28px]">
            Всё под контролем
          </h2>
          <p className="mb-4 max-w-[64ch] text-lg leading-[1.4] text-body">
            Здесь показаны последние доступные цены и их изменение с момента добавления. Уведомления
            о снижении цены доступны на тарифе «Продвинутый».
          </p>
          <p className="mb-4 text-sm text-body-muted">
            Зелёный — цена снизилась, красный — выросла, тёмный — без изменений.
          </p>
          <Link href="/account/tracking" className="btn-arrow">
            Управлять отслеживанием
          </Link>
        </div>

        {isPending && !tracked ? (
          LOADING_STATE
        ) : isGate ? (
          <SubscriptionGateCard message={trackingGate(error)?.message ?? ''} />
        ) : error ? (
          <p role="alert" className="text-body-muted">
            Не удалось загрузить отслеживание. Попробуйте обновить страницу.
          </p>
        ) : total === 0 ? (
          EMPTY_STATE
        ) : (
          <TrackedCard items={tracked?.results.slice(0, PREVIEW_SIZE) ?? []} />
        )}
      </div>
    </section>
  );
};

export { TrackingOverview };
