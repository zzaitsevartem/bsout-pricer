'use client';

import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { FaqAccordion } from '@/widgets/FaqAccordion/ui/FaqAccordion';

export default function FaqPage() {
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

        <FaqAccordion />
      </div>
      <Footer />
    </>
  );
}
