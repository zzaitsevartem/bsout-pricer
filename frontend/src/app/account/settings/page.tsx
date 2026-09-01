'use client';

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useMe, useUpdateMe, userUpdateRequestSchema, type UserUpdateRequest } from '@/models/user';

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

              <form onSubmit={handleSubmit(onSubmit)} noValidate className="rounded-[24px] p-[31px] bg-ivory-elevated">
                <div className="mb-4">
                  <label htmlFor="full_name" className="block text-[15px] font-medium text-slate mb-2">Имя и фамилия</label>
                  <input type="text" id="full_name" {...register('full_name')} className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Иван Петров" />
                  {errors.full_name && <p className="text-[13px] text-clay mt-[6px]">Укажите имя и фамилию</p>}
                </div>
                <div className="mb-4">
                  <label htmlFor="phone" className="block text-[15px] font-medium text-slate mb-2">Телефон</label>
                  <input type="tel" id="phone" {...register('phone')} className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="+7 (999) 123-45-67" />
                  {errors.phone && <p className="text-[13px] text-clay mt-[6px]">Слишком длинный номер</p>}
                </div>
                <div className="mb-6">
                  <label htmlFor="company" className="block text-[15px] font-medium text-slate mb-2">Название сервисного центра</label>
                  <input type="text" id="company" {...register('company')} className="block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="ИП Иванов" />
                </div>

                {updateMe.isSuccess && !isDirty && (
                  <p className="text-[14px] text-olive mb-4">Изменения сохранены</p>
                )}
                {updateMe.isError && (
                  <p className="text-[14px] text-clay mb-4">Не удалось сохранить изменения</p>
                )}

                <button type="submit" disabled={updateMe.isPending || !isDirty} className="btn-primary btn-sm disabled:opacity-60">
                  {updateMe.isPending ? 'Сохраняем…' : 'Сохранить'}
                </button>
              </form>
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
