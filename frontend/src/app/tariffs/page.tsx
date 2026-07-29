'use client';

import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { PlanComparison } from '@/widgets/PlanComparison/ui/PlanComparison';

export default function TariffsPage() {
  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</a>
          <span className="text-body-muted">/</span>
          <span>Тарифы</span>
        </div>
        <PlanComparison />
      </div>
      <Footer />
    </>
  );
}
