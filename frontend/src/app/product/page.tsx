'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

export default function ProductPage() {
  return (
    <>
      <Header showProfileIcon navCta="login" />
      <div className="max-w-[1200px] mx-auto px-6 py-8 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</a>
          <span className="text-body-muted">/</span>
          <a href="/search" className="text-body-subtle no-underline hover:text-slate hover:underline">Поиск</a>
          <span className="text-body-muted">/</span>
          <span>Дисплей iPhone 13</span>
        </div>

        <div className="grid grid-cols-2 gap-12 max-md:grid-cols-1">
          <div>
            <div className="rounded-[24px] bg-ivory-elevated aspect-square flex items-center justify-center text-body-muted text-[15px] border border-border-light">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
            </div>
          </div>
          <div>
            <span className="inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-success-soft border border-[#C7D2B0] text-[#4F5C36] mb-4">В наличии</span>
            <h1 className="text-[32px] font-bold text-slate mb-2">Дисплей iPhone 13 (оригинал)</h1>
            <p className="text-[15px] text-body-subtle mb-6">Оригинальный дисплей Apple для iPhone 13. Стекло Ceramic Shield, True Tone, Haptic Touch.</p>

            <div className="rounded-[24px] p-6 bg-ivory-elevated mb-6">
              <h4 className="text-xl font-semibold text-slate mb-4">Предложения магазинов</h4>
              <div className="flex flex-col gap-3">
                {[
                  { store: 'ТГСМ', badge: 'Самый дешёвый', price: '4 500 ₽', oldPrice: '5 200 ₽' },
                  { store: 'Профи', price: '4 800 ₽' },
                  { store: 'Либерти', price: '5 100 ₽', note: 'Доставка 3 дня' },
                  { store: 'ГринСпарк', price: '5 300 ₽' },
                ].map((item, i) => (
                  <div key={i} className="flex justify-between items-center pb-3 border-b border-border-light-subtle last:border-b-0 last:pb-0">
                    <div>
                      <span className="font-semibold text-slate">{item.store}</span>
                      {item.badge && <span className="ml-2 inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 bg-success-soft border border-[#C7D2B0] text-[#4F5C36]">{item.badge}</span>}
                      {item.note && <span className="ml-2 text-[13px] text-body-subtle">{item.note}</span>}
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-slate">{item.price}</div>
                      {item.oldPrice && <div className="text-[14px] text-body-muted line-through">{item.oldPrice}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <h4 className="text-xl font-semibold text-slate mb-4">История цены</h4>
            <p className="text-[15px] text-body-subtle mb-4">Изменение средней цены за последние 6 месяцев</p>
            <div className="w-full h-[120px] bg-ivory-elevated relative overflow-hidden">
              <svg className="absolute bottom-0 left-0 right-0 h-full" width="100%" height="100%" viewBox="0 0 500 120" preserveAspectRatio="none">
                <polyline points="0,80 50,70 100,85 150,60 200,50 250,55 300,40 350,45 400,30 450,35 500,25" fill="none" stroke="#141413" strokeWidth="2" vectorEffect="non-scaling-stroke"/>
                <polyline points="0,80 50,70 100,85 150,60 200,50 250,55 300,40 350,45 400,30 450,35 500,25" fill="url(#grad)" opacity="0.1"/>
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#141413"/>
                    <stop offset="100%" stopColor="#F0EEE6"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div className="flex justify-between mt-2">
              <span className="text-[12px] text-body-muted">Янв</span>
              <span className="text-[12px] text-body-muted">Фев</span>
              <span className="text-[12px] text-body-muted">Мар</span>
              <span className="text-[12px] text-body-muted">Апр</span>
              <span className="text-[12px] text-body-muted">Май</span>
              <span className="text-[12px] text-body-muted">Июн</span>
            </div>

            <div className="flex gap-3 mt-6">
              <a href="#" className="btn-primary">Перейти в магазин →</a>
              <button className="btn-secondary">В избранное</button>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
