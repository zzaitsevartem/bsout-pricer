'use client';

import React from 'react';
import { useAdminStats } from '@/models/admin';
import { apiErrorMessage, formatNumber } from '@/app/admin/_components/lib';

export function StatsCards() {
  const stats = useAdminStats();

  if (stats.isError) {
    return (
      <div className="p-5 border border-border-light rounded-[24px] bg-ivory-elevated mb-8">
        <div className="text-[15px] text-clay">
          {apiErrorMessage(stats.error, 'Не удалось загрузить статистику')}
        </div>
        <button
          type="button"
          onClick={() => stats.refetch()}
          className="btn-secondary btn-sm mt-3"
        >
          Повторить
        </button>
      </div>
    );
  }

  const cards: { label: string; value: number | undefined }[] = [
    { label: 'Пользователей', value: stats.data?.total_users },
    { label: 'Активных подписок', value: stats.data?.active_subscriptions },
    { label: 'Товаров в базе', value: stats.data?.total_products },
    { label: 'Магазинов', value: stats.data?.total_stores },
  ];

  return (
    <div className="grid grid-cols-4 gap-4 mb-8 max-lg:grid-cols-2 max-[480px]:grid-cols-1">
      {cards.map((card) => (
        <div key={card.label} className="p-5 border border-border-light rounded-[24px] bg-ivory-elevated">
          <div className="text-[32px] font-bold text-slate leading-none mb-1">
            {card.value === undefined ? '—' : formatNumber(card.value)}
          </div>
          <div className="text-[14px] text-body-subtle">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
