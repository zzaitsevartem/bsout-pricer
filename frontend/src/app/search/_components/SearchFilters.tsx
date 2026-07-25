import React from 'react';
import { cn } from '@/shared/lib/utils';
import { withSelected } from '@/app/search/_components/lib';
import type {
  CatalogFacets,
  FilterKey,
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
  const visible = withSelected(options, selectedId);

  if (visible.length === 0) {
    return null;
  }

  return (
    <div className="pb-6 mb-6 border-b border-border-light-subtle">
      <h4 className="text-[15px] font-semibold text-slate mb-3">{title}</h4>
      <div className="flex flex-col gap-2">
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
                  'w-[18px] h-[18px] border flex items-center justify-center flex-shrink-0 transition-colors',
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
  onFilterChange: (key: FilterKey, value: number | null) => void;
  onReset: () => void;
  hasActiveFilters: boolean;
};

export function SearchFilters({
  facets,
  state,
  onFilterChange,
  onReset,
  hasActiveFilters,
}: SearchFiltersProps) {
  const isEmpty =
    facets.qualityTiers.length === 0 &&
    facets.devices.length === 0 &&
    facets.partTypes.length === 0 &&
    !hasActiveFilters;

  return (
    <aside className="sticky top-20 self-start max-lg:hidden">
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

      {isEmpty && (
        <div className="pb-6 mb-6 border-b border-border-light-subtle">
          <h4 className="text-[15px] font-semibold text-slate mb-3">Фильтры</h4>
          <p className="text-[14px] text-body-muted">
            Фильтры появятся, когда в выдаче будут товары.
          </p>
        </div>
      )}

      <div className="mb-6">
        <h4 className="text-[15px] font-semibold text-slate mb-3">Скоро</h4>
        <p className="text-[14px] text-body-muted">
          Отбор по магазину, диапазону цены и наличию каталог пока не поддерживает.
        </p>
      </div>

      {hasActiveFilters && (
        <button type="button" onClick={onReset} className="btn-ghost w-full justify-center">
          Сбросить фильтры
        </button>
      )}
    </aside>
  );
}
