'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useSearchHistory, useClearSearchHistory } from '@/models/search';
import { formatDate } from '@/shared/lib/format';

function HistoryContent() {
  const history = useSearchHistory();
  const clearHistory = useClearSearchHistory();
  const [confirmOpen, setConfirmOpen] = useState(false);

  return (
    <>
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main>
            <div className="mb-12">
              <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
                <h2 className="text-[40px] font-semibold text-slate">История поиска</h2>
                <button
                  type="button"
                  className="btn-secondary btn-sm border-border-input disabled:opacity-40 disabled:cursor-not-allowed"
                  disabled={!history.data?.length || history.isLoading || history.isError}
                  onClick={() => {
                    clearHistory.reset();
                    setConfirmOpen(true);
                  }}
                >
                  Очистить всю историю
                </button>
              </div>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {history.isLoading ? (
                  <div className="px-6 py-4 text-body-subtle">Загрузка…</div>
                ) : history.isError ? (
                  <div className="px-6 py-4 text-body-subtle">Не удалось загрузить историю</div>
                ) : history.data && history.data.length > 0 ? (
                  history.data.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center gap-4 px-6 py-4 border-b border-border-light-subtle last:border-b-0"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-[15px] font-medium text-slate">{item.query}</div>
                        <div className="text-[14px] text-body-subtle">
                          {item.results_count} результатов · {formatDate(item.created_at)}
                        </div>
                      </div>
                      <Link
                        href={`/search?q=${encodeURIComponent(item.query)}`}
                        className="btn-arrow flex-shrink-0"
                      >
                        Повторить
                      </Link>
                    </div>
                  ))
                ) : (
                  <div className="px-6 py-4 text-body-subtle">История поиска пуста</div>
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
      {confirmOpen && (
        <ClearHistoryDialog
          pending={clearHistory.isPending}
          error={clearHistory.isError}
          onCancel={() => setConfirmOpen(false)}
          onConfirm={() =>
            clearHistory.mutate(undefined, { onSuccess: () => setConfirmOpen(false) })
          }
        />
      )}
      <Footer />
    </>
  );
}

function ClearHistoryDialog({
  pending,
  error,
  onCancel,
  onConfirm,
}: {
  pending: boolean;
  error: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = dialog.current;
    modal?.showModal();
    cancel.current?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      modal?.close();
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, []);

  return (
    <dialog
      ref={dialog}
      aria-labelledby="clear-history-title"
      aria-describedby="clear-history-description"
      aria-modal="true"
      onCancel={(event) => {
        event.preventDefault();
        if (!pending) onCancel();
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-[480px] rounded-[24px] border border-border-light-subtle bg-ivory p-6 text-body shadow-lg backdrop:bg-black/30 backdrop:backdrop-blur-sm"
    >
      <h3 id="clear-history-title" className="mb-3 text-2xl font-semibold text-slate">
        Очистить историю поиска?
      </h3>
      <p id="clear-history-description" className="text-[15px] text-body-subtle">
        Все ваши поисковые запросы будут удалены. Отменить это действие нельзя.
      </p>
      {error && (
        <p role="alert" className="mt-4 text-[14px] text-clay">
          Не удалось очистить историю. Попробуйте ещё раз.
        </p>
      )}
      <div className="mt-6 flex justify-end gap-3 flex-wrap">
        <button
          ref={cancel}
          type="button"
          className="btn-secondary btn-sm border-border-input disabled:opacity-50"
          disabled={pending}
          onClick={onCancel}
        >
          Отмена
        </button>
        <button
          type="button"
          className="btn-primary btn-sm disabled:opacity-50"
          disabled={pending}
          onClick={onConfirm}
        >
          {pending ? 'Очищаем…' : 'Да, очистить'}
        </button>
      </div>
    </dialog>
  );
}

export default function AccountHistoryPage() {
  return (
    <>
      <Header />
      <RequireAuth>
        <HistoryContent />
      </RequireAuth>
    </>
  );
}
