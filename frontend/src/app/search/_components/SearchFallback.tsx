import React from 'react';
import { ResultsSkeleton } from '@/app/search/_components/ResultsSkeleton';

export function SearchFallback() {
  return (
    <div className="max-w-[1200px] mx-auto px-6">
      <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-lg:grid-cols-1">
        <aside className="sticky top-20 self-start max-lg:hidden" aria-hidden="true">
          {Array.from({ length: 3 }, (_, index) => (
            <div key={index} className="pb-6 mb-6 border-b border-border-light-subtle">
              <div className="h-4 w-28 bg-ivory-elevated mb-3 animate-pulse" />
              <div className="flex flex-col gap-2">
                <div className="h-4 w-full bg-ivory-elevated animate-pulse" />
                <div className="h-4 w-3/4 bg-ivory-elevated animate-pulse" />
              </div>
            </div>
          ))}
        </aside>
        <main>
          <div className="h-[42px] w-full bg-ivory-elevated mb-6 animate-pulse" aria-hidden="true" />
          <ResultsSkeleton />
        </main>
      </div>
    </div>
  );
}
