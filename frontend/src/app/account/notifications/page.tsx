'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useMarkNotificationRead, useNotifications } from '@/models/notification';
import type { NotificationResponse } from '@/models/notification';
import { cn } from '@/shared/lib/utils';
import { formatDateTime, formatMoney } from '@/shared/lib/format';

const PER_PAGE = 20;

const TYPE_LABELS: Record<string, string> = {
  price_drop: 'Цена снизилась',
  target_reached: 'Достигнута целевая цена',
};

function NotificationRow({ item }: { item: NotificationResponse }) {
  const markRead = useMarkNotificationRead();

  return (
    <div
      className={cn(
        'px-6 py-4 border-b border-border-light-subtle last:border-b-0 flex items-start gap-4 flex-wrap',
        item.is_read ? 'bg-transparent' : 'bg-ivory',
      )}
    >
      <div className="flex-1 min-w-[240px]">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          {!item.is_read && <span className="w-2 h-2 bg-slate flex-shrink-0" aria-hidden="true" />}
          <span className="text-[15px] font-medium text-slate">{item.title}</span>
          <span className="inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-ivory-elevated border border-border-default text-body-subtle">
            {TYPE_LABELS[item.type] ?? item.type}
          </span>
        </div>
        <p className="text-[14px] text-body-subtle mb-1">{item.body}</p>
        <div className="text-[13px] text-body-muted flex gap-3 flex-wrap">
          <span>{formatDateTime(item.created_at)}</span>
          {item.old_price && item.new_price && (
            <span>
              {formatMoney(item.old_price)} → {formatMoney(item.new_price)}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {item.product_id !== null && (
          <Link href={`/product/${item.product_id}`} className="btn-secondary btn-sm">
            К товару
          </Link>
        )}
        {!item.is_read && (
          <button
            type="button"
            onClick={() => markRead.mutate(item.id)}
            disabled={markRead.isPending}
            className="btn-ghost btn-sm disabled:opacity-60"
          >
            Прочитано
          </button>
        )}
      </div>
    </div>
  );
}

function NotificationsContent() {
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const notifications = useNotifications({
    page,
    per_page: PER_PAGE,
    ...(unreadOnly ? { unread: true } : {}),
  });
  const totalPages = notifications.data
    ? Math.max(1, Math.ceil(notifications.data.total / PER_PAGE))
    : 1;

  return (
    <>
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main>
            <div className="mb-12">
              <div className="flex items-baseline justify-between gap-4 mb-6 flex-wrap">
                <h2 className="text-[40px] font-semibold text-slate">Уведомления</h2>
                <button
                  type="button"
                  onClick={() => {
                    setUnreadOnly((current) => !current);
                    setPage(1);
                  }}
                  className={unreadOnly ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'}
                >
                  {unreadOnly ? 'Показать все' : 'Только непрочитанные'}
                </button>
              </div>

              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {notifications.isLoading ? (
                  <div className="px-6 py-4 text-body-subtle">Загрузка…</div>
                ) : notifications.isError ? (
                  <div className="px-6 py-4 text-body-subtle">
                    Не удалось загрузить уведомления
                  </div>
                ) : notifications.data && notifications.data.results.length > 0 ? (
                  notifications.data.results.map((item) => (
                    <NotificationRow key={item.id} item={item} />
                  ))
                ) : (
                  <div className="px-6 py-10 text-center">
                    <p className="text-[15px] text-body-subtle mb-2">
                      {unreadOnly ? 'Непрочитанных уведомлений нет.' : 'Уведомлений пока нет.'}
                    </p>
                    <p className="text-[14px] text-body-muted mb-4">
                      Уведомления приходят на тарифе «Продвинутый», когда цена отслеживаемого товара
                      снижается.
                    </p>
                    <Link href="/account/tracking" className="btn-secondary">
                      К мониторингу
                    </Link>
                  </div>
                )}
              </div>

              {totalPages > 1 && (
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

export default function AccountNotificationsPage() {
  return (
    <>
      <Header />
      <RequireAuth>
        <NotificationsContent />
      </RequireAuth>
    </>
  );
}
