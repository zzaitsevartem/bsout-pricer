'use client';

import React from 'react';
import { cn } from '@/shared/lib/utils';
import type { ComparisonOfferResponse } from '@/models/catalog';
import {
  BADGE_BASE,
  BADGE_SUCCESS,
  DASH,
  TABLE,
  TABLE_HEAD_ROW,
  TABLE_TD,
  TABLE_TH,
  TABLE_WRAPPER,
  formatDateTime,
  formatMoney,
  formatNumber,
  parseMoney,
  stockBadgeClass,
  stockLabel,
} from '@/app/product/[id]/_components/lib';

type OffersTableProps = {
  offers: ComparisonOfferResponse[];
};

export function OffersTable({ offers }: OffersTableProps) {
  const sorted = React.useMemo(() => {
    return [...offers].sort((a, b) => {
      const left = parseMoney(a.price_retail);
      const right = parseMoney(b.price_retail);
      return (left ?? Number.POSITIVE_INFINITY) - (right ?? Number.POSITIVE_INFINITY);
    });
  }, [offers]);

  const cheapest = React.useMemo(() => {
    const values = sorted
      .map((offer) => parseMoney(offer.price_retail))
      .filter((value): value is number => value !== null);
    return values.length > 0 ? Math.min(...values) : null;
  }, [sorted]);

  if (sorted.length === 0) {
    return (
      <div className="border border-border-light rounded-[24px] bg-ivory-elevated p-6 text-[15px] text-body-subtle">
        Активных предложений по этому товару сейчас нет. Загляните позже — цены обновляются
        автоматически.
      </div>
    );
  }

  return (
    <div className={TABLE_WRAPPER}>
      <table className={TABLE}>
        <thead>
          <tr className={TABLE_HEAD_ROW}>
            <th className={TABLE_TH}>Магазин</th>
            <th className={TABLE_TH}>Розница</th>
            <th className={TABLE_TH}>Опт</th>
            <th className={TABLE_TH}>Наличие</th>
            <th className={TABLE_TH}>Обновлено</th>
            <th className={cn(TABLE_TH, 'text-right')}>
              <span className="sr-only">Ссылка на магазин</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((offer) => {
            const retail = parseMoney(offer.price_retail);
            const isCheapest = cheapest !== null && retail !== null && retail === cheapest;

            return (
              <tr key={offer.id} className={cn(isCheapest && 'bg-[#EDF1E5]')}>
                <td className={TABLE_TD}>
                  <div className="font-semibold text-slate">{offer.store?.name ?? DASH}</div>
                  {isCheapest && (
                    <span className={cn(BADGE_BASE, BADGE_SUCCESS, 'mt-1')}>Самый дешёвый</span>
                  )}
                </td>

                <td className={TABLE_TD}>
                  <div className="text-[17px] font-bold text-slate whitespace-nowrap">
                    {formatMoney(offer.price_retail)}
                  </div>
                  {parseMoney(offer.price_old) !== null && (
                    <div className="text-[13px] text-body-muted line-through whitespace-nowrap">
                      {formatMoney(offer.price_old)}
                    </div>
                  )}
                </td>

                <td className={cn(TABLE_TD, 'whitespace-nowrap text-body-subtle')}>
                  {formatMoney(offer.price_opt)}
                </td>

                <td className={TABLE_TD}>
                  <span className={cn(BADGE_BASE, stockBadgeClass(offer.stock_status))}>
                    {stockLabel(offer.stock_status)}
                  </span>
                  {offer.stock_qty !== null && (
                    <div className="text-[13px] text-body-muted mt-1">
                      {formatNumber(offer.stock_qty)} шт.
                    </div>
                  )}
                </td>

                <td className={cn(TABLE_TD, 'whitespace-nowrap text-[14px] text-body-subtle')}>
                  {formatDateTime(offer.last_seen_at)}
                </td>

                <td className={cn(TABLE_TD, 'text-right')}>
                  {offer.url ? (
                    <a
                      href={offer.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(
                        'btn-sm whitespace-nowrap',
                        isCheapest ? 'btn-primary' : 'btn-secondary',
                      )}
                    >
                      В магазин
                    </a>
                  ) : (
                    <span className="text-[14px] text-body-muted">{DASH}</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
