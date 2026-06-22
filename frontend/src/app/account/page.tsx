'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

export default function AccountPage() {
  return (
    <>
      <Header navCta="logout" />
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <aside className="sticky top-20 self-start max-md:hidden">
            <div className="border-r-0 w-full">
              <div className="p-0">
                <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-4">Аккаунт</div>
                <a href="/account" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline bg-ivory-elevated font-medium border-l-2 border-slate transition-colors hover:bg-ivory-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  Профиль
                </a>
                <a href="/subscription" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
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
              <h2 className="text-[40px] font-semibold text-slate mb-6">Профиль</h2>
              <div className="flex gap-6 p-6 bg-ivory-elevated rounded-[24px] items-center flex-wrap">
                <div className="w-16 h-16 bg-ivory-warm flex items-center justify-center text-2xl font-bold text-slate">ИП</div>
                <div>
                  <h3 className="text-xl font-semibold text-slate mb-1">Иван Петров</h3>
                  <p className="text-body-subtle mb-0">ivan@example.com · +7 (999) 123-45-67</p>
                  <p className="text-[14px] text-body-subtle mt-1">Сервисный центр «РемонтПро»</p>
                </div>
                <a href="/account/settings" className="btn-secondary btn-sm ml-auto">Редактировать</a>
              </div>
            </div>

            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Текущий тариф</h2>
              <div className="rounded-[24px] p-[31px] bg-ivory-elevated flex justify-between items-center flex-wrap gap-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="inline-flex items-center px-4 py-[6px] text-[14px] font-semibold bg-ivory-elevated text-slate border border-slate">Базовый</span>
                    <span className="text-[12px] text-body-muted">Активен до 15.07.2026</span>
                  </div>
                  <p className="text-[15px] text-body-subtle mb-0">100 товаров · 15+ поставщиков · Обновление каждые 6ч · Экспорт PDF/CSV</p>
                </div>
                <a href="/subscription" className="btn-secondary btn-sm">Управлять</a>
              </div>
            </div>

            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">История поиска</h2>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {[
                  { query: 'Дисплей iPhone 13', results: '24 результата', date: '12.06.2026' },
                  { query: 'Аккумулятор Samsung Galaxy S23', results: '18 результатов', date: '10.06.2026' },
                  { query: 'Материнская плата Xiaomi Redmi Note 12', results: '7 результатов', date: '08.06.2026' },
                ].map((item) => (
                  <div key={item.query} className="flex items-center gap-4 px-6 py-4 border-b border-border-light-subtle last:border-b-0">
                    <div className="flex-1 min-w-0">
                      <div className="text-[15px] font-medium text-slate">{item.query}</div>
                      <div className="text-[14px] text-body-subtle">{item.results} · {item.date}</div>
                    </div>
                    <a href={`/search?q=${encodeURIComponent(item.query)}`} className="btn-arrow flex-shrink-0">Повторить</a>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-12">
              <h2 className="text-[40px] font-semibold text-slate mb-6">Недавно просмотренные</h2>
              <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
                {[
                  { name: 'Дисплей iPhone 13 Pro Max', price: 'от 6 800 ₽', stores: '3 магазина' },
                  { name: 'Шлейф зарядки Huawei P30', price: 'от 650 ₽', stores: '5 магазинов' },
                ].map((item) => (
                  <div key={item.name} className="flex items-center gap-4 px-6 py-4 border-b border-border-light-subtle last:border-b-0">
                    <div className="w-12 h-12 bg-ivory-warm flex items-center justify-center flex-shrink-0">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[15px] font-medium text-slate">{item.name}</div>
                      <div className="text-[14px] text-body-subtle">{item.price} · {item.stores}</div>
                    </div>
                    <a href="/product" className="btn-arrow flex-shrink-0">Открыть</a>
                  </div>
                ))}
              </div>
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}
