'use client';

import React, { useEffect, useRef, useState } from 'react';

import { SearchIcon } from '@/shared/ui/IconSVG';
import { ProductSearchField } from '@/widgets/ProductSearch/ui/ProductSearchField';
import type { CatalogSearchParams } from '@/models/catalog';

type SearchInputProps = {
  query: string;
  onQueryChange: (value: string) => void;
  suggestionsEnabled?: boolean;
  filters?: CatalogSearchParams;
};

export function SearchInput({
  query,
  onQueryChange,
  suggestionsEnabled = false,
  filters,
}: SearchInputProps) {
  const [text, setText] = useState(query);
  const committed = useRef(query);
  const choose = (value: string) => {
    committed.current = value;
    setText(value);
    onQueryChange(value);
  };

  useEffect(() => {
    if (query !== committed.current) {
      committed.current = query;
      setText(query);
    }
  }, [query]);

  useEffect(() => {
    if (text === committed.current) return;
    const timer = setTimeout(() => {
      if (text === committed.current) return;
      committed.current = text;
      onQueryChange(text);
    }, 350);
    return () => clearTimeout(timer);
  }, [text, onQueryChange]);

  return (
    <form
      className="flex gap-3 mb-6"
      onSubmit={(event) => {
        event.preventDefault();
        committed.current = text;
        onQueryChange(text);
      }}
    >
      <div className="relative flex-1 min-w-0">
        <SearchIcon className="absolute z-10 left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <ProductSearchField
          value={text}
          onValueChange={setText}
          onSelect={choose}
          suggestionsEnabled={suggestionsEnabled}
          filters={filters}
          label="Поиск запчастей"
          placeholder="Поиск запчастей..."
          inputClassName="w-full rounded-full pl-11 pr-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
        />
      </div>
      <button type="submit" className="btn-primary">
        Найти
      </button>
    </form>
  );
}
