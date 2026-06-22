'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

export default function SubscriptionPage() {
  return (
    <>
      <Header navCta="logout" />
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <aside className="sticky top-20 self-start max-md:hidden">
            <div className="border-r-0 w-full">
              <div className="p-0">
                <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-4">Аккаунт</div>
                <a href="/account" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  Профиль
                </a>
                <a href="/subscription" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline bg-ivory-elevated font-medium border-l-2 border-slate transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M12 9v6"/><path d="M9 12h6"/></svg>
                  Подписка
                </a>
                <a href="/account/history" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  История поиска
                </a>
                <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-6">Настройки</div>
                <a href="/account/settings" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                  Настройки
                </a>
              </div>
            </div>
          </aside>

          <main>
            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Управление подпиской</h2>

              <div className="rounded-[24px] p-[31px] bg-ivory-elevated mb-8">
                <div className="flex justify-between items-start flex-wrap gap-4">
                  <div>
                    <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Текущий тариф</p>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="inline-flex items-center px-4 py-[6px] text-[14px] font-semibold bg-ivory-elevated text-slate border border-slate">Базовый</span>
                      <span className="text-[14px] text-body-subtle">399 ₽ / месяц</span>
                    </div>
                    <p className="text-[15px] text-body-subtle mt-2 mb-0">Действует до 15.07.2026 · Автопродление включено</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[12px] text-body-muted mb-1">Использовано</p>
                    <p className="text-2xl font-bold text-slate">42 / 100</p>
                    <p className="text-[12px] text-body-muted">товара</p>
                  </div>
                </div>
              </div>

              <h3 className="text-2xl font-semibold text-slate mb-4">Сменить тариф</h3>
              <div className="grid grid-cols-3 gap-6 items-start mb-8 max-lg:grid-cols-1 max-lg:max-w-[480px] max-lg:mx-auto">
                {[
                  {
                    name: 'Пробный', price: '0', period: '', features: ['До 10 товаров', '2 поставщика', 'Обновление 24ч'],
                    current: true, disabled: true, featured: false,
                  },
                  {
                    name: 'Базовый', price: '399', period: '/ мес', discount: '−20% на следующий месяц',
                    features: ['До 100 товаров', '15+ поставщиков', 'Обновление 6ч', 'Экспорт PDF/CSV', 'Поддержка 24/7'],
                    current: true, disabled: false, featured: true,
                  },
                  {
                    name: 'Продвинутый', price: '499', period: '/ мес', discount: '−20% на первый месяц',
                    features: ['Безлимитный поиск', '50+ поставщиков', 'Real-time обновление', 'Нечёткий поиск', 'API-доступ', 'Персональный менеджер'],
                    current: false, disabled: false, featured: false,
                  },
                ].map((plan) => (
                  <div key={plan.name} className={`rounded-[24px] p-[31px] flex flex-col cursor-pointer ${plan.featured ? 'bg-slate text-ivory' : 'bg-ivory-elevated'}`}>
                    <span className={`inline-block font-montserrat text-xs uppercase tracking-[0.04em] px-2 py-1 mb-4 ${plan.featured ? 'bg-clay text-ivory' : plan.current ? 'bg-ivory-warm text-slate' : 'bg-ivory-warm text-body-muted'}`}>
                      {plan.current && plan.featured ? 'Ваш план' : plan.name}
                    </span>
                    <div className={`text-[40px] font-bold leading-none mb-2 ${plan.featured ? 'text-ivory' : 'text-slate'}`}>
                      {plan.price} ₽ {plan.period && <span className="text-base font-normal text-body-subtle">{plan.period}</span>}
                    </div>
                    {plan.discount && <span className="inline-block text-[13px] font-semibold text-green-discount mt-2">{plan.discount}</span>}
                    <ul className="my-6 flex-1">
                      {plan.features.map((f) => (
                        <li key={f} className={`flex items-start gap-3 py-[6px] text-[15px] ${plan.featured ? 'text-[#D1CFC5]' : 'text-body'}`}>
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="flex-shrink-0 mt-0.5">
                            <path d="M13.5 4.5L6 12L2.5 8.5" stroke="#788C5D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                          {f}
                        </li>
                      ))}
                    </ul>
                    {plan.current && plan.featured ? (
                      <button disabled className="w-full py-3 text-[15px] font-medium bg-ivory text-slate border border-ivory opacity-50 cursor-not-allowed">Текущий тариф</button>
                    ) : plan.current ? (
                      <button disabled className="w-full py-3 text-[15px] font-medium bg-transparent text-body-muted border border-border-default opacity-50 cursor-not-allowed">Текущий</button>
                    ) : (
                      <Link href="/register?plan=advanced" className="block w-full text-center py-3 text-[15px] font-medium no-underline bg-transparent text-slate border border-slate transition-colors hover:bg-ivory-elevated">Перейти на Продвинутый</Link>
                    )}
                  </div>
                ))}
              </div>

              <div className="mb-12">
                <h3 className="text-2xl font-semibold text-slate mb-4">Способ оплаты</h3>
                <div className="rounded-[24px] p-[31px] bg-ivory-elevated flex justify-between items-center flex-wrap gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-8 bg-slate flex items-center justify-center text-ivory text-[10px] font-bold">VISA</div>
                    <div>
                      <div className="font-medium text-slate">Visa ···· 4242</div>
                      <p className="text-[12px] text-body-muted mb-0">Истекает 12/27</p>
                    </div>
                  </div>
                  <button className="btn-ghost btn-sm">Изменить</button>
                </div>
              </div>

              <div className="rounded-[24px] p-[31px] bg-ivory-warm mt-12">
                <h4 className="text-xl font-semibold text-[#C6613F] mb-2">Отмена подписки</h4>
                <p className="text-[15px] text-body-subtle">После отмены ваш тариф будет действовать до конца оплаченного периода.</p>
                <button className="btn-danger btn-sm mt-4">Отменить подписку</button>
              </div>
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}
