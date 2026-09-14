'use client';

import { type ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUnit } from 'effector-react';
import { $authReady, $isAuth } from '@/shared/config/store';

export function RequireAuth({ children }: { children: ReactNode }) {
  const router = useRouter();
  const isAuth = useUnit($isAuth);
  const ready = useUnit($authReady);

  useEffect(() => {
    if (ready && !isAuth) {
      router.replace('/login');
    }
  }, [ready, isAuth, router]);

  if (!ready) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-64px)] text-body-subtle text-[15px]">
        Загрузка…
      </div>
    );
  }

  if (!isAuth) {
    return null;
  }

  return <>{children}</>;
}
