'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useMe, useSubscription } from '@/models/user';
import { useSearchHistory } from '@/models/search';
import { formatDate, initials, planLabel } from '@/shared/lib/format';

function AccountContent() {
  const { data: me, isLoading: meLoading } = useMe();
  const subscription = useSubscription();
  const history = useSearchHistory();

  return (
    <>
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main>
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Профиль</h2>
              <div className="flex gap-6 p-6 bg-ivory-elevated rounded-[24px] items-center flex-wrap">
                {meLoading || !me ? (
                  <p className="text-body-subtle">Загрузка профиля…</p>
                ) : (
                  <>
                    <div className="w-16 h-16 rounded-full bg-ivory-warm flex items-center justify-center text-2xl font-bold text-slate">{initials(me.full_name)}</div>
                    <div>
                      <h3 className="text-xl font-semibold text-slate mb-1">{me.full_name}</h3>
                      <p className="text-body-subtle mb-0">{me.email}{me.phone ? ` · ${me.phone}` : ''}</p>
                      {me.username && <p className="text-[14px] text-body-subtle mt-1">Логин: {me.username}</p>}
                      {me.company && <p className="text-[14px] text-body-subtle mt-1">{me.company}</p>}
                    </div>
                    <Link href="/account/settings" className="btn-secondary btn-sm ml-auto">Редактировать</Link>
                  </>
                )}
              </div>
            </div>

            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Текущий тариф</h2>
              <div className="rounded-[24px] pt-[20px] px-[31px] pb-[31px] bg-ivory-elevated flex justify-between items-center flex-wrap gap-4">
                {subscription.isLoading ? (
                  <p className="text-body-subtle mb-0">Загрузка…</p>
                ) : subscription.data ? (
                  <>
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="inline-flex items-center rounded-full px-4 py-[6px] text-[14px] font-semibold bg-green-discount text-white border border-transparent">{planLabel(subscription.data.plan)}</span>
                        <span className="text-[12px] text-body-muted">Активна до {formatDate(subscription.data.end_date)}</span>
                      </div>
                      <p className="text-[15px] text-body-subtle mt-2 mb-0">{subscription.data.auto_renew ? 'Автопродление включено' : 'Автопродление выключено'}</p>
                    </div>
                    <Link href="/subscription" className="btn-secondary btn-sm">Управлять</Link>
                  </>
                ) : (
                  <>
                    <div>
                      <p className="text-[15px] text-body-subtle mb-0">У вас нет активной подписки</p>
                    </div>
                    <Link href="/tariffs" className="btn-primary btn-sm">Выбрать тариф</Link>
                  </>
                )}
              </div>
            </div>

            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">История поиска</h2>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {history.isLoading ? (
                  <div className="px-6 py-4 text-body-subtle">Загрузка…</div>
                ) : history.data && history.data.length > 0 ? (
                  history.data.slice(0, 5).map((item) => (
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

export default function AccountPage() {
  return (
    <>
      <Header />
      <RequireAuth>
        <AccountContent />
      </RequireAuth>
    </>
  );
}
