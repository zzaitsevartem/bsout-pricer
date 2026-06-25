'use client';

import React from 'react';
import { Header } from '../../widgets/Header/ui/Header';
import { Footer } from '../../widgets/Footer/ui/Footer';

export default function ContactsPage() {
  return (
    <>
      <Header showProfileIcon navCta="register" />
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
          <div>
            {[
              { icon: (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>), title: 'Email', lines: ['hello@bscout.ru', 'support@bscout.ru'] },
              { icon: (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>), title: 'Телефон', lines: ['+7 (999) 123-45-67'], caption: 'Пн–Пт, 09:00–18:00' },
              { icon: (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>), title: 'Адрес', lines: ['г. Ставрополь, ул. Ленина, д. 123'], caption: 'По предварительной договорённости' },
              { icon: (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 2H3v16h5v4l4-4h5l4-4V2zm-10 9V7m0 8v-2"/></svg>), title: 'Поддержка', lines: ['Чат поддержки доступен в личном кабинете для тарифов Базовый и Продвинутый'] },
            ].map((item) => (
              <div key={item.title} className="flex gap-4 mb-6">
                <div className="w-10 h-10 bg-ivory-elevated flex items-center justify-center flex-shrink-0 text-slate">
                  {item.icon}
                </div>
                <div>
                  <h5 className="text-[18px] font-semibold text-slate mb-1">{item.title}</h5>
                  {item.lines.map((line, i) => (
                    <p key={i} className="text-body-subtle mb-0">{line}</p>
                  ))}
                  {item.caption && <p className="text-[14px] text-body-muted mt-1">{item.caption}</p>}
                </div>
              </div>
            ))}
          </div>

          <div>
            <div className="rounded-[24px] p-[31px] bg-ivory-elevated">
              <h4 className="text-xl font-semibold text-slate mb-4">Напишите нам</h4>
              <form>
                <div className="mb-4">
                  <label htmlFor="name" className="block text-[15px] font-medium text-slate mb-2">Имя</label>
                  <input type="text" id="name" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Ваше имя" />
                </div>
                <div className="mb-4">
                  <label htmlFor="email" className="block text-[15px] font-medium text-slate mb-2">Email</label>
                  <input type="email" id="email" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="your@email.com" />
                </div>
                <div className="mb-4">
                  <label htmlFor="subject" className="block text-[15px] font-medium text-slate mb-2">Тема</label>
                  <input type="text" id="subject" className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413]" placeholder="Чем мы можем помочь?" />
                </div>
                <div className="mb-4">
                  <label htmlFor="message" className="block text-[15px] font-medium text-slate mb-2">Сообщение</label>
                  <textarea id="message" rows={5} className="block w-full px-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_#141413] resize-y min-h-[96px]" placeholder="Ваше сообщение..." />
                </div>
                <button type="submit" className="btn-primary w-full justify-center">Отправить</button>
              </form>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
