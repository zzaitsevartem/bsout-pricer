'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

const products = [
  { name: 'Дисплей iPhone 13 (оригинал)', store: 'ТГСМ', available: 'В наличии', price: '4 500 ₽', oldPrice: '5 200 ₽', cheapest: true },
  { name: 'Дисплей iPhone 13 (аналог)', store: 'Профи', available: 'В наличии', price: '3 200 ₽', cheapest: true },
  { name: 'Дисплей iPhone 13 Pro (оригинал)', store: 'Либерти', available: 'В наличии', price: '6 800 ₽', cheapest: false },
  { name: 'Дисплей iPhone 13 mini', store: 'ГринСпарк', available: 'В наличии', price: '3 900 ₽', oldPrice: '4 500 ₽', cheapest: false },
  { name: 'Дисплей iPhone 13 (оригинал)', store: 'Дивизион', available: 'Под заказ', price: '5 100 ₽', cheapest: false },
];

export default function SearchPage() {
  return (
    <>
      <Header showProfileIcon navCta="login" />
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-lg:grid-cols-1">
          <aside className="sticky top-20 self-start max-lg:hidden">
            <div className="pb-6 mb-6 border-b border-border-light-subtle">
              <h4 className="text-[15px] font-semibold text-slate mb-3">Магазин</h4>
              <div className="flex flex-col gap-2">
                {['Все магазины', 'ТГСМ', 'Профи', 'Либерти', 'ГринСпарк', 'Дивизион'].map((store) => (
                  <label key={store} className="inline-flex items-center gap-2 cursor-pointer text-[15px] text-slate">
                    <input type="checkbox" defaultChecked={store !== 'ГринСпарк'} className="hidden" />
                    <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0">
                      <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden">
                        <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </span>
                    {store}
                  </label>
                ))}
              </div>
            </div>

            <div className="pb-6 mb-6 border-b border-border-light-subtle">
              <h4 className="text-[15px] font-semibold text-slate mb-3">Цена</h4>
              <div className="flex gap-2">
                <input type="text" className="w-20 px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate" placeholder="от" />
                <input type="text" className="w-20 px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate" placeholder="до" />
              </div>
            </div>

            <div className="pb-6 mb-6 border-b border-border-light-subtle">
              <h4 className="text-[15px] font-semibold text-slate mb-3">Категория</h4>
              <div className="flex flex-col gap-2">
                {['Дисплеи', 'Аккумуляторы', 'Материнские платы', 'Шлейфы', 'Корпуса'].map((cat) => (
                  <label key={cat} className="inline-flex items-center gap-2 cursor-pointer text-[15px] text-slate">
                    <input type="checkbox" defaultChecked={cat === 'Дисплеи' || cat === 'Аккумуляторы'} className="hidden" />
                    <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0">
                      <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden">
                        <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </span>
                    {cat}
                  </label>
                ))}
              </div>
            </div>

            <div className="pb-6 mb-6 border-b border-border-light-subtle">
              <h4 className="text-[15px] font-semibold text-slate mb-3">Наличие</h4>
              <div className="flex flex-col gap-2">
                <label className="inline-flex items-center gap-2 cursor-pointer text-[15px] text-slate">
                  <input type="checkbox" defaultChecked className="hidden" />
                  <span className="w-[18px] h-[18px] border border-[#87867F] bg-ivory flex items-center justify-center flex-shrink-0">
                    <svg width="12" height="6" viewBox="0 0 12 6" fill="none" className="hidden">
                      <path d="M1 3L4 6L11 1" stroke="#FAF9F5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                  Только в наличии
                </label>
              </div>
            </div>

            <button className="btn-primary w-full justify-center mb-2">Применить</button>
            <button className="btn-ghost w-full justify-center">Сбросить</button>
          </aside>

          <main>
            <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
              <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</a>
              <span className="text-body-muted">/</span>
              <span>Поиск</span>
            </div>

            <div className="flex gap-3 mb-6">
              <div className="relative flex-1">
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-body-subtle pointer-events-none" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>
                <input type="text" defaultValue="Дисплей iPhone 13" className="w-full pl-9 pr-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate" placeholder="Поиск запчастей..." />
              </div>
              <button className="btn-primary">Найти</button>
            </div>

            <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
              <span className="text-[15px] text-body-subtle">Найдено: 24 товара</span>
              <div className="flex items-center gap-2">
                <span className="text-[15px] text-body-subtle">Сортировка:</span>
                <div className="relative">
                  <select className="appearance-none pr-9 pl-3 py-2 text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate">
                    <option>Сначала дешёвые</option>
                    <option>Сначала дорогие</option>
                    <option>По дате обновления</option>
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 w-0 h-0 border-l-[5px] border-r-[5px] border-t-[5px] border-body-subtle pointer-events-none" />
                </div>
              </div>
            </div>

            <div className="rounded-[24px] overflow-hidden bg-ivory-elevated">
              {products.map((product) => (
                <div key={product.name} className="flex gap-4 p-4 items-center border-b border-border-light-subtle last:border-b-0">
                  <div className="w-16 h-16 bg-ivory-warm flex items-center justify-center text-body-muted text-xs flex-shrink-0">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <a href="/product" className="text-base font-semibold text-slate no-underline block mb-1 hover:underline">{product.name}</a>
                    <div className="text-[14px] text-body-subtle flex gap-3 flex-wrap">
                      <span>{product.store}</span>
                      <span>{product.available}</span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-lg font-bold text-slate">{product.price}</div>
                    {product.oldPrice && <div className="text-[14px] text-body-muted line-through">{product.oldPrice}</div>}
                    {product.cheapest && <div className="text-[12px] text-olive font-semibold">— Самый дешёвый</div>}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-center mt-8">
              <div className="inline-flex items-center">
                <span className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-body-muted border border-border-light-subtle bg-ivory-elevated pointer-events-none">←</span>
                <span className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-ivory bg-slate border border-slate z-10 -ml-px">1</span>
                <a href="#" className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-body bg-ivory border border-border-default -ml-px no-underline hover:bg-ivory-elevated">2</a>
                <a href="#" className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-body bg-ivory border border-border-default -ml-px no-underline hover:bg-ivory-elevated">3</a>
                <span className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-body bg-ivory border border-border-default -ml-px">…</span>
                <a href="#" className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-body bg-ivory border border-border-default -ml-px no-underline hover:bg-ivory-elevated">12</a>
                <a href="#" className="flex items-center justify-center w-9 h-9 text-[14px] font-medium text-body bg-ivory border border-border-default -ml-px no-underline hover:bg-ivory-elevated">→</a>
              </div>
            </div>
          </main>
        </div>
      </div>
      <Footer />
    </>
  );
}
