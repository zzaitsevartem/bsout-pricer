import React from 'react';
import Image from 'next/image';
import type { ProductResponse } from '@/models/product';
import { formatPrice } from '@/app/search/_components/lib';

function stockLabel(status: string): string | null {
  switch (status) {
    case 'in_stock':
      return 'В наличии';
    case 'low':
      return 'Заканчивается';
    case 'out':
      return 'Нет в наличии';
    case 'preorder':
      return 'Предзаказ';
    default:
      return null;
  }
}

function PlaceholderImage() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <rect x="2" y="2" width="20" height="20" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <path d="M21 15l-5-5L5 21" />
    </svg>
  );
}

export function OfferResultCard({ item }: { item: ProductResponse }) {
  const stock = stockLabel(item.stock_status);

  return (
    <div className="flex gap-4 p-4 items-center border-b border-border-light-subtle last:border-b-0">
      <div className="w-16 h-16 bg-ivory-warm flex items-center justify-center text-body-muted text-xs flex-shrink-0 overflow-hidden">
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.title}
            width={64}
            height={64}
            unoptimized
            loading="lazy"
            className="w-full h-full object-cover"
          />
        ) : (
          <PlaceholderImage />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="text-base font-semibold text-slate no-underline block mb-1 hover:underline"
        >
          {item.title}
        </a>
        <div className="text-[14px] text-body-subtle flex gap-3 flex-wrap items-center">
          {item.store && <span>{item.store.name}</span>}
          {stock && <span>{stock}</span>}
        </div>
      </div>

      <div className="text-right flex-shrink-0">
        <div className="text-lg font-bold text-slate">{formatPrice(item.price_retail)}</div>
        {item.price_opt && (
          <div className="text-[14px] text-body-muted">опт {formatPrice(item.price_opt)}</div>
        )}
      </div>
    </div>
  );
}
