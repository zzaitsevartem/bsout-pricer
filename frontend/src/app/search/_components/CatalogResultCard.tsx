'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import type { CatalogItemResponse } from '@/models/catalog';
import { formatPrice, offersLabel, storesLabel } from '@/app/search/_components/lib';
import { TrackButton } from '@/widgets/TrackButton/ui/TrackButton';

function deviceLabel(item: CatalogItemResponse): string | null {
  const parts = [item.brand?.name, item.device?.name].filter(Boolean);
  return parts.length > 0 ? parts.join(' ') : null;
}

export function CatalogResultCard({ item }: { item: CatalogItemResponse }) {
  const device = deviceLabel(item);
  const stock = item.stock_status === 'in_stock'
    ? { label: 'В наличии', color: 'text-brand-green' }
    : item.stock_status === 'out'
      ? { label: 'Нет в наличии', color: 'text-stock-unavailable' }
      : item.stock_status === 'preorder'
        ? { label: 'Предзаказ', color: 'text-body-subtle' }
        : null;

  return (
    <div className="flex gap-4 p-4 items-center rounded-2xl border border-border-input bg-ivory-elevated">
      <div className="w-16 h-16 bg-ivory-warm flex items-center justify-center text-body-muted text-xs flex-shrink-0">
        <CatalogImage imageUrl={item.image_url} name={item.canonical_name} />
      </div>

      <div className="flex-1 min-w-0">
        <Link
          href={`/product/${item.id}`}
          className="text-base font-semibold text-slate no-underline block mb-1 hover:underline decoration-brand-green underline-offset-[6px] dark:decoration-current dark:underline-offset-auto"
        >
          {item.canonical_name}
        </Link>
        <div className="text-[14px] text-body-subtle flex gap-3 flex-wrap items-center">
          {device && <span>{device}</span>}
          {item.part_type && <span>{item.part_type.name_ru}</span>}
          {item.quality_tier && item.quality_tier.code !== 'unknown' && (
            <span className={item.quality_tier.code === 'original' ? 'text-brand-green font-medium' : ''}>
              {item.quality_tier.name_ru}
            </span>
          )}
          {stock && <span className={`text-xs font-medium ${stock.color}`}>{stock.label}</span>}
        </div>
      </div>

      <div className="text-right flex-shrink-0">
        <div className="text-lg font-bold text-slate">
            {item.min_price_retail === null ? 'Нет цены' : `от ${formatPrice(item.min_price_retail)}`}
          </div>
          <div className="ml-auto max-w-48 break-words text-sm text-body-muted">
            {item.source ? (
              <>
                Источник цены:{' '}
                <a
                  href={item.source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="break-words underline underline-offset-2 hover:text-slate"
                >
                  {item.source.store_name}
                </a>
              </>
            ) : (
              'Источник недоступен'
            )}
          </div>
        {item.min_price_opt && (
          <div className="text-[14px] text-body-muted">опт от {formatPrice(item.min_price_opt)}</div>
        )}
        <div className="text-[13px] text-body-subtle">
          {storesLabel(item.stores_count)} · {offersLabel(item.offers_count)}
        </div>
        <div className="mt-2 flex justify-end">
          <TrackButton productId={item.id} size="sm" />
        </div>
      </div>
    </div>
  );
}

function CatalogImage({ imageUrl, name }: { imageUrl?: string | null; name: string }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  if (imageUrl && imageUrl !== failedUrl) {
    return (
      <Image
        src={imageUrl}
        alt={name}
        width={64}
        height={64}
        unoptimized
        loading="lazy"
        className="h-16 w-16 object-contain"
        onError={() => setFailedUrl(imageUrl)}
      />
    );
  }
  return (<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>);
}
