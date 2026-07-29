'use client';

import React, { useEffect } from 'react';
import { useUnit } from 'effector-react';
import { useRouter } from 'next/navigation';
import { $isAuth, $authPending } from '../../models/auth/store';

interface Props {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: Props) {
  const isAuth = useUnit($isAuth);
  const authPending = useUnit($authPending);
  const router = useRouter();

  useEffect(() => {
    if (!authPending && !isAuth) {
      router.replace('/login');
    }
  }, [authPending, isAuth, router]);

  if (authPending) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-body-muted text-sm">Загрузка…</div>
      </div>
    );
  }

  if (!isAuth) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-body-muted text-sm">Перенаправление…</div>
      </div>
    );
  }

  return <>{children}</>;
}
