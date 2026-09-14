import React from 'react';
import type { ComparisonStatsResponse } from '@/models/catalog';
import {
  DASH,
  formatMoney,
  formatNumber,
  formatPercent,
  plural,
} from '@/app/product/[id]/_components/lib';

type PriceStatsProps = {
  stats: ComparisonStatsResponse;
};

export function PriceStats({ stats }: PriceStatsProps) {
  const hasRange = stats.min_price_retail !== null && stats.max_price_retail !== null;

  const cards: { label: string; value: string; hint?: string }[] = [
    {
      label: 'Разброс цен',
      value:
        stats.spread_abs === null
          ? DASH
          : `${formatMoney(stats.spread_abs)} (${formatPercent(stats.spread_pct)})`,
      hint: 'разница между самым дешёвым и самым дорогим',
    },
    {
      label: 'Средняя цена',
      value: formatMoney(stats.avg_price_retail),
      hint: 'по всем активным предложениям',
    },
    {
      label: 'Магазинов',
      value: `${formatNumber(stats.stores_count)} ${plural(
        stats.stores_count,
        'магазин',
        'магазина',
        'магазинов',
      )}`,
      hint: `${formatNumber(stats.offers_count)} ${plural(
        stats.offers_count,
        'предложение',
        'предложения',
        'предложений',
      )}`,
    },
    {
      label: 'Опт от',
      value: formatMoney(stats.min_price_opt),
      hint: 'минимальная оптовая цена',
    },
  ];

  return (
    <div className="mb-10">
      <div className="rounded-[24px] border border-border-light bg-ivory-elevated p-6 mb-4">
        <div className="text-[14px] text-body-subtle mb-1">Цена по городу</div>
        {hasRange ? (
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="text-[15px] text-body-subtle">от</span>
            <span className="text-[40px] leading-none font-bold text-slate">
              {formatMoney(stats.min_price_retail)}
            </span>
            <span className="text-[15px] text-body-subtle">до</span>
            <span className="text-[24px] leading-none font-semibold text-body">
              {formatMoney(stats.max_price_retail)}
            </span>
          </div>
        ) : (
          <div className="text-[19px] font-semibold text-body-subtle">
            Нет активных предложений
          </div>
        )}
      </div>

      <div className="grid grid-cols-4 gap-4 max-lg:grid-cols-2 max-[480px]:grid-cols-1">
        {cards.map((card) => (
          <div
            key={card.label}
            className="p-5 border border-border-light rounded-[24px] bg-ivory-elevated"
          >
            <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted mb-2">
              {card.label}
            </div>
            <div className="text-[19px] font-bold text-slate leading-tight mb-1">{card.value}</div>
            {card.hint && <div className="text-[13px] text-body-subtle">{card.hint}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
