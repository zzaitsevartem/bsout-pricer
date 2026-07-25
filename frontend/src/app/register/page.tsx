'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Header } from '@/widgets/Header/ui/Header';
import { registerRequestSchema, useRegister } from '@/models/auth';
import { usePlans } from '@/models/payment';

function formatDays(days: number): string {
  const tail = days % 10;
  const teen = days % 100;
  if (teen >= 11 && teen <= 14) {
    return `${days} дней`;
  }
  if (tail === 1) {
    return `${days} день`;
  }
  if (tail >= 2 && tail <= 4) {
    return `${days} дня`;
  }
  return `${days} дней`;
}

const registerFormSchema = registerRequestSchema
  .extend({
    confirmPassword: z.string(),
    terms: z.literal(true),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  });

type RegisterFormValues = z.infer<typeof registerFormSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const registerMutation = useRegister();
  const plans = usePlans();
  const trialDays = plans.data?.find((plan) => plan.plan === 'trial')?.durationDays ?? 7;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerFormSchema),
  });

  const onSubmit = (data: RegisterFormValues) => {
    registerMutation.mutate(
      {
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        phone: data.phone || undefined,
        company: data.company || undefined,
      },
      {
        onSuccess: () => router.push('/account'),
      },
    );
  };

  return (
    <>
      <Header />
      <div className="flex min-h-[calc(100vh-64px)]">
        <div className="flex-1 bg-[url('/auth.webp')] bg-cover bg-center border-r border-border-light max-md:hidden" />
        <div className="flex-1 flex items-center justify-center px-10 py-12 bg-ivory max-md:flex-none max-md:w-full max-md:px-5">
          <div className="w-full max-w-[480px] bg-ivory border border-border-light rounded-[24px] p-12 max-md:p-8">
            <h1 className="text-[32px] font-bold text-slate mb-2">Регистрация</h1>
            <p className="text-lg text-body mb-8">Создайте аккаунт и получите {formatDays(trialDays)} бесплатного доступа</p>

            <form onSubmit={handleSubmit(onSubmit)} noValidate>
              <div className="mb-4">
                <label htmlFor="full_name" className="block text-[15px] font-medium text-slate mb-2">Имя и фамилия</label>
                <input type="text" id="full_name" {...register('full_name')} className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Иван Петров" />
                {errors.full_name && <p className="text-[13px] text-clay mt-[6px]">Укажите имя и фамилию</p>}
              </div>
              <div className="mb-4">
                <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">Email</label>
                <input type="email" id="email" {...register('email')} className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="example@email.com" />
                {errors.email ? (
                  <p className="text-[13px] text-clay mt-[6px]">Введите корректный email</p>
                ) : (
                  <p className="text-[14px] text-body-subtle mt-[6px]">На этот адрес придёт подтверждение</p>
                )}
              </div>
              <div className="mb-4">
                <label htmlFor="phone" className="block text-[15px] font-medium text-slate mb-2">Телефон</label>
                <input type="tel" id="phone" {...register('phone')} className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="+7 (999) 123-45-67" />
                {errors.phone && <p className="text-[13px] text-clay mt-[6px]">Слишком длинный номер</p>}
              </div>
              <div className="mb-4">
                <label htmlFor="company" className="block text-[15px] font-medium text-slate mb-2">Название сервисного центра (необязательно)</label>
                <input type="text" id="company" {...register('company')} className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="ИП Иванов" />
              </div>
              <div className="mb-4">
                <label htmlFor="password" className="block text-[15px] font-medium text-slate mb-2">Пароль</label>
                <input type="password" id="password" {...register('password')} className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Не менее 6 символов" />
                {errors.password && <p className="text-[13px] text-clay mt-[6px]">Пароль должен быть не короче 6 символов</p>}
              </div>
              <div className="mb-4">
                <label htmlFor="confirmPassword" className="block text-[15px] font-medium text-slate mb-2">Подтвердите пароль</label>
                <input type="password" id="confirmPassword" {...register('confirmPassword')} className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Введите пароль ещё раз" />
                {errors.confirmPassword && <p className="text-[13px] text-clay mt-[6px]">{errors.confirmPassword.message}</p>}
              </div>

              <div className="mb-6">
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" {...register('terms')} className="hidden peer" />
                  <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0 peer-checked:bg-slate peer-checked:border-slate transition-colors">
                    <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden peer-checked:block">
                      <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                  <span className="text-[14px] text-body">Я принимаю <a href="#" className="text-slate">условия использования</a> и <a href="#" className="text-slate">политику конфиденциальности</a></span>
                </label>
                {errors.terms && <p className="text-[13px] text-clay mt-[6px]">Необходимо принять условия</p>}
              </div>

              {registerMutation.isError && (
                <p className="text-[14px] text-clay mb-4">Не удалось зарегистрироваться. Возможно, email уже занят.</p>
              )}

              <button type="submit" disabled={registerMutation.isPending} className="btn-primary w-full justify-center disabled:opacity-60">
                {registerMutation.isPending ? 'Создаём…' : 'Создать аккаунт'}
              </button>
            </form>

            <p className="text-center text-[14px] text-body-muted mt-6">
              Уже есть аккаунт? <Link href="/login" className="text-slate font-medium no-underline hover:underline">Войти</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
