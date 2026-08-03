'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header } from '../../widgets/Header/ui/Header';
import { useRegister } from '../../models/auth/hooks';
import { registerRequestSchema } from '../../models/auth/schema';

export default function RegisterPage() {
  const router = useRouter();
  const registerMutation = useRegister();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [company, setCompany] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (password !== password2) {
      setErrorMessage('Пароли не совпадают');
      return;
    }

    const parsed = registerRequestSchema.safeParse({
      email: email.trim(),
      password,
      full_name: fullName.trim(),
      phone: phone.trim() || undefined,
      company: company.trim() || undefined,
    });

    if (!parsed.success) {
      setErrorMessage('Проверьте правильность заполнения полей');
      return;
    }

    registerMutation.mutate(parsed.data, {
      onSuccess: () => router.push('/'),
      onError: () => {
        setErrorMessage('Не удалось создать аккаунт. Проверьте данные или попробуйте позже.');
      },
    });
  };

  return (
    <>
      <Header navCta="login" />
      <div className="flex min-h-[calc(100vh-64px)]">
        <div className="flex-1 bg-[url('/auth.webp')] bg-cover bg-center border-r border-border-light max-md:hidden" />
        <div className="flex-1 flex items-center justify-center px-10 py-12 bg-ivory max-md:flex-none max-md:w-full max-md:px-5">
          <div className="w-full max-w-[480px] bg-ivory border border-border-light rounded-[24px] p-12 max-md:p-8">
            <h1 className="text-[32px] font-bold text-slate mb-2">Регистрация</h1>
            <p className="text-lg text-body mb-8">Создайте аккаунт и получите 10 дней бесплатного доступа</p>

            <form onSubmit={handleSubmit} noValidate>
              <div className="mb-4">
                <label htmlFor="name" className="block text-[15px] font-medium text-slate mb-2">Имя и фамилия</label>
                <input
                  type="text"
                  id="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413] placeholder:text-body-muted"
                  placeholder="Иван Петров"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">Email</label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413] placeholder:text-body-muted"
                  placeholder="example@email.com"
                />
                <p className="text-[14px] text-body-subtle mt-[6px]">На этот адрес придёт подтверждение</p>
              </div>
              <div className="mb-4">
                <label htmlFor="phone" className="block text-[15px] font-medium text-slate mb-2">Телефон</label>
                <input
                  type="tel"
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413] placeholder:text-body-muted"
                  placeholder="+7 (999) 123-45-67"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="company" className="block text-[15px] font-medium text-slate mb-2">Название сервисного центра (необязательно)</label>
                <input
                  type="text"
                  id="company"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413] placeholder:text-body-muted"
                  placeholder="ИП Иванов"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="password" className="block text-[15px] font-medium text-slate mb-2">Пароль</label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413] placeholder:text-body-muted"
                  placeholder="Не менее 6 символов"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="password2" className="block text-[15px] font-medium text-slate mb-2">Подтвердите пароль</label>
                <input
                  type="password"
                  id="password2"
                  value={password2}
                  onChange={(e) => setPassword2(e.target.value)}
                  className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413] placeholder:text-body-muted"
                  placeholder="Введите пароль ещё раз"
                />
              </div>

              {errorMessage && (
                <div className="mb-6 text-[14px] text-center text-[#C6613F]">{errorMessage}</div>
              )}

              <div className="mb-6">
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="hidden peer" />
                  <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0 peer-checked:bg-slate peer-checked:border-slate transition-colors">
                    <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden peer-checked:block">
                      <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                  <span className="text-[14px] text-body">Я принимаю <a href="#" className="text-slate">условия использования</a> и <a href="#" className="text-slate">политику конфиденциальности</a></span>
                </label>
              </div>

              <button
                type="submit"
                disabled={registerMutation.isPending}
                className="btn-primary w-full justify-center disabled:opacity-50 disabled:pointer-events-none"
              >
                {registerMutation.isPending ? 'Создаём аккаунт...' : 'Создать аккаунт'}
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
