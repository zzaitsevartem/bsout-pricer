'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginRequestSchema, type LoginRequest } from '@/models/auth/schema';
import { useLogin } from '@/models/auth';
import { userLoggedIn } from '@/models/auth';
import { cn } from '@/shared/lib/utils';
interface LoginFormProps {
  className?: string;
}

export function LoginForm({ className }: LoginFormProps) {
  const router = useRouter();
  const loginMutation = useLogin();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginRequest>({
    resolver: zodResolver(loginRequestSchema),
  });

  const onSubmit = async (data: LoginRequest) => {
    try {
      await loginMutation.mutateAsync(data);
      userLoggedIn();
      router.push('/');
    } catch (e: unknown) {
      const detail =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setError('root', {
        message: detail || 'Неверный email или пароль',
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={cn('w-full', className)}>
      <h1 className="text-[32px] font-bold text-slate mb-2">Вход</h1>
      <p className="text-lg text-body mb-8">Войдите в аккаунт для доступа к поиску</p>

      {errors.root && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-[14px]">
          {errors.root.message}
        </div>
      )}

      <div className="mb-4">
        <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">
          Email
        </label>
        <input
          id="email"
          type="email"
          {...register('email')}
          className={cn(
            'block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border transition-colors',
            'focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]',
            errors.email ? 'border-red-400' : 'border-border-default',
          )}
          placeholder="example@email.com"
        />
        {errors.email && (
          <p className="text-red-500 text-[13px] mt-1">{errors.email.message}</p>
        )}
      </div>

      <div className="mb-4">
        <label htmlFor="password" className="block text-[15px] font-medium text-slate mb-2">
          Пароль
        </label>
        <input
          id="password"
          type="password"
          {...register('password')}
          className={cn(
            'block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border transition-colors',
            'focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]',
            errors.password ? 'border-red-400' : 'border-border-default',
          )}
          placeholder="Введите пароль"
        />
        {errors.password && (
          <p className="text-red-500 text-[13px] mt-1">{errors.password.message}</p>
        )}
      </div>

      <div className="flex justify-between items-center mb-6">
        <label className="inline-flex items-center gap-2 cursor-pointer text-[15px] text-slate">
          <input type="checkbox" className="hidden peer" />
          <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0 peer-checked:bg-slate peer-checked:border-slate transition-colors">
            <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden peer-checked:block">
              <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          Запомнить меня
        </label>
        <a href="#" className="text-[14px] text-body-subtle no-underline hover:text-slate">
          Забыли пароль?
        </a>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="btn-primary w-full justify-center disabled:opacity-50"
      >
        {isSubmitting ? 'Вход...' : 'Войти'}
      </button>
    </form>
  );
}
