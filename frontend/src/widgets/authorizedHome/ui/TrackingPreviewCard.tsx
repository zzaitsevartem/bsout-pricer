import type { ReactNode } from 'react';

export function TrackingPreviewCard({
  header,
  children,
}: {
  header: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-[340px] flex-col gap-4 rounded-[24px] border border-border-light bg-ivory-warm p-6">
      <div className="flex items-center gap-3 bg-slate p-3 text-ivory">{header}</div>
      {children}
    </div>
  );
}

export function TrackingPreviewRow({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-[58px] items-center gap-3 rounded-xl bg-ivory p-3 transition-colors hover:bg-ivory-warm">
      {children}
    </div>
  );
}
