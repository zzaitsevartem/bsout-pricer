'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import {
  trackingGate,
  useTrackedProducts,
  useTrackingUsage,
  useUntrackProduct,
  useUpdateTrackedProduct,
} from '@/models/tracking';
import type { TrackedProductResponse, TrackingGate } from '@/models/tracking';
import { useExportTracking } from '@/models/export';
import { ExportNotice } from '@/widgets/CatalogExport/ui/CatalogExport';
import { formatMoney, formatPercent, plural } from '@/shared/lib/format';

const PER_PAGE = 20;

function UsageBar() {
  const usage = useTrackingUsage();

  if (usage.isLoading || !usage.data) {
    return <div className="h-[76px] bg-ivory-elevated animate-pulse rounded-[24px] mb-6" />;
  }

  const { used, limit } = usage.data;
  const share = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const full = limit > 0 && used >= limit;

  return (
    <div className="rounded-[24px] bg-ivory-elevated p-6 mb-6">
      <div className="flex items-baseline justify-between gap-4 mb-3 flex-wrap">
        <div className="text-[15px] text-body">
          Отслеживается <span className="font-semibold text-slate">{used}</span> из{' '}
          <span className="font-semibold text-slate">{limit}</span>{' '}
          {plural(limit, 'товара', 'товаров', 'товаров')}
        </div>
        {full && (
          <Link href="/tariffs" className="btn-secondary btn-sm">
            Повысить тариф
          </Link>
        )}
      </div>
      <div className="h-2 w-full bg-ivory border border-border-light-subtle">
        <div className="h-full bg-slate" style={{ width: `${share}%` }} />
      </div>
    </div>
  );
}

function DeltaCell({ item }: { item: TrackedProductResponse }) {
  if (item.price_delta === null || item.price_delta_pct === null) {
    return <span className="text-body-muted">—</span>;
  }

  const delta = Number(item.price_delta);
  if (!Number.isFinite(delta) || delta === 0) {
    return <span className="text-body-subtle">без изменений</span>;
  }

  const dropped = delta < 0;
  return (
    <span className={dropped ? 'text-[#4F5C36] font-medium' : 'text-clay'}>
      {dropped ? '↓' : '↑'} {formatMoney(String(Math.abs(delta)))} (
      {formatPercent(Math.abs(item.price_delta_pct))})
    </span>
  );
}

function TargetPriceEditor({ item }: { item: TrackedProductResponse }) {
  const update = useUpdateTrackedProduct();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(item.target_price ?? '');

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => {
          setValue(item.target_price ?? '');
          setEditing(true);
        }}
        className="btn-arrow"
      >
        {item.target_price ? formatMoney(item.target_price) : 'Задать цель'}
      </button>
    );
  }

  const submit = () => {
    const trimmed = value.trim();
    const parsed = trimmed === '' ? null : Number(trimmed.replace(',', '.'));
    if (parsed !== null && (!Number.isFinite(parsed) || parsed <= 0)) {
      return;
    }
    update.mutate(
      { trackedId: item.id, target_price: parsed },
      { onSettled: () => setEditing(false) },
    );
  };

  return (
    <div className="flex items-center gap-2">
      <input
        type="text"
        inputMode="decimal"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="цена, ₽"
        className="w-[110px] rounded-full px-2 py-1 text-[14px] bg-ivory border border-border-default text-slate"
      />
      <button
        type="button"
        onClick={submit}
        disabled={update.isPending}
        className="btn-primary btn-sm disabled:opacity-60"
      >
        ОК
      </button>
      <button type="button" onClick={() => setEditing(false)} className="btn-ghost btn-sm">
        Отмена
      </button>
    </div>
  );
}

function TrackedRow({ item }: { item: TrackedProductResponse }) {
  const untrack = useUntrackProduct();

  return (
    <div className="px-6 py-4 border-b border-border-light-subtle last:border-b-0">
      <div className="grid grid-cols-[minmax(0,1fr)_130px_170px_190px_auto] gap-4 items-start max-lg:grid-cols-[minmax(0,1fr)_auto] max-sm:grid-cols-1">
        <div className="min-w-0 max-lg:col-span-2 max-sm:col-span-1">
          <Link
            href={`/product/${item.product_id}`}
            className="text-[15px] font-medium text-slate no-underline hover:underline"
          >
            {item.canonical_name}
          </Link>
          <div className="text-[14px] text-body-subtle mt-1 flex gap-3 flex-wrap items-center">
            <span>
              {item.stores_count} {plural(item.stores_count, 'магазин', 'магазина', 'магазинов')}
            </span>
            {item.target_reached && (
              <span className="inline-flex items-center rounded-full text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-[#EDF1E5] border border-[#C7D2B0] text-[#4F5C36]">
                Цель достигнута
              </span>
            )}
          </div>
        </div>

        <div className="min-w-0">
          <div className="text-[13px] text-body-muted">Сейчас</div>
          <div className="text-[15px] font-semibold text-slate">
            {formatMoney(item.current_price)}
          </div>
        </div>

        <div className="min-w-0">
          <div className="text-[13px] text-body-muted">С момента добавления</div>
          <div className="text-[15px]">
            <DeltaCell item={item} />
          </div>
        </div>

        <div className="min-w-0">
          <div className="text-[13px] text-body-muted">Целевая цена</div>
          <TargetPriceEditor item={item} />
        </div>

        <button
          type="button"
          onClick={() => untrack.mutate(item.id)}
          disabled={untrack.isPending}
          className="btn-ghost btn-sm justify-self-end disabled:opacity-60"
        >
          Убрать
        </button>
      </div>
    </div>
  );
}

function GateState({ gate }: { gate: TrackingGate }) {
  return (
    <div className="rounded-[24px] bg-ivory-elevated p-10 text-center">
      <h3 className="text-[20px] font-semibold text-slate mb-3">Мониторинг недоступен</h3>
      <p className="text-[15px] text-body-subtle mb-6 max-w-[520px] mx-auto">{gate.message}</p>
      <Link href="/tariffs" className="btn-primary">
        Выбрать тариф
      </Link>
    </div>
  );
}

function TrackingContent() {
  const [page, setPage] = useState(1);
  const tracked = useTrackedProducts({ page, per_page: PER_PAGE });
  const exportTracking = useExportTracking();
  const gate = tracked.isError ? trackingGate(tracked.error) : null;
  const totalPages = tracked.data ? Math.max(1, Math.ceil(tracked.data.total / PER_PAGE)) : 1;
  const hasRows = Boolean(tracked.data && tracked.data.results.length > 0);

  return (
    <>
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main>
            <div className="mb-12">
              <div className="flex items-start justify-between gap-4 mb-2 flex-wrap">
                <h2 className="text-[40px] font-semibold text-slate">Мониторинг товаров</h2>
                <button
                  type="button"
                  onClick={() => exportTracking.mutate()}
                  disabled={!hasRows || exportTracking.isPending}
                  aria-busy={exportTracking.isPending}
                  className="btn-secondary btn-sm mt-3 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {exportTracking.isPending ? 'Готовим файл…' : 'Выгрузить CSV'}
                </button>
              </div>
              <p className="text-[15px] text-body-subtle mb-6 max-w-[640px]">
                Мы следим за ценой в пяти магазинах и присылаем уведомление, когда она падает или
                опускается до вашей цели.
              </p>

              {exportTracking.error && <ExportNotice error={exportTracking.error} />}

              <UsageBar />

              {gate ? (
                <GateState gate={gate} />
              ) : (
                <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                  {tracked.isLoading ? (
                    <div className="px-6 py-4 text-body-subtle">Загрузка…</div>
                  ) : tracked.isError ? (
                    <div className="px-6 py-4 text-body-subtle">
                      Не удалось загрузить список отслеживаемых товаров
                    </div>
                  ) : tracked.data && tracked.data.results.length > 0 ? (
                    tracked.data.results.map((item) => <TrackedRow key={item.id} item={item} />)
                  ) : (
                    <div className="px-6 py-10 text-center">
                      <p className="text-[15px] text-body-subtle mb-4">
                        Вы пока ничего не отслеживаете.
                      </p>
                      <Link href="/search" className="btn-primary">
                        Найти товар
                      </Link>
                    </div>
                  )}
                </div>
              )}

              {!gate && totalPages > 1 && (
                <div className="flex items-center justify-center gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                    disabled={page <= 1}
                    className="btn-secondary btn-sm disabled:opacity-40"
                  >
                    Назад
                  </button>
                  <span className="text-[14px] text-body-subtle">
                    {page} из {totalPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                    disabled={page >= totalPages}
                    className="btn-secondary btn-sm disabled:opacity-40"
                  >
                    Вперёд
                  </button>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}

export default function AccountTrackingPage() {
  return (
    <>
      <Header />
      <RequireAuth>
        <TrackingContent />
      </RequireAuth>
    </>
  );
}
