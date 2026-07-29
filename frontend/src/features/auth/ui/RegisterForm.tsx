'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerRequestSchema, type RegisterRequest } from '@/models/auth/schema';
import { useRegister } from '@/models/auth';
import { userLoggedIn } from '@/models/auth';
import { cn } from '@/shared/lib/utils';
interface RegisterFormProps {
  className?: string;
}

export function RegisterForm({ className }: RegisterFormProps) {
  const router = useRouter();
  const registerMutation = useRegister();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterRequest>({
    resolver: zodResolver(registerRequestSchema),
  });

  const onSubmit = async (data: RegisterRequest) => {
    try {
      await registerMutation.mutateAsync(data);
      userLoggedIn();
      router.push('/');
    } catch (e: unknown) {
      const detail =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setError('root', {
        message: detail || 'Ошибка регистрации. Попробуйте позже.',
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={cn('w-full', className)}>
      <h1 className="text-[32px] font-bold text-slate mb-2">Регистрация</h1>
      <p className="text-lg text-body mb-8">Создайте аккаунт и получите 10 дней бесплатного доступа</p>

      {errors.root && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-[14px]">
          {errors.root.message}
        </div>
      )}

      <div className="mb-4">
        <label htmlFor="full_name" className="block text-[15px] font-medium text-slate mb-2">
          Имя и фамилия
        </label>
        <input
          id="full_name"
          type="text"
          {...register('full_name')}
          className={cn(
            'block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border transition-colors',
            'focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]',
            errors.full_name ? 'border-red-400' : 'border-border-default',
          )}
          placeholder="Иван Петров"
        />
        {errors.full_name && (
          <p className="text-red-500 text-[13px] mt-1">{errors.full_name.message}</p>
        )}
      </div>

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
        <p className="text-[14px] text-body-subtle mt-[6px]">На этот адрес придёт подтверждение</p>
      </div>

      <div className="mb-4">
        <label htmlFor="phone" className="block text-[15px] font-medium text-slate mb-2">
          Телефон
        </label>
        <input
          id="phone"
          type="tel"
          {...register('phone')}
          className={cn(
            'block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border transition-colors',
            'focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]',
            errors.phone ? 'border-red-400' : 'border-border-default',
          )}
          placeholder="+7 (999) 123-45-67"
        />
        {errors.phone && (
          <p className="text-red-500 text-[13px] mt-1">{errors.phone.message}</p>
        )}
      </div>

      <div className="mb-4">
        <label htmlFor="company" className="block text-[15px] font-medium text-slate mb-2">
          Название сервисного центра (необязательно)
        </label>
        <input
          id="company"
          type="text"
          {...register('company')}
          className={cn(
            'block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border transition-colors',
            'focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]',
            errors.company ? 'border-red-400' : 'border-border-default',
          )}
          placeholder="ИП Иванов"
        />
        {errors.company && (
          <p className="text-red-500 text-[13px] mt-1">{errors.company.message}</p>
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
          placeholder="Не менее 6 символов"
        />
        {errors.password && (
          <p className="text-red-500 text-[13px] mt-1">{errors.password.message}</p>
        )}
      </div>

      <div className="mb-6">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input type="checkbox" className="hidden peer" required />
          <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0 peer-checked:bg-slate peer-checked:border-slate transition-colors">
            <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden peer-checked:block">
              <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="text-[14px] text-body">
            Я принимаю <a href="#" className="text-slate">условия использования</a> и{' '}
            <a href="#" className="text-slate">политику конфиденциальности</a>
          </span>
        </label>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="btn-primary w-full justify-center disabled:opacity-50"
      >
        {isSubmitting ? 'Создание...' : 'Создать аккаунт'}
      </button>
    </form>
  );
}
