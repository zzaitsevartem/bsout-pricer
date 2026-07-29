'use client';

import Link from 'next/link';
import { useProduct, usePriceHistory } from '@/models/product';
import { PriceHistoryChart } from './PriceHistoryChart';

function formatPrice(raw: string): string {
  const num = parseFloat(raw);
  if (isNaN(num)) return raw;
  return num.toLocaleString('ru-RU') + ' ₽';
}

type ProductDetailProps = {
  productId: number | null;
};

export function ProductDetail({ productId }: ProductDetailProps) {
  const { data: product, isLoading, isError, error } = useProduct(productId ?? 0);
  const { data: priceHistory = [], isLoading: isHistoryLoading, isError: isHistoryError, error: historyError } = usePriceHistory(productId ?? 0);

  const isHistoryForbidden = isHistoryError &&
    (historyError as { response?: { status?: number } })?.response?.status === 403;

  // No ID provided
  if (!productId) {
    return (
      <div className="max-w-[1200px] mx-auto px-6 py-16 text-center">
        <div className="text-body-muted text-[15px] mb-2">Товар не выбран</div>
        <Link href="/search" className="btn-primary no-underline inline-block">
          Перейти к поиску
        </Link>
      </div>
    );
  }

  // Loading
  if (isLoading) {
    return (
      <div className="max-w-[1200px] mx-auto px-6 py-8 pb-16">
        <div className="animate-pulse space-y-6">
          <div className="h-4 bg-ivory-elevated rounded w-64" />
          <div className="grid grid-cols-2 gap-12 max-md:grid-cols-1">
            <div className="aspect-square bg-ivory-elevated rounded-[24px]" />
            <div className="space-y-4">
              <div className="h-4 bg-ivory-elevated rounded w-24" />
              <div className="h-8 bg-ivory-elevated rounded w-3/4" />
              <div className="h-4 bg-ivory-elevated rounded w-full" />
              <div className="h-32 bg-ivory-elevated rounded-[24px]" />
              <div className="h-32 bg-ivory-elevated rounded-[24px]" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // API error (401, 403, 404, 500)
  if (isError || !product) {
    const status = (error as { response?: { status?: number } })?.response?.status;
    const messages: Record<number, { title: string; description: string }> = {
      401: { title: 'Требуется авторизация', description: 'Войдите в аккаунт для просмотра товара' },
      403: { title: 'Требуется подписка', description: 'Для просмотра товаров необходима активная подписка' },
      404: { title: 'Товар не найден', description: 'Возможно, он был удалён или ссылка недействительна' },
    };
    const msg = status ? messages[status] : null;

    return (
      <div className="max-w-[1200px] mx-auto px-6 py-16 text-center">
        <div className="text-[24px] font-semibold text-slate mb-2">{msg?.title ?? 'Ошибка загрузки'}</div>
        <div className="text-body-muted text-[15px] mb-6">{msg?.description ?? 'Попробуйте обновить страницу'}</div>
        <div className="flex gap-3 justify-center">
          {status === 401 && (
            <Link href="/login" className="btn-primary no-underline inline-block">Войти</Link>
          )}
          {status === 403 && (
            <Link href="/tariffs" className="btn-primary no-underline inline-block">Выбрать тариф</Link>
          )}
          <Link href="/search" className="btn-secondary no-underline inline-block">Вернуться к поиску</Link>
        </div>
      </div>
    );
  }

  // Success — render product
  return (
    <div className="max-w-[1200px] mx-auto px-6 py-8 pb-16">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
        <Link href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</Link>
        <span className="text-body-muted">/</span>
        <Link href="/search" className="text-body-subtle no-underline hover:text-slate hover:underline">Поиск</Link>
        <span className="text-body-muted">/</span>
        <span>{product.name}</span>
      </div>

      <div className="grid grid-cols-2 gap-12 max-md:grid-cols-1">
        {/* Image */}
        <div>
          <div className={`rounded-[24px] ${product.image_url ? 'overflow-hidden' : 'bg-ivory-elevated'} aspect-square flex items-center justify-center text-body-muted text-[15px] border border-border-light`}>
            {product.image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-full object-contain"
              />
            ) : (
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                <rect x="2" y="2" width="20" height="20" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
            )}
          </div>
        </div>

        {/* Info */}
        <div>
          {/* Stock badge */}
          {product.in_stock ? (
            <span className="inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-success-soft border border-[#C7D2B0] text-[#4F5C36] mb-4">
              В наличии
            </span>
          ) : (
            <span className="inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-ivory-warm border border-border-light text-body-muted mb-4">
              Нет в наличии
            </span>
          )}

          <h1 className="text-[32px] font-bold text-slate mb-2">{product.name}</h1>

          {product.description && (
            <p className="text-[15px] text-body-subtle mb-6">{product.description}</p>
          )}

          {/* Store offer */}
          <div className="rounded-[24px] p-6 bg-ivory-elevated mb-6">
            <div className="flex justify-between items-center">
              <div>
                <span className="font-semibold text-slate">{product.store?.name ?? 'Магазин'}</span>
                {product.is_cheapest && (
                  <span className="ml-2 inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-success-soft border border-[#C7D2B0] text-[#4F5C36]">
                    Самый дешёвый
                  </span>
                )}
              </div>
              <div className="text-right">
                <div className={`text-lg font-bold ${product.is_cheapest ? 'text-olive' : 'text-slate'}`}>
                  {formatPrice(product.price)}
                </div>
                {product.old_price && (
                  <div className="text-[14px] text-body-muted line-through">
                    {formatPrice(product.old_price)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Price history */}
          <h4 className="text-xl font-semibold text-slate mb-4">История цены</h4>
          {isHistoryLoading ? (
            <div className="w-full h-[120px] bg-ivory-elevated rounded-[12px] animate-pulse" />
          ) : isHistoryForbidden ? (
            <div className="w-full rounded-[16px] p-4 bg-ivory-warm border border-border-light flex items-center justify-between gap-3 max-md:flex-col">
              <div className="text-[15px] text-body-subtle">
                История цен доступна по подписке
              </div>
              <Link href="/tariffs" className="btn-primary no-underline whitespace-nowrap text-sm">
                Выбрать тариф
              </Link>
            </div>
          ) : priceHistory.length > 0 ? (
            <PriceHistoryChart data={priceHistory} />
          ) : (
            <p className="text-[15px] text-body-subtle">Нет данных об изменении цены</p>
          )}

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            {product.product_url && (
              <a
                href={product.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary no-underline inline-flex items-center"
              >
                Перейти в магазин →
              </a>
            )}
            <button className="btn-secondary">В избранное</button>
          </div>
        </div>
      </div>
    </div>
  );
}
