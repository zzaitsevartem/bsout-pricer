'use client';

import React, { useMemo } from 'react';
import { useCatalogSearch } from '@/models/catalog';
import type { CatalogSearchParams } from '@/models/catalog';
import { useExportCatalog } from '@/models/export';
import type { ExportCatalogParams } from '@/models/export';
import { cn } from '@/shared/lib/utils';
import { SearchLayout } from '@/app/search/_components/SearchLayout';
import { ExportCsvButton, ExportNotice } from '@/app/search/_components/CatalogExport';
import { CatalogResultCard } from '@/app/search/_components/CatalogResultCard';
import { ResultsSkeleton } from '@/app/search/_components/ResultsSkeleton';
import { Pagination } from '@/app/search/_components/Pagination';
import {
  EMPTY_FACETS,
  FACETS_SAMPLE_SIZE,
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
      sort_by: state.sort_by,
      page: state.page,
      per_page: PER_PAGE,
    }),
    [
      state.q,
      state.device_id,
      state.part_type_id,
      state.quality_tier_id,
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
      sort_by: state.sort_by,
    }),
    [state.q, state.device_id, state.part_type_id, state.quality_tier_id, state.sort_by],
  );

  const results = useCatalogSearch(params);
  const facetsQuery = useCatalogSearch(facetParams);
  const exportCatalog = useExportCatalog();

  const facets = useMemo(
    () => (facetsQuery.data ? collectFacets(facetsQuery.data.results) : EMPTY_FACETS),
    [facetsQuery.data],
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
  } else if (!results.data || results.data.results.length === 0) {
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
    content = (
      <>
        <div
          className={cn(
            'rounded-[24px] overflow-hidden bg-ivory-elevated transition-opacity',
            results.isFetching && 'opacity-60',
          )}
        >
          {results.data.results.map((item) => (
            <CatalogResultCard key={item.id} item={item} />
          ))}
        </div>
        <Pagination
          page={state.page}
          totalPages={totalPages}
          onPageChange={controls.onPageChange}
        />
      </>
    );
  }

  const hasResults = (results.data?.results.length ?? 0) > 0;

  return (
    <SearchLayout
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
    </SearchLayout>
  );
}
