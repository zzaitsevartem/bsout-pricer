'use client';

import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { userApi } from '@/models/user/service';
import { userDataReceived } from '@/models/auth';

export function AuthGate() {
  const initialized = useRef(false);

  const hasToken = typeof window !== 'undefined' && !!localStorage.getItem('access_token');

  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['user', 'me'],
    queryFn: () => userApi.getMe().then((r) => r.data),
    enabled: hasToken,
    retry: false,
    staleTime: 60 * 1000,
  });

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    if (!hasToken) {
      userDataReceived(null);
    }
  }, [hasToken]);

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        userDataReceived(user);
      } else if (isError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        userDataReceived(null);
      }
    }
  }, [isLoading, user, isError]);

  return null;
}
