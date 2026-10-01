'use client';

import React, { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Header } from '@/widgets/Header/ui/Header';
import {
  passwordResetRequestSchema,
  passwordResetConfirmSchema,
  useRequestPasswordReset,
  useConfirmPasswordReset,
  type PasswordResetRequest,
  type PasswordResetConfirm,
} from '@/models/auth';

function extractError(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
  }
  return 'Что-то пошло не так. Попробуйте ещё раз.';
}

function RequestForm() {
  const requestReset = useRequestPasswordReset();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PasswordResetRequest>({
    resolver: zodResolver(passwordResetRequestSchema),
  });

  if (requestReset.isSuccess) {
    return (
      <div className="text-center">
        <h1 className="text-[28px] font-bold text-slate mb-3">Проверьте почту</h1>
        <p className="text-body mb-6">
          Если такой адрес зарегистрирован, мы отправили письмо со ссылкой. Ссылка действует 1 час и
          сработает один раз.
        </p>
        <Link href="/login" className="btn-primary btn-sm inline-flex">
          Вернуться ко входу
        </Link>
      </div>
    );
  }

  return (
    <>
      <h1 className="text-[32px] font-bold text-slate mb-2">Восстановление пароля</h1>
      <p className="text-lg text-body mb-8">Укажите почту — пришлём ссылку для сброса.</p>

      <form onSubmit={handleSubmit((data) => requestReset.mutate(data))} noValidate>
        <div className="mb-6">
          <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">
            Email
          </label>
          <input
            type="email"
            id="email"
            {...register('email')}
            placeholder="your@email.com"
            className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
          />
          {errors.email && <p className="text-[13px] text-clay mt-[6px]">{errors.email.message}</p>}
        </div>

        {requestReset.isError && (
          <p className="text-[14px] text-clay mb-4">{extractError(requestReset.error)}</p>
        )}

        <button
          type="submit"
          disabled={requestReset.isPending}
          className="btn-primary w-full justify-center disabled:opacity-60"
        >
          {requestReset.isPending ? 'Отправляем…' : 'Отправить ссылку'}
        </button>
      </form>
    </>
  );
}

function ConfirmForm({ token }: { token: string }) {
  const confirmReset = useConfirmPasswordReset();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PasswordResetConfirm>({
    resolver: zodResolver(passwordResetConfirmSchema),
    defaultValues: { token },
  });

  if (confirmReset.isSuccess) {
    return (
      <div className="text-center">
        <h1 className="text-[28px] font-bold text-slate mb-3">Пароль изменён</h1>
        <p className="text-body mb-6">
          Всё готово — старые сеансы отозваны. Войдите с новым паролем.
        </p>
        <Link href="/login" className="btn-primary btn-sm inline-flex">
          Войти
        </Link>
      </div>
    );
  }

  return (
    <>
      <h1 className="text-[32px] font-bold text-slate mb-2">Новый пароль</h1>
      <p className="text-lg text-body mb-8">Придумайте пароль минимум из 8 символов.</p>

      <form
        onSubmit={handleSubmit((data) =>
          confirmReset.mutate({ token: data.token, new_password: data.new_password }),
        )}
        noValidate
      >
        <div className="mb-4">
          <label htmlFor="new_password" className="block text-[15px] font-medium text-slate mb-2">
            Новый пароль
          </label>
          <input
            type="password"
            id="new_password"
            {...register('new_password')}
            placeholder="Минимум 8 символов"
            className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
          />
          {errors.new_password && (
            <p className="text-[13px] text-clay mt-[6px]">{errors.new_password.message}</p>
          )}
        </div>

        <div className="mb-6">
          <label
            htmlFor="confirm_password"
            className="block text-[15px] font-medium text-slate mb-2"
          >
            Повторите пароль
          </label>
          <input
            type="password"
            id="confirm_password"
            {...register('confirm_password')}
            placeholder="Повторите пароль"
            className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
          />
          {errors.confirm_password && (
            <p className="text-[13px] text-clay mt-[6px]">{errors.confirm_password.message}</p>
          )}
        </div>

        {confirmReset.isError && (
          <p className="text-[14px] text-clay mb-4">{extractError(confirmReset.error)}</p>
        )}

        <button
          type="submit"
          disabled={confirmReset.isPending}
          className="btn-primary w-full justify-center disabled:opacity-60"
        >
          {confirmReset.isPending ? 'Сохраняем…' : 'Сменить пароль'}
        </button>
      </form>
    </>
  );
}

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';

  return (
    <div className="flex-1 flex items-center justify-center px-10 py-12 bg-ivory max-md:px-5">
      <div className="w-full max-w-[480px] bg-ivory border border-border-light rounded-[24px] p-12 max-md:p-8">
        {token ? <ConfirmForm token={token} /> : <RequestForm />}
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] flex flex-col">
        <Suspense fallback={null}>
          <ResetPasswordContent />
        </Suspense>
      </div>
    </>
  );
}
