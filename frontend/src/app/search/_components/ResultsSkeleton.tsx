import React from 'react';

export function ResultsSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-[24px] overflow-hidden bg-ivory-elevated" aria-hidden="true">
      {Array.from({ length: rows }, (_, index) => (
        <div
          key={index}
          className="flex gap-4 p-4 items-center border-b border-border-light-subtle last:border-b-0"
        >
          <div className="w-16 h-16 bg-ivory-warm flex-shrink-0 animate-pulse" />
          <div className="flex-1 min-w-0">
            <div className="h-4 w-2/3 bg-ivory-warm mb-2 animate-pulse" />
            <div className="h-3 w-1/3 bg-ivory-warm animate-pulse" />
          </div>
          <div className="flex flex-col items-end gap-2 flex-shrink-0">
            <div className="h-5 w-24 bg-ivory-warm animate-pulse" />
            <div className="h-3 w-32 bg-ivory-warm animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}
