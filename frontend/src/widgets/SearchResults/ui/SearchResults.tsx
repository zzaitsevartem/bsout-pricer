'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import type { ProductResponse } from '@/models/product';

type SearchResultsProps = {
  products: ProductResponse[];
  total: number;
  totalPages: number;
  page: number;
  sortBy: string;
  isLoading: boolean;
  isError: boolean;
  isPremium: boolean;
  onPageChange: (page: number) => void;
  onSortChange: (sortBy: string) => void;
};

const SORT_OPTIONS = [
  { value: 'price_asc', label: 'Сначала дешёвые' },
  { value: 'price_desc', label: 'Сначала дорогие' },
  { value: 'date', label: 'По дате обновления' },
];

function formatPrice(raw: string): string {
  const num = parseFloat(raw);
  if (isNaN(num)) return raw;
  return num.toLocaleString('ru-RU') + ' ₽';
}

function ProductRow({ product, index }: { product: ProductResponse; index: number }) {
  return (
    <Link
      key={product.id}
      href={`/product?id=${product.id}`}
      className={`flex gap-4 p-4 items-center border-b border-border-light-subtle last:border-b-0 no-underline transition-colors hover:bg-ivory-warm/50 ${
        index % 2 === 1 ? 'bg-ivory-warm/30' : ''
      }`}
    >
      {/* Thumbnail */}
      <div className="w-16 h-16 bg-ivory-warm flex items-center justify-center text-body-muted text-xs flex-shrink-0 rounded-[8px] overflow-hidden">
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="2" y="2" width="20" height="20" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15l-5-5L5 21" />
          </svg>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="text-base font-semibold text-slate block mb-1 hover:underline">
          {product.name}
        </div>
        <div className="text-[14px] text-body-subtle flex gap-3 flex-wrap">
          <span>{product.store?.name ?? '—'}</span>
          {product.in_stock ? (
            <span className="text-olive">В наличии</span>
          ) : (
            <span className="text-body-muted">Нет в наличии</span>
          )}
        </div>
      </div>

      {/* Price */}
      <div className="text-right flex-shrink-0">
        <div className={`text-lg font-bold ${product.is_cheapest ? 'text-olive' : 'text-slate'}`}>
          {formatPrice(product.price)}
        </div>
        {product.old_price && (
          <div className="text-[14px] text-body-muted line-through">
            {formatPrice(product.old_price)}
          </div>
        )}
        {product.is_cheapest && (
          <div className="text-[12px] text-olive font-semibold">— Самый дешёвый</div>
        )}
      </div>
    </Link>
  );
}

function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}) {
  const pageNumbers = useMemo(() => {
    const pages: number[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (page > 3) pages.push(-1);
      for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
      if (page < totalPages - 2) pages.push(-2);
      pages.push(totalPages);
    }
    return pages;
  }, [totalPages, page]);

  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center mt-8">
      <div className="inline-flex items-center">
        {/* Previous */}
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className={`flex items-center justify-center w-9 h-9 text-[14px] font-medium border no-underline -ml-px transition-colors ${
            page <= 1
              ? 'text-body-muted border-border-light-subtle bg-ivory-elevated pointer-events-none'
              : 'text-body bg-ivory border-border-default hover:bg-ivory-elevated'
          }`}
        >
          ←
        </button>

        {/* Pages */}
        {pageNumbers.map((p, i) =>
          p < 0 ? (
            <span
              key={`ellipsis-${i}`}
              className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-body bg-ivory border border-border-default -ml-px"
            >
              …
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`flex items-center justify-center w-9 h-9 text-[14px] font-medium border no-underline -ml-px transition-colors ${
                p === page
                  ? 'text-ivory bg-slate border-slate z-10'
                  : 'text-body bg-ivory border-border-default hover:bg-ivory-elevated'
              }`}
            >
              {p}
            </button>
          ),
        )}

        {/* Next */}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className={`flex items-center justify-center w-9 h-9 text-[14px] font-medium border no-underline -ml-px transition-colors ${
            page >= totalPages
              ? 'text-body-muted border-border-light-subtle bg-ivory-elevated pointer-events-none'
              : 'text-body bg-ivory border-border-default hover:bg-ivory-elevated'
          }`}
        >
          →
        </button>
      </div>
    </div>
  );
}

export function SearchResults({
  products,
  total,
  totalPages,
  page,
  sortBy,
  isLoading,
  isError,
  isPremium,
  onPageChange,
  onSortChange,
}: SearchResultsProps) {
  return (
    <div>
      {/* Sort and count */}
      <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
        <span className="text-[15px] text-body-subtle">
          {isLoading ? 'Поиск...' : `Найдено: ${total} товар${total % 10 === 1 && total % 100 !== 11 ? '' : 'ов'}`}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[15px] text-body-subtle">Сортировка:</span>
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value)}
              className="appearance-none pr-9 pl-3 py-2 text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 w-0 h-0 border-l-[5px] border-r-[5px] border-t-[5px] border-body-subtle pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="text-body-muted text-[15px]">Загрузка результатов...</div>
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center">
            <div className="text-red-500 text-[15px] mb-2">Ошибка загрузки</div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && products.length === 0 && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center">
            <div className="text-body-muted text-[15px] mb-1">Ничего не найдено</div>
            <div className="text-body-muted text-[13px]">Попробуйте изменить параметры поиска</div>
          </div>
        </div>
      )}

      {/* Premium upsell banner for non-subscribers with limited results */}
      {!isPremium && !isLoading && !isError && products.length > 0 && (
        <div className="mb-8 p-6 bg-olive rounded-[16px] flex items-center justify-between gap-4 max-md:flex-col max-md:text-center shadow-lg">
          <div className="flex items-start gap-4 max-md:flex-col max-md:items-center">
            <div className="w-11 h-11 rounded-full bg-white/20 flex items-center justify-center shrink-0">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <div>
              <div className="text-[18px] font-bold text-white mb-1">
                {total > products.length
                  ? `Найдено ${total} товаров — показано только ${products.length}`
                  : `Это только предпросмотр`}
              </div>
              <div className="text-[15px] text-white/80 max-w-[480px]">
                {total > products.length
                  ? `Оформите подписку, чтобы видеть все результаты с полным доступом к истории цен.`
                  : `Оформите подписку для полного доступа к поиску и истории цен.`}
              </div>
            </div>
          </div>
          <Link href="/tariffs" className="inline-flex items-center gap-2 px-6 py-3.5 bg-white text-olive font-bold text-[15px] rounded-[12px] no-underline whitespace-nowrap shrink-0 hover:bg-white/90 transition-colors shadow-md">
            Выбрать тариф →
          </Link>
        </div>
      )}

      {/* Results list */}
      {!isLoading && !isError && products.length > 0 && (
        <>
          <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
            {products.map((product, idx) => (
              <ProductRow key={product.id} product={product} index={idx} />
            ))}
          </div>

          <Pagination page={page} totalPages={totalPages} onPageChange={onPageChange} />
        </>
      )}
    </div>
  );
}
