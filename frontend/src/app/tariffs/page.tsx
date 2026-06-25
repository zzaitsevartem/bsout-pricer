'use client';

import React from 'react';
import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

export default function TariffsPage() {
  return (
    <>
      <Header showProfileIcon navCta="register" />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</a>
          <span className="text-body-muted">/</span>
          <span>Тарифы</span>
        </div>

        <div className="text-center border-b-0 pt-0 max-w-[600px] mx-auto mb-12">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Тарифы</p>
          <h1 className="text-[40px] font-semibold text-slate mb-2">Выберите свой план</h1>
          <p className="text-lg text-body">Начните с бесплатного пробного периода на 10 дней. Затем выберите тариф, который подходит вашим задачам.</p>
        </div>

        <div className="overflow-x-auto border border-slate bg-ivory mb-12">
          <table className="w-full border-collapse text-[15px]">
            <thead>
              <tr className="bg-ivory-elevated border-b border-slate">
                <th className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap w-[30%]">Возможности</th>
                <th className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-center px-4 py-3 whitespace-nowrap w-[23.33%]">Пробный</th>
                <th className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-ivory text-center px-4 py-3 whitespace-nowrap w-[23.33%] bg-slate">Базовый</th>
                <th className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-center px-4 py-3 whitespace-nowrap w-[23.33%]">Продвинутый</th>
              </tr>
            </thead>
            <tbody>
              {[
                { label: 'Цена', values: ['0 ₽ / 10 дней', '399 ₽ / месяц', '499 ₽ / месяц'], bold: true },
                { label: 'Количество товаров', values: ['до 10', 'до 100', 'безлимит'] },
                { label: 'Количество поставщиков', values: ['2', '15+', '50+'] },
                { label: 'Обновление цен', values: ['24ч', '6ч', 'real-time'] },
                { label: 'История цен', values: ['1 месяц', '6 месяцев', '12+ месяцев'] },
                { label: 'Экспорт отчётов (PDF/CSV)', values: ['—', '✓', '✓'], dimmed: [true, false, false] },
                { label: 'Нечёткий поиск (fuzzy)', values: ['—', '—', '✓'], dimmed: [true, true, false] },
                { label: 'API-доступ', values: ['—', '—', '✓'], dimmed: [true, true, false] },
                { label: 'Расширенная аналитика', values: ['—', '—', '✓'], dimmed: [true, true, false] },
                { label: 'Поддержка', values: ['—', '24/7', '24/7 + менеджер'], dimmed: [true, false, false] },
              ].map((row, i) => (
                <tr key={i}>
                  <td className="px-4 py-[14px] border-b border-border-light-subtle font-medium text-body">{row.label}</td>
                  {row.values.map((val, j) => (
                    <td key={j} className={`px-4 py-[14px] border-b border-border-light-subtle text-center ${j === 1 ? 'bg-ivory-elevated' : ''} ${row.bold ? 'font-bold' : ''} ${row.dimmed?.[j] ? 'text-body-muted' : 'text-body'}`}>
                      {val}
                    </td>
                  ))}
                </tr>
              ))}
              <tr>
                <td className="px-4 py-[14px] border-b border-border-light-subtle"></td>
                {['/register', '/register?plan=basic', '/register?plan=advanced'].map((href, j) => (
                  <td key={j} className={`px-4 py-5 text-center ${j === 1 ? 'bg-ivory-elevated' : ''}`}>
                    <Link href={href} className={`btn ${j === 1 ? 'btn-primary' : 'btn-secondary'} btn-sm no-underline`}>
                      {j === 0 ? 'Попробовать' : 'Выбрать'}
                    </Link>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        <p className="text-center text-[14px] text-body-muted max-w-[500px] mx-auto">
          Скидка 20% на первый платёж любого платного тарифа. Отмена подписки в любой момент.
        </p>
      </div>
      <Footer />
    </>
  );
}
