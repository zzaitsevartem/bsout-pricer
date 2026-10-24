'use client';

import React, { useMemo, useState } from 'react';
import { useCatalogSearch } from '@/models/catalog';
import type { CatalogSearchParams } from '@/models/catalog';
import { useStores } from '@/models/store';
import { useProductSearch } from '@/models/product';
import type { ProductSearchParams } from '@/models/product';
import { useExportCatalog } from '@/models/export';
import type { ExportCatalogParams } from '@/models/export';
import { cn } from '@/shared/lib/utils';
import { TrackingButtonsProvider } from '@/widgets/TrackButton/ui/TrackButton';
import { SearchLayout } from '@/app/search/_components/SearchLayout';
import { ExportCsvButton, ExportNotice } from '@/widgets/CatalogExport/ui/CatalogExport';
import { CatalogResultCard } from '@/app/search/_components/CatalogResultCard';
import { OfferResultCard } from '@/app/search/_components/OfferResultCard';
import { ResultsSkeleton } from '@/app/search/_components/ResultsSkeleton';
import { Pagination } from '@/app/search/_components/Pagination';
import {
  EMPTY_FACETS,
  FACETS_SAMPLE_SIZE,
  OFFERS_PER_PAGE,
  PER_PAGE,
  apiErrorMessage,
  collectFacets,
  foundLabel,
} from '@/app/search/_components/lib';
import type { SearchControls, SearchUrlState } from '@/app/search/_components/lib';

type CatalogSearchViewProps = {
  state: SearchUrlState;
  controls: SearchControls;
};

export function CatalogSearchView({ state, controls }: CatalogSearchViewProps) {
  const params = useMemo<CatalogSearchParams>(
    () => ({
      q: state.q || undefined,
      device_id: state.device_id,
      part_type_id: state.part_type_id,
      quality_tier_id: state.quality_tier_id,
      store: state.store,
      min_price: state.min_price,
      max_price: state.max_price,
      in_stock: state.in_stock,
      sort_by: state.sort_by,
      page: state.page,
      per_page: PER_PAGE,
    }),
    [
      state.q,
      state.device_id,
      state.part_type_id,
      state.quality_tier_id,
      state.store,
      state.min_price,
      state.max_price,
      state.in_stock,
      state.sort_by,
      state.page,
    ],
  );

  const facetParams = useMemo<CatalogSearchParams>(
    () => ({
      q: state.q || undefined,
      sort_by: 'min_price_asc',
      page: 1,
      per_page: FACETS_SAMPLE_SIZE,
    }),
    [state.q],
  );

  const exportParams = useMemo<ExportCatalogParams>(
    () => ({
      q: state.q || undefined,
      device_id: state.device_id,
      part_type_id: state.part_type_id,
      quality_tier_id: state.quality_tier_id,
      store: state.store,
      min_price: state.min_price,
      max_price: state.max_price,
      in_stock: state.in_stock,
      sort_by: state.sort_by,
    }),
    [
      state.q,
      state.device_id,
      state.part_type_id,
      state.quality_tier_id,
      state.sort_by,
      state.store,
      state.min_price,
      state.max_price,
      state.in_stock,
    ],
  );

  const results = useCatalogSearch(params);
  const facetsQuery = useCatalogSearch(facetParams);
  const exportCatalog = useExportCatalog();

  const [offersExpanded, setOffersExpanded] = useState(false);

  const offersParams = useMemo<ProductSearchParams>(
    () => ({
      q: state.q || undefined,
      store: state.store,
      min_price: state.min_price,
      max_price: state.max_price,
      in_stock: state.in_stock,
      sort_by: 'price_asc',
      page: 1,
      per_page: OFFERS_PER_PAGE,
    }),
    [state.q, state.store, state.min_price, state.max_price, state.in_stock],
  );
  const offersQuery = useProductSearch(offersParams, { enabled: offersExpanded });

  const storesQuery = useStores();

  const facets = useMemo(
    () => ({
      ...(facetsQuery.data ? collectFacets(facetsQuery.data.results) : EMPTY_FACETS),
      stores: (storesQuery.data ?? []).filter((store) => store.is_active),
    }),
    [facetsQuery.data, storesQuery.data],
  );

  const total = results.data?.total;
  const perPage = results.data?.per_page ?? PER_PAGE;
  const totalPages = total === undefined ? 0 : Math.max(1, Math.ceil(total / perPage));

  const summary = results.isError
    ? 'Не удалось загрузить результаты'
    : total === undefined
      ? 'Загрузка…'
      : foundLabel(total);

  let content: React.ReactNode;

  const hasCatalog = (results.data?.results.length ?? 0) > 0;
  const hasOffers = (offersQuery.data?.results.length ?? 0) > 0;

  if (results.isLoading) {
    content = <ResultsSkeleton />;
  } else if (results.isError) {
    content = (
      <div className="rounded-[24px] bg-ivory-elevated p-8 text-center">
        <p className="text-[15px] text-clay mb-4">
          {apiErrorMessage(results.error, 'Не удалось загрузить результаты поиска')}
        </p>
        <button type="button" onClick={() => results.refetch()} className="btn-secondary btn-sm">
          Повторить
        </button>
      </div>
    );
  } else if (!hasCatalog) {
    content = (
      <div className="rounded-[24px] bg-ivory-elevated p-8 text-center">
        <p className="text-base font-semibold text-slate mb-2">Ничего не найдено</p>
        <p className="text-[15px] text-body-subtle">
          {state.q
            ? `По запросу «${state.q}» товаров нет. Попробуйте изменить запрос или снять фильтры.`
            : 'Уточните запрос или снимите фильтры — по текущим условиям товаров нет.'}
        </p>
      </div>
    );
  } else {
    content = hasCatalog ? (
      <>
        <div
          className={cn(
            'rounded-[24px] overflow-hidden bg-ivory-elevated transition-opacity',
            results.isFetching && 'opacity-60',
          )}
        >
          <TrackingButtonsProvider>
            {(results.data?.results ?? []).map((item) => (
              <CatalogResultCard key={item.id} item={item} />
            ))}
          </TrackingButtonsProvider>
        </div>
        <Pagination
          page={state.page}
          totalPages={totalPages}
          onPageChange={controls.onPageChange}
        />
      </>
    ) : null;
  }

  const hasResults = hasCatalog;
  const offersTotal = offersQuery.data?.total ?? 0;
  const shownOffers = offersQuery.data?.results ?? [];

  const offersSection = (
    <section className="mt-8 border-t border-border-light-subtle pt-6">
      <button
        type="button"
        onClick={() => setOffersExpanded((open) => !open)}
        aria-expanded={offersExpanded}
        aria-controls="store-offers"
        className="btn-secondary btn-sm"
      >
        {offersExpanded ? 'Скрыть предложения магазинов' : 'Показать предложения магазинов'}
      </button>
      {offersExpanded && (
        <div id="store-offers" className="mt-4">
          {offersQuery.isLoading ? (
            <ResultsSkeleton />
          ) : offersQuery.isError ? (
            <div role="alert">
              <p className="text-clay">Не удалось загрузить предложения магазинов</p>
              <button
                type="button"
                className="btn-secondary btn-sm mt-2"
                onClick={() => offersQuery.refetch()}
              >
                Повторить загрузку предложений
              </button>
            </div>
          ) : hasOffers ? (
            <>
              <h2 className="text-xl font-semibold text-slate mb-4">
                Предложения магазинов: {offersTotal}
              </h2>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {shownOffers.map((offer) => (
                  <OfferResultCard key={offer.id} item={offer} />
                ))}
              </div>
              {offersTotal > shownOffers.length && (
                <p className="text-[14px] text-body-subtle mt-3">
                  Показаны первые {shownOffers.length} из {offersTotal}. Уточните запрос, чтобы
                  увидеть остальные.
                </p>
              )}
            </>
          ) : (
            <p className="text-body-subtle">
              Предложения магазинов не найдены по выбранным условиям.
            </p>
          )}
        </div>
      )}
    </section>
  );

  return (
    <SearchLayout
      suggestionsEnabled
      state={state}
      controls={controls}
      facets={facets}
      summary={summary}
      actions={
        <ExportCsvButton
          mutation={exportCatalog}
          params={exportParams}
          disabled={!hasResults || results.isFetching}
        />
      }
    >
      {exportCatalog.error && <ExportNotice error={exportCatalog.error} />}
      {content}
      {offersSection}
    </SearchLayout>
  );
}
