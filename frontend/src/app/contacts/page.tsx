'use client';

import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { ContactInfo, ContactForm } from '@/widgets/ContactWidget/ui/ContactWidget';

export default function ContactsPage() {
  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6 py-12 pb-16">
        <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
          <a href="/" className="text-body-subtle no-underline hover:text-slate hover:underline">Главная</a>
          <span className="text-body-muted">/</span>
          <span>Контакты</span>
        </div>

        <div className="pb-8 mb-8 border-b-0">
          <p className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted mb-2">Контакты</p>
          <h1 className="text-[40px] font-semibold text-slate mb-2">Свяжитесь с нами</h1>
          <p className="text-lg text-body">Есть вопросы или предложения? Напишите нам!</p>
        </div>

        <div className="grid grid-cols-2 gap-12 max-md:grid-cols-1">
          <ContactInfo />
          <ContactForm />
        </div>
      </div>
      <Footer />
    </>
  );
}
