'use client';

import { type ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useMe } from '@/models/user';

function AdminGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: me, isLoading } = useMe();

  useEffect(() => {
    if (me && !me.is_admin) {
      router.replace('/account');
    }
  }, [me, router]);

  if (isLoading || !me) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-64px)] text-body-subtle text-[15px]">
        Загрузка…
      </div>
    );
  }

  if (!me.is_admin) {
    return null;
  }

  return <>{children}</>;
}

export function RequireAdmin({ children }: { children: ReactNode }) {
  return (
    <RequireAuth>
      <AdminGate>{children}</AdminGate>
    </RequireAuth>
  );
}
