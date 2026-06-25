'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Header } from '../../widgets/Header/ui/Header';

export default function LoginPage() {
  return (
    <>
      <Header navCta="register" />
      <div className="flex min-h-[calc(100vh-64px)]">
        <div className="flex-1 bg-[url('/auth.webp')] bg-cover bg-center border-r border-border-light max-md:hidden" />
        <div className="flex-1 flex items-center justify-center px-10 py-12 bg-ivory max-md:flex-none max-md:w-full max-md:px-5">
          <div className="w-full max-w-[480px] bg-ivory border border-border-light rounded-[24px] p-12 max-md:p-8">
            <h1 className="text-[32px] font-bold text-slate mb-2">Вход</h1>
            <p className="text-lg text-body mb-8">Войдите в аккаунт для доступа к поиску</p>

            <form>
              <div className="mb-4">
                <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">Email</label>
                <input type="email" id="email" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="example@email.com" />
              </div>
              <div className="mb-4">
                <label htmlFor="password" className="block text-[15px] font-medium text-slate mb-2">Пароль</label>
                <input type="password" id="password" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Введите пароль" />
              </div>

              <div className="flex justify-between items-center mb-6">
                <label className="inline-flex items-center gap-2 cursor-pointer text-[15px] text-slate">
                  <input type="checkbox" className="hidden peer" />
                  <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0 peer-checked:bg-slate peer-checked:border-slate transition-colors">
                    <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden peer-checked:block">
                      <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                  Запомнить меня
                </label>
                <a href="#" className="text-[14px] text-body-subtle no-underline hover:text-slate">Забыли пароль?</a>
              </div>

              <button type="submit" className="btn-primary w-full justify-center">Войти</button>
            </form>

            <div className="text-center text-body-muted text-[14px] my-6 relative before:absolute before:top-1/2 before:left-0 before:w-[calc(50%-24px)] before:h-px before:bg-border-light after:absolute after:top-1/2 after:right-0 after:w-[calc(50%-24px)] after:h-px after:bg-border-light">
              или
            </div>

            <div className="flex gap-3">
              <button className="btn-secondary w-full justify-center">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M12 9v6"/><path d="M9 12h6"/></svg>
                ВКонтакте
              </button>
              <button className="btn-secondary w-full justify-center">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"/></svg>
                Телеграм
              </button>
            </div>

            <p className="text-center text-[14px] text-body-muted mt-6">
              Нет аккаунта? <Link href="/register" className="text-slate font-medium no-underline hover:underline">Зарегистрироваться</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
