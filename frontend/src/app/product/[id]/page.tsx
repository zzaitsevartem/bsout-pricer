'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { useCatalogProduct } from '@/models/catalog';
import { OffersTable } from '@/app/product/[id]/_components/OffersTable';
import { PriceStats } from '@/app/product/[id]/_components/PriceStats';
import { PriceHistory } from '@/app/product/[id]/_components/PriceHistory';
import { Alternatives } from '@/app/product/[id]/_components/Alternatives';
import {
  CHIP,
  apiErrorMessage,
  apiErrorStatus,
  parseProductId,
} from '@/app/product/[id]/_components/lib';

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-8 pb-16">{children}</div>
      <Footer />
    </>
  );
}

function Breadcrumbs({ current }: { current: string }) {
  return (
    <div className="flex items-center gap-2 text-[14px] text-body-muted mb-6 flex-wrap">
      <Link href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">
        Главная
      </Link>
      <span>/</span>
      <Link
        href="/search"
        className="text-body-subtle no-underline hover:text-slate hover:underline"
      >
        Поиск
      </Link>
      <span>/</span>
      <span className="text-body">{current}</span>
    </div>
  );
}

function NotFoundState() {
  return (
    <Shell>
      <Breadcrumbs current="Товар не найден" />
      <div className="rounded-[24px] border border-border-light bg-ivory-elevated p-10 text-center">
        <h1 className="text-[32px] font-bold text-slate mb-3">Товар не найден</h1>
        <p className="text-[15px] text-body-subtle mb-6 max-w-[520px] mx-auto">
          Такого товара нет в каталоге — возможно, он был объединён с другой позицией или ссылка
          устарела. Попробуйте найти нужную деталь через поиск.
        </p>
        <Link href="/search" className="btn-primary">
          Перейти к поиску
        </Link>
      </div>
    </Shell>
  );
}

function LoadingState() {
  return (
    <Shell>
      <Breadcrumbs current="Загрузка…" />
      <div className="h-8 w-2/3 bg-ivory-elevated animate-pulse mb-4 rounded-[8px]" />
      <div className="h-5 w-1/3 bg-ivory-elevated animate-pulse mb-8 rounded-[8px]" />
      <div className="h-[132px] bg-ivory-elevated animate-pulse mb-4 rounded-[24px]" />
      <div className="grid grid-cols-4 gap-4 mb-10 max-lg:grid-cols-2 max-[480px]:grid-cols-1">
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="h-[112px] bg-ivory-elevated animate-pulse rounded-[24px]" />
        ))}
      </div>
      <div className="h-[280px] bg-ivory-elevated animate-pulse rounded-[24px]" />
    </Shell>
  );
}

export default function ProductComparisonPage({ params }: { params: { id: string } }) {
  const productId = parseProductId(params.id);
  const comparison = useCatalogProduct(productId ?? 0);

  if (productId === null) {
    return <NotFoundState />;
  }

  if (comparison.isLoading) {
    return <LoadingState />;
  }

  if (comparison.isError) {
    if (apiErrorStatus(comparison.error) === 404) {
      return <NotFoundState />;
    }

    return (
      <Shell>
        <Breadcrumbs current="Ошибка" />
        <div className="rounded-[24px] border border-border-light bg-ivory-elevated p-10 text-center">
          <h1 className="text-[24px] font-semibold text-slate mb-3">
            Не удалось загрузить товар
          </h1>
          <p className="text-[15px] text-clay mb-6">
            {apiErrorMessage(comparison.error, 'Попробуйте обновить страницу чуть позже')}
          </p>
          <button type="button" onClick={() => comparison.refetch()} className="btn-primary">
            Повторить
          </button>
        </div>
      </Shell>
    );
  }

  const data = comparison.data;

  if (!data) {
    return <NotFoundState />;
  }

  const { product, stats, offers, alternatives } = data;

  const attributes = Object.entries(product.key_attrs ?? {}).filter(
    ([, value]) => typeof value === 'string' || typeof value === 'number',
  );

  return (
    <Shell>
      <Breadcrumbs current={product.canonical_name} />

      <header className="mb-8">
        <h1 className="text-[32px] font-bold text-slate mb-3 leading-tight">
          {product.canonical_name}
        </h1>

        <div className="flex items-center gap-2 flex-wrap">
          {product.brand && <span className={CHIP}>{product.brand.name}</span>}
          {product.device && <span className={CHIP}>{product.device.name}</span>}
          {product.part_type && <span className={CHIP}>{product.part_type.name_ru}</span>}
          {product.quality_tier && (
            <span className="inline-flex items-center text-[13px] px-2.5 py-1 bg-slate text-ivory border border-slate">
              {product.quality_tier.name_ru}
            </span>
          )}
          {attributes.map(([key, value]) => (
            <span key={key} className={CHIP}>
              {key}: {String(value)}
            </span>
          ))}
        </div>
      </header>

      <PriceStats stats={stats} />

      <section className="mb-10">
        <h2 className="text-[24px] font-semibold text-slate mb-1">Предложения магазинов</h2>
        <p className="text-[15px] text-body-subtle mb-4">
          Одна и та же деталь в разных магазинах — от самой низкой цены к самой высокой.
        </p>
        <OffersTable offers={offers} />
      </section>

      <PriceHistory productId={productId} />

      <Alternatives alternatives={alternatives} currentMinPrice={stats.min_price_retail} />
    </Shell>
  );
}
