import React, { useState } from 'react';
import { cn } from '@/shared/lib/utils';
import { withSelected } from '@/app/search/_components/lib';
import type {
  CatalogFacets,
  FilterKey,
  FilterValue,
  SearchControls,
  FilterOption,
  SearchUrlState,
} from '@/app/search/_components/lib';

type FilterGroupProps = {
  title: string;
  options: FilterOption[];
  selectedId?: number;
  onSelect: (value: number | null) => void;
};

function FilterGroup({ title, options, selectedId, onSelect }: FilterGroupProps) {
  const [search, setSearch] = useState('');
  const allOptions = withSelected(options, selectedId);
  const searchable = allOptions.length > 8;
  const visible =
    searchable && search.trim()
      ? allOptions.filter(
          (option) =>
            option.id === selectedId ||
            option.label.toLocaleLowerCase('ru').includes(search.trim().toLocaleLowerCase('ru')),
        )
      : allOptions;

  if (allOptions.length === 0) {
    return null;
  }

  return (
    <div className="pb-6 mb-6 border-b border-border-light-subtle">
      <h4 className="text-[15px] font-semibold text-slate mb-3">{title}</h4>
      {searchable && (
        <input
          type="search"
          aria-label={`Найти: ${title.toLocaleLowerCase('ru')}`}
          placeholder="Найти…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="mb-3 w-full rounded-xl p-2 text-slate bg-ivory border border-border-input focus-visible:outline-slate"
        />
      )}
      <div className="flex max-h-48 overflow-y-auto flex-col gap-2 pr-1">
        {visible.map((option) => {
          const selected = option.id === selectedId;
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => onSelect(selected ? null : option.id)}
              aria-pressed={selected}
              className={cn(
                'inline-flex items-center gap-2 text-left text-[15px] transition-colors',
                selected ? 'text-slate font-medium' : 'text-body-subtle hover:text-slate',
              )}
            >
              <span
                className={cn(
                  'w-[18px] h-[18px] rounded-full border flex items-center justify-center flex-shrink-0 transition-colors',
                  selected ? 'bg-slate border-slate text-ivory' : 'bg-ivory border-body-muted',
                )}
              >
                {selected && (
                  <svg width="12" height="6" viewBox="0 0 12 6" fill="none">
                    <path
                      d="M1 3L4 6L11 1"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </span>
              <span className="min-w-0 truncate">{option.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

type SearchFiltersProps = {
  facets: CatalogFacets;
  state: SearchUrlState;
  onFilterChange: (key: FilterKey, value: FilterValue) => void;
  onPriceChange: SearchControls['onPriceChange'];
  onReset: () => void;
  hasActiveFilters: boolean;
};

export function SearchFilters({
  facets,
  state,
  onFilterChange,
  onReset,
  onPriceChange,
  hasActiveFilters,
}: SearchFiltersProps) {
  return (
    <aside aria-label="Фильтры каталога">
      <FilterGroup
        title="Класс качества"
        options={facets.qualityTiers}
        selectedId={state.quality_tier_id}
        onSelect={(value) => onFilterChange('quality_tier_id', value)}
      />
      <FilterGroup
        title="Тип детали"
        options={facets.partTypes}
        selectedId={state.part_type_id}
        onSelect={(value) => onFilterChange('part_type_id', value)}
      />
      <FilterGroup
        title="Устройство"
        options={facets.devices}
        selectedId={state.device_id}
        onSelect={(value) => onFilterChange('device_id', value)}
      />

      <div className="pb-6 mb-6 border-b border-border-light-subtle">
        <label htmlFor="catalog-store" className="block text-[15px] font-semibold text-slate mb-3">
          Магазин
        </label>
        <select
          id="catalog-store"
          value={state.store ?? ''}
          onChange={(event) => onFilterChange('store', event.target.value || null)}
          className="w-full rounded-xl p-2 text-slate bg-ivory border border-border-input focus-visible:outline-slate"
        >
          <option value="">Все магазины</option>
          {state.store && !facets.stores?.some((store) => store.slug === state.store) && (
            <option value={state.store}>{state.store}</option>
          )}
          {facets.stores?.map((store) => (
            <option key={store.slug} value={store.slug}>
              {store.name}
            </option>
          ))}
        </select>
      </div>
      <PriceRange
        key={`${state.min_price ?? ''}:${state.max_price ?? ''}`}
        state={state}
        onApply={onPriceChange}
      />
      <div className="mb-6">
        <label htmlFor="catalog-stock" className="block text-[15px] font-semibold text-slate mb-3">
          Наличие
        </label>
        <select
          id="catalog-stock"
          value={state.in_stock === undefined ? '' : String(state.in_stock)}
          onChange={(event) =>
            onFilterChange(
              'in_stock',
              event.target.value === '' ? null : event.target.value === 'true',
            )
          }
          className="w-full rounded-xl p-2 text-slate bg-ivory border border-border-input focus-visible:outline-slate"
        >
          <option value="">Любое наличие</option>
          <option value="true">В наличии</option>
          <option value="false">Нет в наличии</option>
        </select>
      </div>

      {hasActiveFilters && (
        <button type="button" onClick={onReset} className="btn-ghost w-full justify-center">
          Сбросить фильтры
        </button>
      )}
    </aside>
  );
}

function PriceRange({
  state,
  onApply,
}: {
  state: SearchUrlState;
  onApply: SearchControls['onPriceChange'];
}) {
  return (
    <form
      className="pb-6 mb-6 border-b border-border-light-subtle"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const minInput = form.elements.namedItem('min_price') as HTMLInputElement;
        const maxInput = form.elements.namedItem('max_price') as HTMLInputElement;
        const min = minInput.value === '' ? null : minInput.valueAsNumber;
        const max = maxInput.value === '' ? null : maxInput.valueAsNumber;
        maxInput.setCustomValidity(
          min !== null && max !== null && min > max
            ? 'Максимальная цена должна быть не меньше минимальной'
            : '',
        );
        if (form.reportValidity()) onApply(min, max);
      }}
    >
      <fieldset>
        <legend className="text-[15px] font-semibold text-slate mb-3">Цена, ₽</legend>
        <div className="flex gap-2 mb-3">
          <label className="min-w-0 flex-1 text-[14px] text-body-subtle">
            От
            <input
              name="min_price"
              type="number"
              min="0"
              step="0.01"
              defaultValue={state.min_price}
              onInput={(event) => {
                const form = event.currentTarget.form;
                (form?.elements.namedItem('max_price') as HTMLInputElement)?.setCustomValidity('');
              }}
              className="w-full rounded-xl p-2 text-slate bg-ivory border border-border-input focus-visible:outline-slate"
            />
          </label>
          <label className="min-w-0 flex-1 text-[14px] text-body-subtle">
            До
            <input
              name="max_price"
              type="number"
              min="0"
              step="0.01"
              defaultValue={state.max_price}
              onInput={(event) => event.currentTarget.setCustomValidity('')}
              className="w-full rounded-xl p-2 text-slate bg-ivory border border-border-input focus-visible:outline-slate"
            />
          </label>
        </div>
        <button type="submit" className="btn-secondary btn-sm w-full">
          Применить цену
        </button>
      </fieldset>
    </form>
  );
}
