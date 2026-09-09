'use client';

import React, { useId, useState } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/shared/lib/utils';
import { CloseIcon, SearchIcon } from '@/shared/ui/IconSVG';

type HeaderSearchProps = {
  className?: string;
  onSubmitted?: () => void;
};

const HeaderSearch: React.FC<HeaderSearchProps> = ({ className, onSubmitted }) => {
  const [value, setValue] = useState('');
  const inputId = useId();
  const router = useRouter();

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const query = value.trim();
    router.push(query ? `/search?q=${encodeURIComponent(query)}` : '/search');
    onSubmitted?.();
  };

  return (
    <form role="search" onSubmit={handleSubmit} className={cn(className)}>
      <label htmlFor={inputId} className="sr-only">
        Поиск запчастей
      </label>
      <div className="relative flex h-11 items-center rounded-full border border-border-default bg-ivory-elevated transition-colors focus-within:border-slate focus-within:bg-ivory focus-within:shadow-sm">
        <input
          id={inputId}
          type="search"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Поиск запчастей…"
          className="block h-full w-full min-w-0 bg-transparent py-0 pl-4 pr-20 text-[15px] tracking-[-0.002em] text-slate placeholder:text-body-muted focus:outline-none [&::-webkit-search-cancel-button]:appearance-none"
        />
        {value && (
          <button
            type="button"
            onClick={() => setValue('')}
            aria-label="Очистить поиск"
            className="absolute right-10 top-1/2 flex -translate-y-1/2 items-center justify-center border-none bg-transparent p-0 text-body-subtle transition-colors hover:text-slate focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate"
          >
            <CloseIcon />
          </button>
        )}
        <button
          type="submit"
          className="absolute right-1.5 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border-none bg-transparent p-0 text-body-subtle transition-colors hover:bg-ivory-warm hover:text-slate focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate"
          aria-label="Найти"
        >
          <SearchIcon />
        </button>
      </div>
    </form>
  );
};

export { HeaderSearch };
