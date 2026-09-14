'use client';

import { type ReactNode, useEffect } from 'react';
import { authHydrated, setAuth } from '@/shared/config/store';

export function AuthProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    authHydrated(Boolean(localStorage.getItem('access_token')));

    const onStorage = (event: StorageEvent) => {
      if (event.key === 'access_token') {
        setAuth(Boolean(event.newValue));
      }
    };

    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  return <>{children}</>;
}
