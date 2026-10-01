import React from 'react';
import { cn } from '@/shared/lib/utils';

type SidebarItem = {
  label: string;
  href: string;
  active?: boolean;
  icon: React.ReactNode;
};

const MAIN_ITEMS: SidebarItem[] = [
  {
    label: 'Дашборд',
    href: '#dashboard',
    active: true,
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
    ),
  },
  {
    label: 'Пользователи',
    href: '#users',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
    ),
  },
];

const SYSTEM_ITEMS: SidebarItem[] = [
  {
    label: 'Парсеры',
    href: '#parsers',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
    ),
  },
  {
    label: 'Рассылки',
    href: '#mailings',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/></svg>
    ),
  },
];

function SidebarLink({ item }: { item: SidebarItem }) {
  return (
    <a
      href={item.href}
      className={cn(
        'flex items-center gap-3 rounded-full px-3 py-2 text-[15px] no-underline transition-colors hover:bg-ivory-elevated',
        item.active ? 'bg-ivory-elevated text-slate font-medium' : 'text-body',
      )}
    >
      {item.icon}
      {item.label}
    </a>
  );
}

export function AdminSidebar() {
  return (
    <aside className="w-[264px] min-w-[240px] bg-ivory border-r border-border-light-subtle sticky top-16 h-[calc(100vh-64px)] overflow-y-auto max-lg:hidden">
      <div className="px-4 pt-4 pb-2">
        <span className="text-base font-bold text-slate no-underline">Панель управления</span>
      </div>
      <div className="p-2">
        <div className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted px-2 mb-2">Основное</div>
        {MAIN_ITEMS.map((item) => (
          <SidebarLink key={item.label} item={item} />
        ))}
        <div className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-4">Система</div>
        {SYSTEM_ITEMS.map((item) => (
          <SidebarLink key={item.label} item={item} />
        ))}
      </div>
    </aside>
  );
}
