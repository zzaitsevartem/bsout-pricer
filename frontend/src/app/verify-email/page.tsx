'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/widgets/Header/ui/Header';
import {
  useConfirmEmailChangeOld,
  useConfirmEmailChangeNew,
  useFreezeEmailChange,
} from '@/models/user';
import { authApi } from '@/models/auth';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const purpose = searchParams.get('purpose') ?? 'email_verify';
  const confirmOld = useConfirmEmailChangeOld();
  const confirmNew = useConfirmEmailChangeNew();
  const freeze = useFreezeEmailChange();

  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [result, setResult] = useState<null | 'old_confirmed' | 'new_confirmed' | 'frozen'>(
    null,
  );

  useEffect(() => {
    let cancelled = false;

    async function verify() {
      if (!token) {
        setStatus('error');
        setErrorMessage('Отсутствует токен подтверждения.');
        return;
      }
      setStatus('loading');
      try {
        if (purpose === 'email_change_old') {
          await confirmOld.mutateAsync(token);
          if (!cancelled) setResult('old_confirmed');
        } else if (purpose === 'email_change_new') {
          await confirmNew.mutateAsync(token);
          if (!cancelled) setResult('new_confirmed');
        } else if (purpose === 'email_change_freeze') {
          await freeze.mutateAsync(token);
          if (!cancelled) setResult('frozen');
        } else {
          await authApi.confirmEmail(token);
          if (!cancelled) setResult(null);
        }
        if (!cancelled) {
          setStatus('success');
        }
      } catch (err) {
        if (!cancelled) {
          setStatus('error');
          setErrorMessage(extractError(err));
        }
      }
    }

    verify();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, purpose]);

  const title = () => {
    if (result === 'old_confirmed') return 'Шаг 1 подтверждён';
    if (result === 'new_confirmed') return 'Адрес почты обновлён';
    if (result === 'frozen') return 'Аккаунт заморожен';
    if (status === 'error' && errorMessage.toLowerCase().includes('заморожен')) {
      return 'Аккаунт заморожен';
    }
    return 'Почта подтверждена';
  };

  const message = () => {
    if (result === 'old_confirmed') {
      return 'Мы проверили вашу старую почту. Откройте письмо, отправленное на новый адрес, и подтвердите второй шаг.';
    }
    if (result === 'new_confirmed') {
      return 'Ваш новый адрес электронной почты сохранён. Смена завершена.';
    }
    if (result === 'frozen') {
      return 'Ваш аккаунт был заморожен для защиты. Свяжитесь с поддержкой, чтобы восстановить доступ.';
    }
    return 'Спасибо! Ваш email подтверждён.';
  };

  return (
    <div className="flex-1 flex items-center justify-center px-10 py-12 bg-ivory">
      <div className="w-full max-w-[480px] bg-ivory border border-border-light rounded-[24px] p-12 text-center">
        {status === 'loading' && (
          <>
            <h1 className="text-[28px] font-bold text-slate mb-3">Проверяем ссылку…</h1>
            <p className="text-body mb-0">Пожалуйста, подождите.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <h1 className="text-[28px] font-bold text-slate mb-3">{title()}</h1>
            <p className="text-body mb-6">{message()}</p>
            {result === 'frozen' ? (
              <Link href="/" className="btn-primary btn-sm inline-flex">
                На главную
              </Link>
            ) : (
              <Link href="/account/settings" className="btn-primary btn-sm inline-flex">
                Перейти в настройки
              </Link>
            )}
          </>
        )}

        {status === 'error' && (
          <>
            <h1 className="text-[28px] font-bold text-slate mb-3">Не удалось подтвердить</h1>
            <p className="text-body mb-6">{errorMessage}</p>
            <Link href="/account/settings" className="btn-primary btn-sm inline-flex">
              Вернуться в настройки
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

function extractError(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } }).response?.data
      ?.detail;
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message: unknown }).message);
    }
  }
  return 'Что-то пошло не так. Попробуйте ещё раз или запросите письмо повторно.';
}

export default function VerifyEmailPage() {
  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] flex flex-col">
        <Suspense fallback={null}>
          <VerifyEmailContent />
        </Suspense>
      </div>
    </>
  );
}
