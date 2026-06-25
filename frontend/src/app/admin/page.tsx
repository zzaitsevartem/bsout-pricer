'use client';

import React from 'react';
import { Header } from '../../widgets/Header/ui/Header';

export default function AdminPage() {
  return (
    <>
      <Header adminBadge navCta="logout" />

      <div className="flex min-h-[calc(100vh-64px)]">
        <aside className="w-[264px] min-w-[240px] bg-ivory border-r border-border-light-subtle sticky top-16 h-[calc(100vh-64px)] overflow-y-auto max-lg:hidden">
          <div className="px-4 pt-4 pb-2">
            <span className="text-base font-bold text-slate no-underline">Панель управления</span>
          </div>
          <div className="p-2">
            <div className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted px-2 mb-2">Основное</div>
            {[
              { label: 'Дашборд', active: true, icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>) },
              { label: 'Пользователи', active: false, icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>) },
              { label: 'Подписки', active: false, icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M12 9v6"/><path d="M9 12h6"/></svg>) },
            ].map((item) => (
              <a key={item.label} href="#" className={`flex items-center gap-3 px-[10px] py-2 text-[15px] no-underline transition-colors hover:bg-ivory-elevated ${item.active ? 'bg-ivory-elevated text-slate font-medium border-l-2 border-slate' : 'text-body'}`}>
                {item.icon}
                {item.label}
              </a>
            ))}
            <div className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-4">Система</div>
            {[
              { label: 'Парсеры', icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>) },
              { label: 'Магазины', icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>) },
              { label: 'Логи', icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>) },
            ].map((item) => (
              <a key={item.label} href="#" className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated">
                {item.icon}
                {item.label}
              </a>
            ))}
          </div>
        </aside>

        <main className="flex-1 p-8 overflow-x-hidden max-lg:p-6 max-md:p-4">
          <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
            <div>
              <h2 className="text-[40px] font-semibold text-slate mb-1" style={{ marginBottom: '4px' }}>Дашборд</h2>
              <p className="text-[15px] text-body-subtle mb-0">Сводка по системе за последние 30 дней</p>
            </div>
            <div className="flex gap-3">
              <button className="btn-secondary btn-sm">Экспорт</button>
              <button className="btn-primary btn-sm">Обновить</button>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 mb-8 max-lg:grid-cols-2 max-[480px]:grid-cols-1">
            {[
              { value: '248', label: 'Пользователей', change: '+12 за неделю', up: true },
              { value: '156', label: 'Активных подписок', change: '+8 за неделю', up: true },
              { value: '12 847', label: 'Товаров в базе', change: '+342 за сегодня', up: false },
              { value: '5', label: 'Активных парсеров', change: 'Все работают', up: true },
            ].map((stat) => (
              <div key={stat.label} className="p-5 border border-border-light rounded-[24px] bg-ivory-elevated">
                <div className="text-[32px] font-bold text-slate leading-none mb-1">{stat.value}</div>
                <div className="text-[14px] text-body-subtle">{stat.label}</div>
                <p className={`text-[12px] mt-1 mb-0 ${stat.up ? 'text-olive' : 'text-body-subtle'}`}>{stat.change}</p>
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center mb-4">
            <h3 className="text-2xl font-semibold text-slate mb-0">Последние пользователи</h3>
            <a href="#" className="btn-arrow">Все пользователи</a>
          </div>

          <div className="overflow-x-auto border border-slate bg-ivory mb-8">
            <table className="w-full border-collapse text-[15px]">
              <thead>
                <tr className="bg-ivory-elevated border-b border-slate">
                  {['ID', 'Имя', 'Email', 'Тариф', 'Статус', 'Дата регистрации'].map((h) => (
                    <th key={h} className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { id: '#142', name: 'Иван Петров', email: 'ivan@example.com', tariff: 'Базовый', status: 'Активен', date: '01.06.2026', tariffBadge: 'badge-brand', statusBadge: 'badge-success' },
                  { id: '#141', name: 'Анна Смирнова', email: 'anna@example.com', tariff: 'Продвинутый', status: 'Активен', date: '30.05.2026', tariffBadge: 'badge-dark', statusBadge: 'badge-success' },
                  { id: '#140', name: 'Олег Кузнецов', email: 'oleg@example.com', tariff: 'Пробный', status: 'Истекает', date: '28.05.2026', tariffBadge: 'badge-default', statusBadge: 'badge-warning' },
                  { id: '#139', name: 'Мария Иванова', email: 'maria@example.com', tariff: 'Базовый', status: 'Заблокирован', date: '25.05.2026', tariffBadge: 'badge-brand', statusBadge: 'badge-danger' },
                ].map((row) => (
                  <tr key={row.id}>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle font-montserrat text-[14px] text-body">{row.id}</td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle font-semibold text-body">{row.name}</td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle text-body">{row.email}</td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle">
                      <span className={`inline-flex items-center text-xs px-2 py-0.5 border ${
                        row.tariffBadge === 'badge-brand' ? 'bg-ivory-elevated border-[#3D3D3A] text-[#0A0A0A]' :
                        row.tariffBadge === 'badge-dark' ? 'bg-slate text-ivory border-slate' :
                        'bg-ivory border-border-default text-slate'
                      }`}>{row.tariff}</span>
                    </td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle">
                      <span className={`inline-flex items-center text-xs px-2 py-0.5 border ${
                        row.statusBadge === 'badge-success' ? 'bg-[#EDF1E5] border-[#C7D2B0] text-[#4F5C36]' :
                        row.statusBadge === 'badge-warning' ? 'bg-[#F4EBD7] border-[#E5D29B] text-[#4A3A12]' :
                        'bg-[#F8E5DD] border-[#E8B6A1] text-[#8E3F22]'
                      }`}>{row.status}</span>
                    </td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle text-[14px] text-body-subtle">{row.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center mb-4">
            <h3 className="text-2xl font-semibold text-slate mb-0">Парсеры</h3>
            <button className="btn-primary btn-sm">Запустить все</button>
          </div>

          <div className="overflow-x-auto border border-slate bg-ivory">
            <table className="w-full border-collapse text-[15px]">
              <thead>
                <tr className="bg-ivory-elevated border-b border-slate">
                  {['Магазин', 'Статус', 'Товаров', 'Последнее обновление', 'Действия'].map((h) => (
                    <th key={h} className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { store: 'ТГСМ', status: 'Работает', items: '3 421', updated: '12.06.2026 14:30', ok: true },
                  { store: 'Профи', status: 'Работает', items: '2 890', updated: '12.06.2026 14:15', ok: true },
                  { store: 'Либерти', status: 'Ошибка', items: '1 567', updated: '11.06.2026 23:00', ok: false },
                  { store: 'ГринСпарк', status: 'Работает', items: '2 115', updated: '12.06.2026 12:00', ok: true },
                  { store: 'Дивизион', status: 'Не активен', items: '2 854', updated: '10.06.2026 18:00', ok: false },
                ].map((row) => (
                  <tr key={row.store}>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle font-semibold text-body">{row.store}</td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle">
                      <span className={`inline-flex items-center text-xs px-2 py-0.5 border ${
                        row.status === 'Работает' ? 'bg-[#EDF1E5] border-[#C7D2B0] text-[#4F5C36]' :
                        row.status === 'Ошибка' ? 'bg-[#F8E5DD] border-[#E8B6A1] text-[#8E3F22]' :
                        'bg-[#F4EBD7] border-[#E5D29B] text-[#4A3A12]'
                      }`}>{row.status}</span>
                    </td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle text-body">{row.items}</td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle text-[14px] text-body-subtle">{row.updated}</td>
                    <td className="px-4 py-[14px] border-b border-border-light-subtle">
                      <button className="btn-ghost btn-sm">Запустить</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </>
  );
}
