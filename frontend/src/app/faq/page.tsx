'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';

const faqItems = [
  { q: 'Что такое BScout?', a: 'BScout — это веб-платформа для поиска и сравнения цен на запчасти для мобильных телефонов, ноутбуков и другой электроники среди локальных магазинов города Ставрополя. Сервис собирает информацию из четырёх магазинов: ТГСМ, Профи, Либерти и Дивизион.' },
  { q: 'Сколько стоит использование?', a: 'Доступен бесплатный пробный тариф на 7 дней с отслеживанием до 10 товаров. Базовый стоит 399 ₽ за 30 дней и позволяет отслеживать до 100 товаров. Продвинутый стоит 499 ₽ за 30 дней и позволяет отслеживать до 500 товаров; в него также входят нечёткий поиск, уведомления о снижении цен и экспорт отчётов. Лимит каждого тарифа — до пяти магазинов. Скидка 20% применяется к первому платежу за платный тариф.' },
  { q: 'Какие магазины подключены?', a: 'Сейчас цены собираются в магазинах ТГСМ, Профи, Либерти и Дивизион.' },
  { q: 'Как часто обновляются цены?', a: 'Цены обновляются по общему расписанию для всех тарифов — три раза в день. Частота не зависит от тарифа, а данные обновляются после очередного успешного обхода магазинов.' },
  { q: 'Что такое нечёткий поиск?', a: 'Нечёткий поиск (fuzzy search) доступен на Продвинутом тарифе. Он находит товары даже при ошибках в написании, опечатках и неточном вводе. Например, запрос «дисплей айфон 13» найдёт «Дисплей iPhone 13».' },
  { q: 'Могу ли я отменить подписку?', a: 'Да, вы можете отменить подписку в любой момент в личном кабинете. После отмены доступ к платным функциям сохранится до конца оплаченного периода.' },
  { q: 'Какие способы оплаты принимаются?', a: 'Доступный способ оплаты будет указан при оформлении тарифа. Возможность оплаты зависит от настроек платёжного сервиса.' },
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
      <Header />
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

        <div className="max-w-[720px] mx-auto border border-border-subtle rounded-[24px] overflow-hidden">
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
