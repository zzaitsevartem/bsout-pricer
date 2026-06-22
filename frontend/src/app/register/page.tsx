'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';

export default function RegisterPage() {
  return (
    <>
      <Header navCta="login" />
      <div className="flex items-center justify-center min-h-screen px-6 py-12">
        <div className="w-full max-w-[440px] bg-ivory border border-slate rounded-[24px] p-12 max-md:p-8">
          <h1 className="text-[32px] font-bold text-slate mb-2">Регистрация</h1>
          <p className="text-lg text-body mb-8">Создайте аккаунт и получите 10 дней бесплатного доступа</p>

          <form>
            <div className="mb-4">
              <label htmlFor="name" className="block text-[15px] font-medium text-slate mb-2">Имя и фамилия</label>
              <input type="text" id="name" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Иван Петров" />
            </div>
            <div className="mb-4">
              <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">Email</label>
              <input type="email" id="email" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="example@email.com" />
              <p className="text-[14px] text-body-subtle mt-[6px]">На этот адрес придёт подтверждение</p>
            </div>
            <div className="mb-4">
              <label htmlFor="phone" className="block text-[15px] font-medium text-slate mb-2">Телефон</label>
              <input type="tel" id="phone" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="+7 (999) 123-45-67" />
            </div>
            <div className="mb-4">
              <label htmlFor="company" className="block text-[15px] font-medium text-slate mb-2">Название сервисного центра (необязательно)</label>
              <input type="text" id="company" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="ИП Иванов" />
            </div>
            <div className="mb-4">
              <label htmlFor="password" className="block text-[15px] font-medium text-slate mb-2">Пароль</label>
              <input type="password" id="password" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Не менее 8 символов" />
            </div>
            <div className="mb-4">
              <label htmlFor="password2" className="block text-[15px] font-medium text-slate mb-2">Подтвердите пароль</label>
              <input type="password" id="password2" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Введите пароль ещё раз" />
            </div>

            <div className="mb-6">
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="hidden" />
                <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0">
                  <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden">
                    <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
                <span className="text-[14px] text-body">Я принимаю <a href="#" className="text-slate">условия использования</a> и <a href="#" className="text-slate">политику конфиденциальности</a></span>
              </label>
            </div>

            <button type="submit" className="btn-primary w-full justify-center">Создать аккаунт</button>
          </form>

          <p className="text-center text-[14px] text-body-muted mt-6">
            Уже есть аккаунт? <Link href="/login" className="text-slate font-medium no-underline hover:underline">Войти</Link>
          </p>
        </div>
      </div>
    </>
  );
}
