'use client';

import React, { useEffect, useId, useState } from 'react';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { useCatalogSuggestions } from '@/models/catalog';
import type { CatalogSearchParams } from '@/models/catalog';
import { cn } from '@/shared/lib/utils';

type ProductSearchFieldProps = {
  value: string;
  onValueChange: (value: string) => void;
  onSelect: (value: string) => void;
  suggestionsEnabled?: boolean;
  filters?: CatalogSearchParams;
  id?: string;
  label: string;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
};

function HighlightedName({ name, query }: { name: string; query: string }) {
  const term = query.trim();
  const start = term ? name.toLocaleLowerCase().indexOf(term.toLocaleLowerCase()) : -1;
  if (start < 0) return <>{name}</>;

  return (
    <>
      {name.slice(0, start)}
      <strong className="font-semibold text-slate">{name.slice(start, start + term.length)}</strong>
      {name.slice(start + term.length)}
    </>
  );
}

export function ProductSearchField({
  value,
  onValueChange,
  onSelect,
  suggestionsEnabled = true,
  filters,
  id,
  label,
  placeholder,
  className,
  inputClassName,
}: ProductSearchFieldProps) {
  const isAuth = useUnit($isAuth);
  const listId = useId();
  const [focused, setFocused] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [suggestionText, setSuggestionText] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setSuggestionText(value), 200);
    return () => clearTimeout(timer);
  }, [value]);
  const ready =
    suggestionsEnabled &&
    isAuth &&
    focused &&
    !dismissed &&
    suggestionText === value &&
    value.trim().length >= 2;
  const suggestions = useCatalogSuggestions(
    { ...filters, q: suggestionText, limit: 6 },
    { enabled: ready },
  );
  const items = ready ? (suggestions.data ?? []) : [];
  const expanded = items.length > 0;
  const choose = (value: string) => {
    setDismissed(true);
    setActiveIndex(-1);
    onSelect(value);
  };
  return (
    <div className={cn('relative min-w-0', className)}>
      <input
        type="search"
        maxLength={500}
        value={value}
        onChange={(event) => {
          onValueChange(event.target.value);
          setActiveIndex(-1);
          setDismissed(false);
        }}
        onFocus={() => {
          setFocused(true);
          setDismissed(false);
        }}
        onBlur={() => {
          setFocused(false);
          setActiveIndex(-1);
        }}
        role={suggestionsEnabled ? 'combobox' : undefined}
        aria-autocomplete={suggestionsEnabled ? 'list' : undefined}
        aria-expanded={suggestionsEnabled ? expanded : undefined}
        aria-controls={expanded ? listId : undefined}
        aria-activedescendant={
          expanded && activeIndex >= 0 && activeIndex < items.length
            ? `${listId}-${activeIndex}`
            : undefined
        }
        onKeyDown={(event) => {
          if (event.key === 'Enter' && (!expanded || activeIndex < 0)) setDismissed(true);
          if (event.key === 'Escape') {
            setDismissed(true);
            setActiveIndex(-1);
          }
          if (expanded && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
            event.preventDefault();
            setActiveIndex((index) =>
              event.key === 'ArrowDown'
                ? (index + 1) % items.length
                : index <= 0
                  ? items.length - 1
                  : index - 1,
            );
          }
          if (expanded && event.key === 'Enter' && activeIndex >= 0 && items[activeIndex]) {
            event.preventDefault();
            choose(items[activeIndex].canonical_name);
          }
        }}
        id={id}
        aria-label={label}
        className={inputClassName}
        placeholder={placeholder}
      />
      {expanded && (
        <ul
          id={listId}
          role="listbox"
          aria-label="Подсказки поиска"
          className="absolute top-full left-0 right-0 z-30 mt-2 max-h-[min(60vh,24rem)] overflow-y-auto rounded-2xl border border-border-light-subtle bg-search-surface p-2 shadow-lg"
        >
          {items.map((item, index) => (
            <li key={item.id} role="presentation" className="border-b border-border-light-subtle last:border-b-0">
              <button
                type="button"
                role="option"
                tabIndex={-1}
                id={`${listId}-${index}`}
                aria-selected={index === activeIndex}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(item.canonical_name)}
                className={cn(
                  'block w-full whitespace-normal break-words rounded-lg border-l-2 px-3 py-3.5 text-left text-[14px] leading-5 text-body-subtle transition-colors hover:border-brand-green hover:bg-brand-green/10 focus-visible:outline-slate',
                  index === activeIndex
                    ? 'border-brand-green bg-brand-green/10'
                    : 'border-transparent bg-search-surface',
                )}
              >
                <HighlightedName name={item.canonical_name} query={value} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
