'use client';

import { type ReactNode } from 'react';
import { QueryProvider } from './QueryProvider';
import { AuthGate } from '@/features/auth';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <AuthGate />
      {children}
    </QueryProvider>
  );
}
