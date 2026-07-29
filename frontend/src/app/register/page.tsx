'use client';

import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';
import { RegisterForm } from '@/features/auth';

export default function RegisterPage() {
  return (
    <>
      <Header navCta="login" />
      <div className="flex min-h-[calc(100vh-64px)]">
        <div className="flex-1 bg-[url('/auth.webp')] bg-cover bg-center border-r border-border-light max-md:hidden" />
        <div className="flex-1 flex items-center justify-center px-10 py-12 bg-ivory max-md:flex-none max-md:w-full max-md:px-5">
          <div className="w-full max-w-[480px] bg-ivory border border-border-light rounded-[24px] p-12 max-md:p-8">
            <RegisterForm />

            <p className="text-center text-[14px] text-body-muted mt-6">
              Уже есть аккаунт? <Link href="/login" className="text-slate font-medium no-underline hover:underline">Войти</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
