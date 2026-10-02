'use client';

import { useEffect } from 'react';
import Link from 'next/link';

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // В проде сюда должен подключаться мониторинг (Sentry и т.п.) —
    // сейчас ошибка уходит только в консоль браузера.
    console.error(error);
  }, [error]);

  return (
    <main className="bg-ivory">
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">
          Ошибка 500
        </p>
        <h1 className="text-[40px] font-semibold text-slate mb-4 max-md:text-[28px]">
          Что-то пошло не так
        </h1>

        <div className="max-w-[720px]">
          <p className="text-[16px] text-body leading-[1.5] mb-3">
            Страница не отрисовалась из-за ошибки на нашей стороне. Это не связано с вашими
            данными — попробуйте ещё раз.
          </p>
          <p className="text-[15px] text-body-subtle leading-[1.4] mb-8">
            Если ошибка повторяется — сообщите нам, приложив код ниже.
          </p>
        </div>

        {error.digest && (
          <p className="text-[14px] text-body-muted mb-8">
            Код ошибки:{' '}
            <code className="font-mono text-body bg-ivory-elevated border border-border-light-subtle rounded-full px-2 py-[2px]">
              {error.digest}
            </code>
          </p>
        )}

        <div className="flex gap-3 flex-wrap">
          <button type="button" onClick={reset} className="btn btn-primary btn-sm">
            Попробовать снова
          </button>
          <Link href="/search" className="btn btn-secondary btn-sm no-underline">
            К поиску
          </Link>
          <Link href="/contacts" className="btn btn-ghost btn-sm no-underline">
            Написать нам
          </Link>
        </div>
      </div>
    </main>
  );
}
