'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { feedbackRequestSchema, useSendFeedback, type FeedbackRequest } from '@/models/feedback';

function extractError(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
  }
  return 'Не удалось отправить сообщение. Попробуйте позже.';
}

function FeedbackForm() {
  const sendFeedback = useSendFeedback();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FeedbackRequest>({
    resolver: zodResolver(feedbackRequestSchema),
  });

  if (sendFeedback.isSuccess) {
    return (
      <div className="text-center py-6">
        <h4 className="text-xl font-semibold text-slate mb-2">Сообщение отправлено</h4>
        <p className="text-[15px] text-body mb-0">Спасибо! Мы ответим на указанную почту.</p>
      </div>
    );
  }

  const inputClassName =
    'block w-full rounded-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default';
  const errorClassName = 'text-[13px] text-clay mt-[6px]';

  return (
    <form onSubmit={handleSubmit((data) => sendFeedback.mutate(data))} noValidate>
      <div className="mb-4">
        <label htmlFor="name" className="block text-[15px] font-medium text-slate mb-2">
          Имя
        </label>
        <input
          type="text"
          id="name"
          {...register('name')}
          placeholder="Ваше имя"
          className={inputClassName}
        />
        {errors.name && <p className={errorClassName}>{errors.name.message}</p>}
      </div>
      <div className="mb-4">
        <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">
          Email
        </label>
        <input
          type="email"
          id="email"
          {...register('email')}
          placeholder="your@email.com"
          className={inputClassName}
        />
        {errors.email && <p className={errorClassName}>{errors.email.message}</p>}
      </div>
      <div className="mb-4">
        <label htmlFor="subject" className="block text-[15px] font-medium text-slate mb-2">
          Тема
        </label>
        <input
          type="text"
          id="subject"
          {...register('subject')}
          placeholder="Чем мы можем помочь?"
          className={inputClassName}
        />
        {errors.subject && <p className={errorClassName}>{errors.subject.message}</p>}
      </div>
      <div className="mb-4">
        <label htmlFor="message" className="block text-[15px] font-medium text-slate mb-2">
          Сообщение
        </label>
        <textarea
          id="message"
          rows={5}
          {...register('message')}
          placeholder="Ваше сообщение..."
          className="block w-full rounded-3xl px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default resize-y min-h-[96px]"
        />
        {errors.message && <p className={errorClassName}>{errors.message.message}</p>}
      </div>
      {sendFeedback.isError && (
        <p className="text-[14px] text-clay mb-4">{extractError(sendFeedback.error)}</p>
      )}
      <button
        type="submit"
        disabled={sendFeedback.isPending}
        className="btn-primary w-full justify-center disabled:opacity-60"
      >
        {sendFeedback.isPending ? 'Отправляем…' : 'Отправить'}
      </button>
    </form>
  );
}

export default function ContactsPage() {
  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">
            Главная
          </a>
          <span className="text-body-muted">/</span>
          <span>Контакты</span>
        </div>

        <div className="pb-8 mb-8 border-b-0">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
            Контакты
          </p>
          <h1 className="text-[40px] font-semibold text-slate mb-2">Свяжитесь с нами</h1>
          <p className="text-lg text-body">Есть вопросы или предложения? Напишите нам!</p>
        </div>

        <div className="grid grid-cols-2 gap-12 max-md:grid-cols-1">
          <div>
            {[
              {
                icon: (
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                ),
                title: 'Email',
                lines: ['hello@bscout.ru', 'support@bscout.ru'],
              },
            ].map((item) => (
              <div key={item.title} className="flex gap-4 mb-6">
                <div className="w-10 h-10 rounded-full bg-ivory-elevated flex items-center justify-center flex-shrink-0 text-slate">
                  {item.icon}
                </div>
                <div>
                  <h5 className="text-[18px] font-semibold text-slate mb-1">{item.title}</h5>
                  {item.lines.map((line, i) => (
                    <p key={i} className="text-body-subtle mb-0">
                      {line}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div>
            <div className="rounded-[24px] p-[31px] bg-ivory-elevated">
              <h4 className="text-xl font-semibold text-slate mb-4">Напишите нам</h4>
              <FeedbackForm />
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
