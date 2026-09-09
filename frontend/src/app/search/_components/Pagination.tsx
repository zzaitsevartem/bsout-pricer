import React from 'react';
import { cn } from '@/shared/lib/utils';
import { buildPageItems } from '@/app/search/_components/lib';

const CELL = 'flex items-center justify-center rounded-full w-9 h-9 text-[14px] font-medium';

type PaginationProps = {
  page: number;
  totalPages: number;
  onPageChange: (value: number) => void;
};

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  const items = buildPageItems(page, totalPages);
  const prevDisabled = page <= 1;
  const nextDisabled = page >= totalPages;

  return (
    <nav className="flex justify-center mt-8" aria-label="Страницы результатов">
      <div className="inline-flex items-center">
        <button
          type="button"
          disabled={prevDisabled}
          onClick={() => onPageChange(page - 1)}
          aria-label="Предыдущая страница"
          className={cn(
            CELL,
            'border border-border-default bg-ivory text-body',
            prevDisabled
              ? 'border-border-light-subtle bg-ivory-elevated text-body-muted cursor-not-allowed'
              : 'hover:bg-ivory-elevated',
          )}
        >
          ←
        </button>
        {items.map((item, index) =>
          item === 'gap' ? (
            <span
              key={`gap-${index}`}
              className={cn(CELL, 'text-body bg-ivory border border-border-default -ml-px')}
            >
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              onClick={() => onPageChange(item)}
              aria-current={item === page ? 'page' : undefined}
              className={cn(
                CELL,
                '-ml-px',
                item === page
                  ? 'text-ivory bg-slate border border-slate z-10'
                  : 'text-body bg-ivory border border-border-default hover:bg-ivory-elevated',
              )}
            >
              {item}
            </button>
          ),
        )}
        <button
          type="button"
          disabled={nextDisabled}
          onClick={() => onPageChange(page + 1)}
          aria-label="Следующая страница"
          className={cn(
            CELL,
            '-ml-px border border-border-default bg-ivory text-body',
            nextDisabled
              ? 'border-border-light-subtle bg-ivory-elevated text-body-muted cursor-not-allowed'
              : 'hover:bg-ivory-elevated',
          )}
        >
          →
        </button>
      </div>
    </nav>
  );
}
