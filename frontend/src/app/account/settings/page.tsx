'use client';

import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useUsernameAvailable } from '@/models/auth';
import {
  useMe,
  useUpdateMe,
  useResendVerification,
  useRequestEmailChange,
  useCancelEmailChange,
  userUpdateRequestSchema,
  type UserUpdateRequest,
} from '@/models/user';

function LoginSection({ me }: { me: NonNullable<ReturnType<typeof useMe>['data']> }) {
  const [username, setUsername] = useState(me.username ?? '');
  const updateMe = useUpdateMe();
  const trimmed = username.trim();
  const isValid = /^[a-zA-Z0-9_.-]{3,32}$/.test(trimmed);
  const availability = useUsernameAvailable(isValid ? trimmed : '');
  const unchanged = trimmed === (me.username ?? '');
  const isTaken = !unchanged && availability.data?.data.available === false;
  const serverError =
    updateMe.error && 'response' in updateMe.error
      ? String(
          (
            updateMe.error as {
              response?: { data?: { detail?: string } };
            }
          ).response?.data?.detail ?? '',
        )
      : '';

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid || unchanged || isTaken) return;
    updateMe.mutate({ username: trimmed });
  };

  return (
    <div className="rounded-[24px] p-[31px] bg-ivory-elevated">
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-slate mb-1">Смена логина</h3>
        <p className="text-body-subtle text-[15px] mb-0">
          Текущий логин: {me.username || 'не задан'}
        </p>
      </div>

      <form onSubmit={handleSave} noValidate>
        <div className="mb-4">
          <label htmlFor="new_username" className="block text-[15px] font-medium text-slate mb-2">
            Новый логин
          </label>
          <input
            type="text"
            id="new_username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
            placeholder="Ваш логин"
          />
          {username && !isValid && (
            <p className="text-[13px] text-clay mt-[6px]">
              Логин: 3–32 символа, латиница, цифры, _ . -
            </p>
          )}
          {isValid && isTaken && (
            <p className="text-[13px] text-clay mt-[6px]">Этот логин уже занят</p>
          )}
          {isValid && !isTaken && !unchanged && (
            <p className="text-[13px] text-olive mt-[6px]">Логин свободен</p>
          )}
        </div>
        <div className="mb-4">
          <p className="text-[14px] text-body-subtle mb-0">
            Менять логин можно не чаще раза в 5 минут.
          </p>
        </div>

        {updateMe.isError && (
          <p className="text-[14px] text-clay mb-4">{serverError || 'Не удалось сменить логин'}</p>
        )}
        {updateMe.isSuccess && <p className="text-[14px] text-olive mb-4">Логин обновлён</p>}

        <button
          type="submit"
          disabled={!isValid || unchanged || isTaken || updateMe.isPending}
          className="btn-primary btn-sm disabled:opacity-60"
        >
          {updateMe.isPending ? 'Сохраняем…' : 'Сменить логин'}
        </button>
      </form>
    </div>
  );
}

function EmailSection({ me }: { me: NonNullable<ReturnType<typeof useMe>['data']> }) {
  const [newEmail, setNewEmail] = useState('');
  const resend = useResendVerification();
  const change = useRequestEmailChange();
  const cancel = useCancelEmailChange();

  const isVerified = !!me.email_verified_at;
  const pending = me.pending_email;
  const oldConfirmed = !!me.email_change_old_confirmed_at;
  const actionError = resend.error ?? change.error ?? cancel.error;

  const handleRequestChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail.trim()) return;
    change.mutate({ new_email: newEmail.trim() });
  };

  return (
    <div className="rounded-[24px] p-[31px] bg-ivory-elevated">
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-slate mb-1">Адрес электронной почты</h3>
        <p className="text-body-subtle text-[15px] mb-0">Текущий адрес: {me.email}</p>
      </div>

      <div className="mb-4">
        {isVerified ? (
          <span className="inline-flex items-center rounded-full px-3 py-1 text-[13px] font-semibold bg-[#EDF1E5] border border-[#C7D2B0] text-[#4F5C36]">
            Подтверждён
          </span>
        ) : (
          <>
            <span className="inline-flex items-center rounded-full px-3 py-1 text-[13px] font-semibold bg-[#F4EBD7] border border-[#E5D29B] text-[#4A3A12] mb-2">
              Не подтверждён
            </span>
            <div>
              <button
                type="button"
                onClick={() => resend.mutate()}
                disabled={resend.isPending}
                className="btn-ghost btn-sm disabled:opacity-60"
              >
                {resend.isPending ? 'Отправляем…' : 'Отправить письмо повторно'}
              </button>
            </div>
            {resend.isSuccess && (
              <p className="text-[14px] text-olive mt-2 mb-0">
                Письмо отправлено. Проверьте почту и перейдите по ссылке.
              </p>
            )}
          </>
        )}
      </div>

      {pending && (
        <div className="mb-4 rounded-[16px] p-4 bg-ivory border border-border-input">
          {oldConfirmed ? (
            <>
              <p className="text-[14px] text-body mb-2">
                Смена на <span className="font-semibold">{pending}</span> подтверждена на старой
                почте. Откройте письмо, отправленное на новый адрес, чтобы завершить смену.
              </p>
            </>
          ) : (
            <>
              <p className="text-[14px] text-body mb-2">
                Смена адреса на <span className="font-semibold">{pending}</span> ожидает
                подтверждения. Откройте письмо на <span className="font-semibold">{me.email}</span>{' '}
                и подтвердите, что это были вы.
              </p>
            </>
          )}
          <button
            type="button"
            onClick={() => cancel.mutate()}
            disabled={cancel.isPending}
            className="btn-ghost btn-sm disabled:opacity-60"
          >
            {cancel.isPending ? 'Отменяем…' : 'Отменить смену'}
          </button>
        </div>
      )}
      {change.isSuccess && (
        <p className="text-[14px] text-olive mb-4">
          Мы отправили письмо с подтверждением на текущий адрес. Подтвердите, что это были вы, —
          затем подтвердите смену на новом адресе.
        </p>
      )}

      {actionError && (
        <p className="text-[14px] text-clay mb-4">
          {apiMessage(actionError, 'Не удалось выполнить операцию с почтой')}
        </p>
      )}

      <form onSubmit={handleRequestChange} noValidate className="flex items-end gap-3 flex-wrap">
        <div className="flex-1 min-w-[240px]">
          <label htmlFor="new_email" className="block text-[15px] font-medium text-slate mb-2">
            Новый адрес
          </label>
          <input
            type="email"
            id="new_email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
            placeholder="new@example.com"
          />
        </div>
        <button
          type="submit"
          disabled={change.isPending || !newEmail.trim()}
          className="btn-primary btn-sm disabled:opacity-60"
        >
          {change.isPending ? 'Отправляем…' : 'Отправить письмо на новый адрес'}
        </button>
      </form>
    </div>
  );
}

function apiMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message: unknown }).message);
    }
  }
  return fallback;
}

function SettingsContent() {
  const { data: me } = useMe();
  const updateMe = useUpdateMe();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<UserUpdateRequest>({
    resolver: zodResolver(userUpdateRequestSchema),
  });

  useEffect(() => {
    if (me) {
      reset({
        full_name: me.full_name,
        phone: me.phone ?? '',
        company: me.company ?? '',
      });
    }
  }, [me, reset]);

  const onSubmit = (data: UserUpdateRequest) => {
    updateMe.mutate(data, {
      onSuccess: () => reset(data),
    });
  };

  return (
    <>
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main>
            <div className="mb-12 max-w-[560px]">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Настройки</h2>
              <div className="space-y-6">
                <form
                  onSubmit={handleSubmit(onSubmit)}
                  noValidate
                  className="rounded-[24px] p-[31px] bg-ivory-elevated"
                >
                  <div className="mb-4">
                    <label
                      htmlFor="full_name"
                      className="block text-[15px] font-medium text-slate mb-2"
                    >
                      Имя и фамилия
                    </label>
                    <input
                      type="text"
                      id="full_name"
                      {...register('full_name')}
                      className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
                      placeholder="Имя и фамилия"
                    />
                    {errors.full_name && (
                      <p className="text-[13px] text-clay mt-[6px]">Укажите имя и фамилию</p>
                    )}
                  </div>
                  <div className="mb-4">
                    <label
                      htmlFor="phone"
                      className="block text-[15px] font-medium text-slate mb-2"
                    >
                      Телефон
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      {...register('phone')}
                      className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
                      placeholder="+7 (999) 123-45-67"
                    />
                    {errors.phone && (
                      <p className="text-[13px] text-clay mt-[6px]">Слишком длинный номер</p>
                    )}
                  </div>
                  <div className="mb-6">
                    <label
                      htmlFor="company"
                      className="block text-[15px] font-medium text-slate mb-2"
                    >
                      Название сервисного центра
                    </label>
                    <input
                      type="text"
                      id="company"
                      {...register('company')}
                      className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
                      placeholder="Название организации"
                    />
                  </div>

                  {updateMe.isSuccess && !isDirty && (
                    <p className="text-[14px] text-olive mb-4">Изменения сохранены</p>
                  )}
                  {updateMe.isError && (
                    <p className="text-[14px] text-clay mb-4">Не удалось сохранить изменения</p>
                  )}

                  <button
                    type="submit"
                    disabled={updateMe.isPending || !isDirty}
                    className="btn-primary btn-sm disabled:opacity-60"
                  >
                    {updateMe.isPending ? 'Сохраняем…' : 'Сохранить'}
                  </button>
                </form>

                {me && <EmailSection me={me} />}
                {me && <LoginSection me={me} />}
              </div>
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}

export default function AccountSettingsPage() {
  return (
    <>
      <Header />
      <RequireAuth>
        <SettingsContent />
      </RequireAuth>
    </>
  );
}
