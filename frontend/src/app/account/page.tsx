'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useUnit } from 'effector-react';
import { $isAuth } from '../../models/auth/store';
import { useMe, useUpdateMe, useSubscription } from '../../models/user';
import { usePlans } from '../../models/plan';
import { ProtectedRoute } from '../../shared/ui/ProtectedRoute';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

const profileFormSchema = z.object({
  full_name: z.string().min(1, 'Имя обязательно').max(255),
  phone: z.string().max(20).optional().or(z.literal('')),
  company: z.string().max(255).optional().or(z.literal('')),
});

type ProfileFormData = z.infer<typeof profileFormSchema>;

const planNameMap: Record<string, string> = {
  trial: 'Пробный',
  basic: 'Базовый',
  advanced: 'Продвинутый',
};

function AccountContent() {
  const isAuth = useUnit($isAuth);
  const [editing, setEditing] = useState(false);
  const { data: user, isLoading: userLoading } = useMe({ enabled: isAuth });
  const { data: subscription } = useSubscription({ enabled: isAuth });
  const { data: plans } = usePlans();
  const updateMe = useUpdateMe();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileFormSchema),
    values: {
      full_name: user?.full_name ?? '',
      phone: user?.phone ?? '',
      company: user?.company ?? '',
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        full_name: user.full_name,
        phone: user.phone ?? '',
        company: user.company ?? '',
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: ProfileFormData) => {
    try {
      await updateMe.mutateAsync({
        full_name: data.full_name,
        phone: data.phone || undefined,
        company: data.company || undefined,
      });
      setEditing(false);
    } catch {
      // error handled by tanstack query
    }
  };

  const currentPlanSlug = subscription?.is_active ? subscription.plan : null;
  const planInfo = currentPlanSlug
    ? plans?.find((p) => p.slug === currentPlanSlug)
    : null;

  if (userLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-body-muted text-sm">Загрузка профиля…</div>
      </div>
    );
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map((s) => s[0]).join('').slice(0, 2).toUpperCase()
    : '??';

  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <aside className="sticky top-20 self-start max-md:hidden">
            <div className="border-r-0 w-full">
              <div className="p-0">
                <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-4">Аккаунт</div>
                <a href="/account" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline bg-ivory-elevated font-medium border-l-2 border-slate transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  Профиль
                </a>
                <a href="/subscription" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M12 9v6"/><path d="M9 12h6"/></svg>
                  Подписка
                </a>
                <a href="/account/history" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  История поиска
                </a>
                <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-6">Настройки</div>
                <a href="/account/settings" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                  Настройки
                </a>
              </div>
            </div>
          </aside>

          <main>
            {/* Profile section */}
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Профиль</h2>

              <div className="rounded-[24px] p-6 bg-ivory-elevated">
                <div className="flex gap-6 items-start flex-wrap">
                  <div className="w-16 h-16 bg-ivory-warm flex items-center justify-center text-2xl font-bold text-slate flex-shrink-0">
                    {initials}
                  </div>

                  {!editing ? (
                    <>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-semibold text-slate mb-1">{user?.full_name}</h3>
                        <p className="text-body-subtle mb-0">
                          {user?.email}{user?.phone ? ` · ${user.phone}` : ''}
                        </p>
                        {user?.company && (
                          <p className="text-[14px] text-body-subtle mt-1">{user.company}</p>
                        )}
                      </div>
                      <button
                        onClick={() => setEditing(true)}
                        className="btn-secondary btn-sm ml-auto"
                      >
                        Редактировать
                      </button>
                    </>
                  ) : (
                    <form onSubmit={handleSubmit(onSubmit)} className="flex-1 w-full">
                      <div className="grid gap-4 max-w-md">
                        <div>
                          <label className="block text-[13px] font-medium text-body-muted mb-1">Имя</label>
                          <input
                            {...register('full_name')}
                            className="w-full px-3 py-2 border border-border-light rounded-lg text-[15px] bg-white text-slate focus:outline-none focus:ring-2 focus:ring-slate/20"
                          />
                          {errors.full_name && (
                            <p className="text-[13px] text-red-500 mt-1">{errors.full_name.message}</p>
                          )}
                        </div>

                        <div>
                          <label className="block text-[13px] font-medium text-body-muted mb-1">Email</label>
                          <input
                            value={user?.email ?? ''}
                            disabled
                            className="w-full px-3 py-2 border border-border-light rounded-lg text-[15px] bg-ivory text-body-muted cursor-not-allowed"
                          />
                          <p className="text-[12px] text-body-muted mt-1">Email нельзя изменить</p>
                        </div>

                        <div>
                          <label className="block text-[13px] font-medium text-body-muted mb-1">Телефон</label>
                          <input
                            {...register('phone')}
                            placeholder="+7 (999) 123-45-67"
                            className="w-full px-3 py-2 border border-border-light rounded-lg text-[15px] bg-white text-slate focus:outline-none focus:ring-2 focus:ring-slate/20"
                          />
                        </div>

                        <div>
                          <label className="block text-[13px] font-medium text-body-muted mb-1">Компания</label>
                          <input
                            {...register('company')}
                            placeholder="Название организации"
                            className="w-full px-3 py-2 border border-border-light rounded-lg text-[15px] bg-white text-slate focus:outline-none focus:ring-2 focus:ring-slate/20"
                          />
                        </div>

                        <div className="flex gap-3 mt-2">
                          <button
                            type="submit"
                            disabled={isSubmitting}
                            className="btn-primary btn-sm"
                          >
                            {isSubmitting ? 'Сохранение…' : 'Сохранить'}
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditing(false)}
                            className="btn-ghost btn-sm"
                          >
                            Отмена
                          </button>
                        </div>

                        {updateMe.isError && (
                          <p className="text-[13px] text-red-500">Ошибка при сохранении</p>
                        )}
                        {updateMe.isSuccess && !isSubmitting && (
                          <p className="text-[13px] text-green-discount">Профиль обновлён</p>
                        )}
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </div>

            {/* Current tariff */}
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Текущий тариф</h2>
              <div className="rounded-[24px] p-[31px] bg-ivory-elevated flex justify-between items-center flex-wrap gap-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="inline-flex items-center px-4 py-[6px] text-[14px] font-semibold bg-ivory-elevated text-slate border border-slate">
                      {currentPlanSlug ? (planNameMap[currentPlanSlug] ?? currentPlanSlug) : 'Нет тарифа'}
                    </span>
                    {subscription && (
                      <span className="text-[12px] text-body-muted">
                        {subscription.is_active ? 'Активен' : 'Неактивен'}
                        {subscription.end_date && ` до ${new Date(subscription.end_date).toLocaleDateString('ru-RU')}`}
                      </span>
                    )}
                  </div>
                  {planInfo && (
                    <p className="text-[15px] text-body-subtle mb-0">
                      {planInfo.price} ₽ {planInfo.period}
                      {planInfo.features.length > 0 && ` · ${planInfo.features.slice(0, 3).join(' · ')}`}
                    </p>
                  )}
                </div>
                <Link href="/subscription" className="btn-secondary btn-sm">
                  Управлять
                </Link>
              </div>
            </div>

            {/* Search history — mock */}
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">История поиска</h2>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {[
                  { query: 'Дисплей iPhone 13', results: '24 результата', date: '12.06.2026' },
                  { query: 'Аккумулятор Samsung Galaxy S23', results: '18 результатов', date: '10.06.2026' },
                  { query: 'Материнская плата Xiaomi Redmi Note 12', results: '7 результатов', date: '08.06.2026' },
                ].map((item) => (
                  <div key={item.query} className="flex items-center gap-4 px-6 py-4 border-b border-border-light-subtle last:border-b-0">
                    <div className="flex-1 min-w-0">
                      <div className="text-[15px] font-medium text-slate">{item.query}</div>
                      <div className="text-[14px] text-body-subtle">{item.results} · {item.date}</div>
                    </div>
                    <a href={`/search?q=${encodeURIComponent(item.query)}`} className="btn-arrow flex-shrink-0">Повторить</a>
                  </div>
                ))}
              </div>
            </div>

            {/* Recently viewed — mock */}
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Недавно просмотренные</h2>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {[
                  { name: 'Дисплей iPhone 13 Pro Max', price: 'от 6 800 ₽', stores: '3 магазина' },
                  { name: 'Шлейф зарядки Huawei P30', price: 'от 650 ₽', stores: '5 магазинов' },
                ].map((item) => (
                  <div key={item.name} className="flex items-center gap-4 px-6 py-4 border-b border-border-light-subtle last:border-b-0">
                    <div className="w-12 h-12 bg-ivory-warm flex items-center justify-center flex-shrink-0">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[15px] font-medium text-slate">{item.name}</div>
                      <div className="text-[14px] text-body-subtle">{item.price} · {item.stores}</div>
                    </div>
                    <a href="/product" className="btn-arrow flex-shrink-0">Открыть</a>
                  </div>
                ))}
              </div>
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}

export default function AccountPage() {
  return (
    <ProtectedRoute>
      <AccountContent />
    </ProtectedRoute>
  );
}
