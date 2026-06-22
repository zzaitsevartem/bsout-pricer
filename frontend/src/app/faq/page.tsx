'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

const faqItems = [
  { q: 'Что такое BScout?', a: 'BScout — это веб-платформа для поиска и сравнения цен на запчасти для мобильных телефонов, ноутбуков и другой электроники среди локальных магазинов города Ставрополя. Сервис автоматически собирает информацию о товарах из 5 магазинов и предоставляет единый интерфейс для поиска.' },
  { q: 'Сколько стоит использование?', a: 'Мы предлагаем 10-дневный бесплатный пробный период. После этого вы можете выбрать один из двух платных тарифов: Базовый — 399 ₽/мес (до 100 товаров, 15+ поставщиков) или Продвинутый — 499 ₽/мес (безлимитный поиск, 50+ поставщиков, нечёткий поиск, API). Скидка 20% на первый платёж любого тарифа.' },
  { q: 'Какие магазины подключены?', a: 'На данный момент подключены 5 магазинов: ТГСМ, Профи, Либерти, ГринСпарк и Дивизион. Мы постоянно работаем над подключением новых поставщиков.' },
  { q: 'Как часто обновляются цены?', a: 'Частота обновления зависит от вашего тарифа: Пробный — каждые 24 часа, Базовый — каждые 6 часов, Продвинутый — в реальном времени.' },
  { q: 'Что такое нечёткий поиск?', a: 'Нечёткий поиск (fuzzy search) доступен на Продвинутом тарифе. Он находит товары даже при ошибках в написании, опечатках и неточном вводе. Например, запрос «дисплей айфон 13» найдёт «Дисплей iPhone 13».' },
  { q: 'Могу ли я отменить подписку?', a: 'Да, вы можете отменить подписку в любой момент в личном кабинете. После отмены доступ к платным функциям сохранится до конца оплаченного периода.' },
  { q: 'Какие способы оплаты принимаются?', a: 'Мы принимаем банковские карты (Visa, Mastercard, МИР) через защищённый платёжный шлюз. Все платежи мгновенные и безопасные.' },
];

function AccordionItem({ q, a, isOpen, onClick }: { q: string; a: string; isOpen: boolean; onClick: () => void }) {
  return (
    <div className="border-b border-border-light-subtle last:border-b-0">
      <button
        className="flex justify-between items-center w-full px-5 py-[18px] text-base font-medium text-slate bg-ivory text-left transition-colors hover:bg-ivory-elevated"
        onClick={onClick}
      >
        {q}
        <span className={`w-4 h-4 border-r-2 border-b-2 border-body transition-transform duration-200 ${
          isOpen ? 'rotate-[225deg] mt-1' : 'rotate-[45deg] -mt-1'
        }`} />
      </button>
      {isOpen && (
        <div className="px-5 py-5 bg-ivory border-t border-border-light-subtle text-base text-body leading-relaxed">
          {a}
        </div>
      )}
    </div>
  );
}

export default function FaqPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <>
      <Header showProfileIcon navCta="register" />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</a>
          <span className="text-body-muted">/</span>
          <span>FAQ</span>
        </div>

        <div className="pb-8 mb-8 border-b-0">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">FAQ</p>
          <h1 className="text-[40px] font-semibold text-slate mb-2">Часто задаваемые вопросы</h1>
          <p className="text-lg text-body">Ответы на самые популярные вопросы о платформе BScout</p>
        </div>

        <div className="max-w-[720px] mx-auto border border-slate">
          {faqItems.map((item, i) => (
            <AccordionItem
              key={i}
              q={item.q}
              a={item.a}
              isOpen={openIndex === i}
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
            />
          ))}
        </div>
      </div>
      <Footer />
    </>
  );
}
