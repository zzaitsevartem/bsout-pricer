import React, { type ReactNode } from 'react';
import Link from 'next/link';
import type { CatalogSortOption } from '@/models/catalog';
import { SearchFilters } from '@/app/search/_components/SearchFilters';
import { SORT_OPTIONS } from '@/app/search/_components/lib';
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
};

export function SearchLayout({
  state,
  controls,
  facets,
  summary,
  actions,
  children,
}: SearchLayoutProps) {
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

  return (
    <div className="max-w-[1200px] mx-auto px-6">
      <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-lg:grid-cols-1">
        <SearchFilters
          facets={facets}
          state={state}
          onFilterChange={controls.onFilterChange}
          onReset={controls.onReset}
          hasActiveFilters={chips.length > 0}
        />

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

          <form
            className="flex gap-3 mb-6"
            onSubmit={(event) => {
              event.preventDefault();
              controls.onSubmit();
            }}
          >
            <div className="relative flex-1">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-body-subtle pointer-events-none"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              <input
                type="text"
                value={controls.text}
                onChange={(event) => controls.onTextChange(event.target.value)}
                aria-label="Поиск запчастей"
                className="w-full rounded-full pl-9 pr-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate"
                placeholder="Поиск запчастей..."
              />
            </div>
            <button type="submit" className="btn-primary">
              Найти
            </button>
          </form>

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
                    className="appearance-none rounded-full pr-9 pl-3 py-2 text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate"
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
