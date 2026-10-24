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
          className="absolute top-full left-0 right-0 z-30 mt-2 overflow-hidden rounded-2xl border border-border-input bg-ivory-elevated shadow-lg"
        >
          {items.map((item, index) => (
            <li key={item.id} role="presentation">
              <button
                type="button"
                role="option"
                tabIndex={-1}
                id={`${listId}-${index}`}
                aria-selected={index === activeIndex}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(item.canonical_name)}
                className={cn(
                  'w-full px-4 py-3 text-left text-[14px] text-slate hover:bg-ivory-warm focus-visible:outline-slate',
                  index === activeIndex && 'bg-ivory-warm',
                )}
              >
                {item.canonical_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
