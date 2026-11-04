import React, { useState, type ReactNode } from 'react';
import Link from 'next/link';
import type { CatalogSortOption } from '@/models/catalog';
import { SearchInput } from '@/app/search/_components/SearchInput';
import { SearchFilters } from '@/app/search/_components/SearchFilters';
import { SORT_OPTIONS } from '@/app/search/_components/lib';
import { cn } from '@/shared/lib/utils';
import type {
  CatalogFacets,
  FilterKey,
  FilterOption,
  SearchControls,
  SearchUrlState,
} from '@/app/search/_components/lib';

function labelFor(options: FilterOption[], id: number): string {
  return options.find((option) => option.id === id)?.label ?? `#${id}`;
}

type SearchLayoutProps = {
  state: SearchUrlState;
  controls: SearchControls;
  facets: CatalogFacets;
  summary: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  suggestionsEnabled?: boolean;
};

export function SearchLayout({
  state,
  controls,
  facets,
  summary,
  actions,
  children,
  suggestionsEnabled = false,
}: SearchLayoutProps) {
  const [filtersOpen, setFiltersOpen] = useState(false);
  const chips: { key: FilterKey; label: string }[] = [];
  if (state.quality_tier_id !== undefined) {
    chips.push({
      key: 'quality_tier_id',
      label: labelFor(facets.qualityTiers, state.quality_tier_id),
    });
  }
  if (state.part_type_id !== undefined) {
    chips.push({ key: 'part_type_id', label: labelFor(facets.partTypes, state.part_type_id) });
  }
  if (state.device_id !== undefined) {
    chips.push({ key: 'device_id', label: labelFor(facets.devices, state.device_id) });
  }

  if (state.store)
    chips.push({
      key: 'store',
      label: facets.stores?.find((store) => store.slug === state.store)?.name ?? state.store,
    });
  if (state.min_price !== undefined)
    chips.push({ key: 'min_price', label: `От ${state.min_price} ₽` });
  if (state.max_price !== undefined)
    chips.push({ key: 'max_price', label: `До ${state.max_price} ₽` });
  if (state.in_stock !== undefined)
    chips.push({ key: 'in_stock', label: state.in_stock ? 'В наличии' : 'Нет в наличии' });

  return (
    <div className="max-w-[1200px] mx-auto px-6">
      <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-lg:grid-cols-1">
        <div className="self-start lg:sticky lg:top-20">
          <div className="rounded-2xl border border-border-light-subtle p-4 lg:border-0 lg:p-0">
            <button
              type="button"
              className="flex w-full items-center justify-between font-semibold text-slate lg:hidden"
              aria-expanded={filtersOpen}
              aria-controls="catalog-filters-panel"
              onClick={() => setFiltersOpen((open) => !open)}
            >
              Фильтры{chips.length > 0 ? ` (${chips.length})` : ''}
              <span aria-hidden="true">{filtersOpen ? '−' : '+'}</span>
            </button>
            <div
              id="catalog-filters-panel"
              className={cn('mt-4 lg:mt-0 lg:block', !filtersOpen && 'hidden')}
            >
              <SearchFilters
                facets={facets}
                state={state}
                onFilterChange={controls.onFilterChange}
                onPriceChange={controls.onPriceChange}
                onReset={controls.onReset}
                hasActiveFilters={chips.length > 0}
              />
            </div>
          </div>
        </div>

        <main>
          <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
            <Link
              href="/"
              className="text-body-subtle no-underline hover:text-slate hover:underline"
            >
              Главная
            </Link>
            <span className="text-body-muted">/</span>
            <span>Поиск</span>
          </div>

          <SearchInput
            query={state.q}
            onQueryChange={controls.onQueryChange}
            suggestionsEnabled={suggestionsEnabled}
            filters={{
              store: state.store,
              min_price: state.min_price,
              max_price: state.max_price,
              in_stock: state.in_stock,
              device_id: state.device_id,
              part_type_id: state.part_type_id,
              quality_tier_id: state.quality_tier_id,
            }}
          />

          {chips.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap mb-4">
              {chips.map((chip) => (
                <button
                  key={chip.key}
                  type="button"
                  onClick={() => controls.onFilterChange(chip.key, null)}
                  className="inline-flex items-center gap-2 rounded-full text-[14px] text-slate bg-ivory-elevated border border-border-subtle px-3 py-1 transition-colors hover:bg-ivory-warm"
                >
                  {chip.label}
                  <span aria-hidden="true">×</span>
                  <span className="sr-only">Убрать фильтр</span>
                </button>
              ))}
              <button
                type="button"
                onClick={controls.onReset}
                className="text-[14px] text-body-subtle underline underline-offset-[3px] hover:text-slate"
              >
                Сбросить всё
              </button>
            </div>
          )}

          <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
            <span className="text-[15px] text-body-subtle">{summary}</span>
            <div className="flex items-center gap-4 flex-wrap">
              {actions}
              <div className="flex items-center gap-2">
                <label htmlFor="catalog-sort" className="text-[15px] text-body-subtle">
                  Сортировка:
                </label>
                <div className="relative">
                  <select
                    id="catalog-sort"
                    value={state.sort_by}
                    onChange={(event) =>
                      controls.onSortChange(event.target.value as CatalogSortOption)
                    }
                    className="appearance-none rounded-full pr-9 pl-3 py-2 text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
                  >
                    {SORT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 w-0 h-0 border-l-[5px] border-r-[5px] border-t-[5px] border-body-subtle pointer-events-none" />
                </div>
              </div>
            </div>
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}
