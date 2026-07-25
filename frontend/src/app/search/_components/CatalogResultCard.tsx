import React from 'react';
import Link from 'next/link';
import type { CatalogItemResponse } from '@/models/catalog';
import { formatPrice, offersLabel, storesLabel } from '@/app/search/_components/lib';

function deviceLabel(item: CatalogItemResponse): string | null {
  const parts = [item.brand?.name, item.device?.name].filter(Boolean);
  return parts.length > 0 ? parts.join(' ') : null;
}

export function CatalogResultCard({ item }: { item: CatalogItemResponse }) {
  const device = deviceLabel(item);

  return (
    <div className="flex gap-4 p-4 items-center border-b border-border-light-subtle last:border-b-0">
      <div className="w-16 h-16 bg-ivory-warm flex items-center justify-center text-body-muted text-xs flex-shrink-0">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
      </div>

      <div className="flex-1 min-w-0">
        <Link
          href={`/product/${item.id}`}
          className="text-base font-semibold text-slate no-underline block mb-1 hover:underline"
        >
          {item.canonical_name}
        </Link>
        <div className="text-[14px] text-body-subtle flex gap-3 flex-wrap items-center">
          {device && <span>{device}</span>}
          {item.part_type && <span>{item.part_type.name_ru}</span>}
          {item.quality_tier && (
            <span className="inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-ivory border border-border-default text-body-subtle">
              {item.quality_tier.name_ru}
            </span>
          )}
        </div>
      </div>

      <div className="text-right flex-shrink-0">
        <div className="text-lg font-bold text-slate">
          {item.min_price_retail === null ? 'Нет цены' : `от ${formatPrice(item.min_price_retail)}`}
        </div>
        {item.min_price_opt && (
          <div className="text-[14px] text-body-muted">опт от {formatPrice(item.min_price_opt)}</div>
        )}
        <div className="text-[13px] text-body-subtle">
          {storesLabel(item.stores_count)} · {offersLabel(item.offers_count)}
        </div>
      </div>
    </div>
  );
}
