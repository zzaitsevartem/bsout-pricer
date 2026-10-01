'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useSearchHistory } from '@/models/search';
import { formatDate } from '@/shared/lib/format';

function HistoryContent() {
  const history = useSearchHistory();

  return (
    <>
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main>
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">История поиска</h2>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {history.isLoading ? (
                  <div className="px-6 py-4 text-body-subtle">Загрузка…</div>
                ) : history.isError ? (
                  <div className="px-6 py-4 text-body-subtle">Не удалось загрузить историю</div>
                ) : history.data && history.data.length > 0 ? (
                  history.data.map((item) => (
                    <div key={item.id} className="flex items-center gap-4 px-6 py-4 border-b border-border-light-subtle last:border-b-0">
                      <div className="flex-1 min-w-0">
                        <div className="text-[15px] font-medium text-slate">{item.query}</div>
                        <div className="text-[14px] text-body-subtle">{item.results_count} результатов · {formatDate(item.created_at)}</div>
                      </div>
                      <Link href={`/search?q=${encodeURIComponent(item.query)}`} className="btn-arrow flex-shrink-0">Повторить</Link>
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
      <Footer />
    </>
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
