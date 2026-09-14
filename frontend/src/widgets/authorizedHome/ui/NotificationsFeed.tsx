'use client';

import React from 'react';
import Link from 'next/link';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { useNotifications } from '@/models/notification';
import { formatDateTime } from '@/shared/lib/format';
import type { NotificationResponse } from '@/models/notification';
import { cn } from '@/shared/lib/utils';

const FEED_SIZE = 3;

function NotificationItem({ notification }: { notification: NotificationResponse }) {
  return (
    <article className="flex items-start gap-4 border-b border-border-light-subtle py-[22px] last:border-none">
      <span
        className={cn(
          'mt-2 h-[10px] w-[10px] flex-none rounded-full',
          notification.is_read ? 'bg-border-subtle' : 'bg-clay',
        )}
        aria-hidden="true"
      />
      <div className="min-w-0">
        <h4 className="mb-1 text-[15.5px] font-semibold text-slate">{notification.title}</h4>
        <p className="line-clamp-2 text-[14.5px] leading-[1.4] text-body-subtle">
          {notification.body}
        </p>
        <p className="mt-1.5 text-[12.5px] text-body-muted">
          {formatDateTime(notification.created_at)}
        </p>
      </div>
    </article>
  );
}

const NotificationsFeed: React.FC = () => {
  const isAuth = useUnit($isAuth);
  const { data: feed, isPending } = useNotifications(
    { page: 1, per_page: FEED_SIZE },
    { enabled: isAuth },
  );

  if (isPending || !feed || feed.total === 0) {
    return null;
  }

  return (
    <section aria-label="Уведомления" className="pb-[84px] max-md:pb-[61px]">
      <div className="mx-auto max-w-[1200px] px-6">
        <div className="mb-6 flex flex-wrap items-baseline justify-between gap-4">
          <div>
            <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
              Уведомления
            </p>
            <h2 className="mb-0 text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] text-slate max-md:text-[32px] max-[480px]:text-[28px]">
              Новое для вас
            </h2>
          </div>
          <Link href="/account/notifications" className="btn-arrow">
            Все уведомления ({feed.total}) →
          </Link>
        </div>
        <div className="rounded-[24px] bg-ivory-elevated px-[31px] py-2 max-sm:px-6">
          {feed.results.slice(0, FEED_SIZE).map((notification) => (
            <NotificationItem key={notification.id} notification={notification} />
          ))}
        </div>
      </div>
    </section>
  );
};

export { NotificationsFeed };
