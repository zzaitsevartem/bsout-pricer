'use client';

import React, { Suspense, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/widgets/Header/ui/Header';
import { useVkCallback } from '@/models/auth';

function extractError(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const data = (error as { response?: { data?: { detail?: unknown } } }).response?.data;
    const detail = data?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message: unknown }).message);
    }
  }
  return 'Не удалось войти через ВКонтакте. Попробуйте ещё раз или войдите по паролю.';
}

function VkCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const code = searchParams.get('code') ?? '';
  const state = searchParams.get('state') ?? '';
  const callback = useVkCallback();
  const started = useRef(false);

  useEffect(() => {
    if (started.current || !code || !state) {
      return;
    }
    started.current = true;
    callback.mutate({ code, state }, { onSuccess: () => router.push('/account') });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, state]);

  return (
    <div className="flex-1 flex items-center justify-center px-10 py-12 bg-ivory max-md:px-5">
      <div className="w-full max-w-[480px] bg-ivory border border-border-light rounded-[24px] p-12 max-md:p-8 text-center">
        {!code || !state ? (
          <>
            <h1 className="text-[28px] font-bold text-slate mb-3">Нет данных от ВКонтакте</h1>
            <p className="text-body mb-6">
              В ссылке отсутствуют параметры входа. Начните вход заново.
            </p>
            <Link href="/login" className="btn-primary btn-sm inline-flex">
              Вернуться ко входу
            </Link>
          </>
        ) : callback.isSuccess ? (
          <>
            <h1 className="text-[28px] font-bold text-slate mb-3">Вход выполнен</h1>
            <p className="text-body mb-6">Перенаправляем в личный кабинет…</p>
          </>
        ) : callback.isError ? (
          <>
            <h1 className="text-[28px] font-bold text-slate mb-3">Не удалось войти</h1>
            <p className="text-body mb-6">{extractError(callback.error)}</p>
            <Link href="/login" className="btn-primary btn-sm inline-flex">
              Вернуться ко входу
            </Link>
          </>
        ) : (
          <>
            <h1 className="text-[28px] font-bold text-slate mb-3">Входим через ВКонтакте…</h1>
            <p className="text-body mb-0">Пожалуйста, подождите.</p>
          </>
        )}
      </div>
    </div>
  );
}

export default function VkCallbackPage() {
  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] flex flex-col">
        <Suspense fallback={null}>
          <VkCallbackContent />
        </Suspense>
      </div>
    </>
  );
}
