'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { cn } from '@/shared/lib/utils';
import {
  trackingGate,
  useEveryTrackedProduct,
  useTrackProduct,
  useUntrackProduct,
} from '@/models/tracking';
import type { TrackingGate } from '@/models/tracking';

type TrackButtonProps = {
  productId: number;
  size?: 'sm' | 'md';
  className?: string;
};

function BellIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth="1.5"
      aria-hidden="true"
    >
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

function GateNotice({ gate, compact }: { gate: TrackingGate; compact: boolean }) {
  return (
    <div
      role="status"
      className={cn(
        'mt-2 border border-border-default bg-ivory-elevated p-3 text-[13px] text-body-subtle text-left',
        compact ? 'max-w-[280px]' : 'max-w-[420px]',
      )}
    >
      <p className="mb-2">{gate.message}</p>
      {(gate.kind === 'limit' || gate.kind === 'subscription') && (
        <Link href="/tariffs" className="btn-secondary btn-sm">
          {gate.kind === 'limit' ? 'Повысить тариф' : 'Выбрать тариф'}
        </Link>
      )}
    </div>
  );
}

export function TrackButton({ productId, size = 'md', className }: TrackButtonProps) {
  const isAuth = useUnit($isAuth);
  const [gate, setGate] = useState<TrackingGate | null>(null);

  const tracked = useEveryTrackedProduct({ enabled: isAuth });
  const track = useTrackProduct();
  const untrack = useUntrackProduct();

  const sizeClass = size === 'sm' ? 'btn-sm' : '';
  const entry = tracked.data?.find((item) => item.product_id === productId && item.is_active);
  const pending = track.isPending || untrack.isPending;

  if (!isAuth) {
    return (
      <Link
        href="/login"
        className={cn('btn-secondary inline-flex items-center gap-2', sizeClass, className)}
      >
        <BellIcon filled={false} />
        Отслеживать
      </Link>
    );
  }

  const handleClick = () => {
    setGate(null);
    if (entry) {
      untrack.mutate(entry.id, {
        onError: (error) => setGate(trackingGate(error)),
      });
      return;
    }
    track.mutate(
      { product_id: productId },
      {
        onError: (error) => setGate(trackingGate(error)),
      },
    );
  };

  return (
    <div className={cn('inline-block', className)}>
      <button
        type="button"
        onClick={handleClick}
        disabled={pending || tracked.isLoading}
        className={cn(
          entry ? 'btn-primary' : 'btn-secondary',
          sizeClass,
          'inline-flex items-center gap-2 disabled:opacity-60',
        )}
        aria-pressed={Boolean(entry)}
      >
        <BellIcon filled={Boolean(entry)} />
        {entry ? 'Отслеживается' : 'Отслеживать'}
      </button>
      {gate && <GateNotice gate={gate} compact={size === 'sm'} />}
    </div>
  );
}
