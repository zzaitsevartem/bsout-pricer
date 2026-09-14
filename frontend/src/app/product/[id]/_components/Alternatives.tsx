import React from 'react';
import Link from 'next/link';
import type { AlternativeTierResponse } from '@/models/catalog';
import {
  BADGE_BASE,
  BADGE_DEFAULT,
  formatMoney,
  formatNumber,
  parseMoney,
  plural,
} from '@/app/product/[id]/_components/lib';

type AlternativesProps = {
  alternatives: AlternativeTierResponse[];
  currentMinPrice: string | null;
};

function savingsLabel(currentMin: number | null, altMin: number | null): string | null {
  if (currentMin === null || altMin === null || altMin <= 0 || currentMin <= 0) {
    return null;
  }
  if (altMin >= currentMin) {
    return null;
  }
  const times = Math.round((currentMin / altMin) * 10) / 10;
  if (times >= 2) {
    const word = plural(Math.floor(times), 'раз', 'раза', 'раз');
    return `дешевле в ${times.toLocaleString('ru-RU', { maximumFractionDigits: 1 })} ${word}`;
  }
  const percent = Math.round((1 - altMin / currentMin) * 100);
  return percent >= 5 ? `дешевле на ${percent}%` : null;
}

export function Alternatives({ alternatives, currentMinPrice }: AlternativesProps) {
  if (alternatives.length === 0) {
    return null;
  }

  const currentMin = parseMoney(currentMinPrice);

  const sorted = [...alternatives].sort((a, b) => {
    const left = parseMoney(a.min_price_retail);
    const right = parseMoney(b.min_price_retail);
    return (left ?? Number.POSITIVE_INFINITY) - (right ?? Number.POSITIVE_INFINITY);
  });

  return (
    <section className="mb-10">
      <h2 className="text-[24px] font-semibold text-slate mb-1">Другие классы качества</h2>
      <p className="text-[15px] text-body-subtle mb-4">
        Та же деталь для того же устройства, но другого класса — цена может отличаться в разы.
      </p>

      <div className="grid grid-cols-3 gap-4 max-lg:grid-cols-2 max-[480px]:grid-cols-1">
        {sorted.map((alternative) => {
          const altMin = parseMoney(alternative.min_price_retail);
          const savings = savingsLabel(currentMin, altMin);

          return (
            <Link
              key={alternative.product_id}
              href={`/product/${alternative.product_id}`}
              className="block p-5 border border-border-light rounded-[24px] bg-ivory-elevated no-underline transition-colors hover:border-slate"
            >
              <span className={`${BADGE_BASE} ${BADGE_DEFAULT} mb-3`}>
                {alternative.quality_tier?.name_ru ?? 'Класс не указан'}
              </span>

              <div className="text-[15px] font-semibold text-slate mb-3 leading-snug">
                {alternative.canonical_name}
              </div>

              <div className="text-[13px] text-body-subtle mb-1">от</div>
              <div className="text-[24px] font-bold text-slate leading-none mb-2">
                {formatMoney(alternative.min_price_retail)}
              </div>

              {savings && <div className="text-[13px] font-semibold text-olive mb-2">{savings}</div>}

              <div className="text-[13px] text-body-muted">
                {formatNumber(alternative.stores_count)}{' '}
                {plural(alternative.stores_count, 'магазин', 'магазина', 'магазинов')} ·{' '}
                {formatNumber(alternative.offers_count)}{' '}
                {plural(
                  alternative.offers_count,
                  'предложение',
                  'предложения',
                  'предложений',
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
