'use client';

import { useState, useEffect } from 'react';
import type { StoreResponse } from '@/models/store';
import type { CategoryResponse } from '@/models/category';

type SearchFiltersProps = {
  stores: StoreResponse[] | undefined;
  categories: CategoryResponse[] | undefined;
  storeSlug: string;
  categorySlug: string;
  inStockParam: string;
  priceMin: string;
  priceMax: string;
  onStoreToggle: (slug: string) => void;
  onCategoryToggle: (slug: string) => void;
  onInStockToggle: () => void;
  onPriceApply: (min: string, max: string) => void;
  onReset: () => void;
};

function Checkbox({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
}) {
  return (
    <label className="inline-flex items-center gap-2 cursor-pointer text-[15px] text-slate">
      <input type="checkbox" checked={checked} onChange={onChange} className="hidden" />
      <span
        className={`w-[18px] h-[18px] border flex items-center justify-center flex-shrink-0 transition-colors ${
          checked ? 'bg-slate border-slate' : 'border-[#87867F] bg-ivory'
        }`}
      >
        {checked && (
          <svg width="12" height="6" viewBox="0 0 12 6" fill="none">
            <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </span>
      {label}
    </label>
  );
}

function FilterSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="pb-6 mb-6 border-b border-border-light-subtle">
      <h4 className="text-[15px] font-semibold text-slate mb-3">{title}</h4>
      {children}
    </div>
  );
}

export function SearchFilters({
  stores,
  categories,
  storeSlug,
  categorySlug,
  inStockParam,
  priceMin,
  priceMax,
  onStoreToggle,
  onCategoryToggle,
  onInStockToggle,
  onPriceApply,
  onReset,
}: SearchFiltersProps) {
  const [priceMinInput, setPriceMinInput] = useState(priceMin);
  const [priceMaxInput, setPriceMaxInput] = useState(priceMax);

  useEffect(() => { setPriceMinInput(priceMin); }, [priceMin]);
  useEffect(() => { setPriceMaxInput(priceMax); }, [priceMax]);

  const handlePriceKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onPriceApply(priceMinInput, priceMaxInput);
  };

  return (
    <aside className="sticky top-20 self-start max-lg:hidden">
      <FilterSection title="Магазин">
        <div className="flex flex-col gap-2">
          {stores?.map((s) => (
            <Checkbox key={s.slug} checked={storeSlug === s.slug} onChange={() => onStoreToggle(s.slug)} label={s.name} />
          ))}
        </div>
      </FilterSection>

      <FilterSection title="Категория">
        <div className="flex flex-col gap-2">
          {categories?.map((c) => (
            <Checkbox key={c.slug} checked={categorySlug === c.slug} onChange={() => onCategoryToggle(c.slug)} label={c.name} />
          ))}
        </div>
      </FilterSection>

      <FilterSection title="Цена">
        <div className="flex gap-2">
          <input
            type="number" value={priceMinInput} onChange={(e) => setPriceMinInput(e.target.value)}
            onKeyDown={handlePriceKeyDown}
            className="w-20 px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate"
            placeholder="от" min={0}
          />
          <input
            type="number" value={priceMaxInput} onChange={(e) => setPriceMaxInput(e.target.value)}
            onKeyDown={handlePriceKeyDown}
            className="w-20 px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate"
            placeholder="до" min={0}
          />
        </div>
        <button onClick={() => onPriceApply(priceMinInput, priceMaxInput)} className="text-[13px] text-slate underline mt-2 hover:no-underline">
          Применить
        </button>
      </FilterSection>

      <FilterSection title="Наличие">
        <Checkbox checked={inStockParam === 'true'} onChange={onInStockToggle} label="Только в наличии" />
      </FilterSection>

      <button onClick={onReset} className="btn-ghost w-full justify-center">
        Сбросить
      </button>
    </aside>
  );
}
