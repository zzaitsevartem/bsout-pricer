'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useTrialSearch, useTrialStatus } from '@/models/trial/hooks';

const TrialPopup: React.FC = () => {
  const { data: status } = useTrialStatus();
  const searchMutation = useTrialSearch();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isRegistered =
    typeof window !== 'undefined' ? !!window.localStorage.getItem('access_token') : false;
  const trialUsed = status ? !status.available : false;
  const showPrompt = trialUsed || lastQuery !== null;

  useEffect(() => {
    if (isRegistered) return;
    if (status === undefined) return;
    const timer = window.setTimeout(() => {
      if (!window.localStorage.getItem('access_token')) {
        setIsOpen(true);
      }
    }, 5000);
    return () => window.clearTimeout(timer);
  }, [isRegistered, status]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : 'unset';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    if (isOpen) window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    setErrorMessage(null);
    searchMutation.mutate(trimmed, {
      onSuccess: () => setLastQuery(trimmed),
      onError: () => {
        setErrorMessage('Не получилось выполнить поиск. Попробуйте ещё раз.');
      },
    });
  };

  if (!isOpen || isRegistered) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate/40 backdrop-blur-sm animate-trial-fade-in"
        onClick={handleClose}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Пробный поиск"
        className="relative w-full max-w-md bg-ivory rounded-[24px] border border-border-light-subtle shadow-2xl animate-trial-pop overflow-hidden"
      >
        <div className="h-1.5 bg-gradient-to-r from-[#C6993F] via-[#E3B45F] to-[#C6993F]" />

        <button
          type="button"
          onClick={handleClose}
          aria-label="Закрыть окно"
          className="absolute top-4 right-4 w-9 h-9 flex items-center justify-center text-body-muted bg-transparent border-none cursor-pointer transition-colors hover:text-slate hover:bg-ivory-elevated rounded-full"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>

        <div className="p-8 max-sm:p-6">
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-16 h-16 rounded-full bg-ivory-elevated border border-border-light-subtle flex items-center justify-center mb-5 animate-glow-pulse">
              {showPrompt ? (
                <svg className="w-7 h-7 text-[#C6993F]" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <rect x="4" y="10" width="16" height="11" rx="2" />
                  <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                </svg>
              ) : (
                <svg className="w-7 h-7 text-[#C6993F]" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
              )}
            </div>

            {showPrompt ? (
              <>
                <h3 className="text-[24px] font-bold leading-tight tracking-[-0.01em] text-slate mb-2">
                  Зарегистрируйтесь, чтобы увидеть результат
                </h3>
                <p className="text-[15px] leading-relaxed text-body-subtle max-w-[38ch]">
                  {lastQuery
                    ? 'Вы использовали бесплатный пробный поиск. Создайте аккаунт, чтобы увидеть результаты и продолжить поиск.'
                    : 'Бесплатный пробный поиск уже был использован. Создайте аккаунт, чтобы увидеть результаты и продолжить поиск.'}
                </p>
              </>
            ) : (
              <>
                <h3 className="text-[26px] font-bold leading-tight tracking-[-0.01em] text-slate mb-2">
                  Пробный поиск — бесплатно
                </h3>
                <p className="text-[15px] leading-relaxed text-body-subtle max-w-[38ch]">
                  Проверьте BScout в деле: введите название запчасти и найдите лучшие цены в магазинах Ставрополя.
                </p>
              </>
            )}
          </div>

          {showPrompt ? (
            <div className="flex flex-col gap-3 text-center">
              {lastQuery && (
                <div className="rounded-2xl bg-ivory-elevated border border-border-light-subtle p-5 mb-1">
                  <div className="text-[13px] text-body-muted mb-1">Ваш запрос</div>
                  <div className="text-base font-semibold text-slate break-words">«{lastQuery}»</div>
                </div>
              )}
              <Link href="/register" className="btn-primary justify-center no-underline">
                Зарегистрироваться
              </Link>
              <button type="button" onClick={handleClose} className="btn-ghost justify-center">
                Закрыть
              </button>
              <p className="text-[13px] text-body-muted text-center">
                Уже есть аккаунт?{' '}
                <Link href="/login" className="text-slate font-medium no-underline hover:underline">
                  Войти
                </Link>
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Например: дисплей iPhone 13"
                maxLength={500}
                autoFocus
                className="w-full px-4 py-3 text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate placeholder:text-body-muted"
              />
              {errorMessage && (
                <div className="text-[14px] text-center text-[#C6613F]">{errorMessage}</div>
              )}
              <button
                type="submit"
                disabled={searchMutation.isPending || !query.trim()}
                className="btn-primary justify-center disabled:opacity-50 disabled:pointer-events-none"
              >
                {searchMutation.isPending ? 'Ищем...' : 'Попробовать поиск'}
              </button>
              <p className="text-[13px] text-body-muted text-center">Один пробный поиск на браузер</p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export { TrialPopup };
