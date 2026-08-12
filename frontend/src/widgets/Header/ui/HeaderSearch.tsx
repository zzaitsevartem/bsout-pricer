'use client';

import React, { useId, useState } from 'react';
import { useRouter } from 'next/navigation';
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
    <form role="search" onSubmit={handleSubmit} className={className}>
      <label htmlFor={inputId} className="sr-only">
        Поиск запчастей
      </label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-body-subtle pointer-events-none">
          <SearchIcon />
        </span>
        <input
          id={inputId}
          type="search"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Поиск запчастей…"
          className="block w-full h-11 pl-9 pr-9 text-[15px] tracking-[-0.002em] text-slate bg-ivory border border-border-default transition-colors placeholder:text-body-muted focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_var(--color-slate)] [&::-webkit-search-cancel-button]:appearance-none"
        />
        {value && (
          <button
            type="button"
            onClick={() => setValue('')}
            aria-label="Очистить поиск"
            className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center bg-transparent border-none p-0 cursor-pointer text-body-subtle transition-colors hover:text-slate"
          >
            <CloseIcon />
          </button>
        )}
      </div>
      <button type="submit" className="sr-only">
        Найти
      </button>
    </form>
  );
};

export { HeaderSearch };
