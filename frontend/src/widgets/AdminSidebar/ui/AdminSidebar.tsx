'use client';

const MAIN_ITEMS = [
  {
    label: 'Дашборд',
    active: true,
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
      </svg>
    ),
  },
  {
    label: 'Пользователи',
    active: false,
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    label: 'Подписки',
    active: false,
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="2" y="4" width="20" height="16" rx="2" /><path d="M12 9v6" /><path d="M9 12h6" />
      </svg>
    ),
  },
];

const SYSTEM_ITEMS = [
  {
    label: 'Парсеры',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
      </svg>
    ),
  },
  {
    label: 'Магазины',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
  {
    label: 'Логи',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
];

export function AdminSidebar() {
  return (
    <aside className="w-[264px] min-w-[240px] bg-ivory border-r border-border-light-subtle sticky top-16 h-[calc(100vh-64px)] overflow-y-auto max-lg:hidden">
      <div className="px-4 pt-4 pb-2">
        <span className="text-base font-bold text-slate no-underline">Панель управления</span>
      </div>
      <div className="p-2">
        <div className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted px-2 mb-2">Основное</div>
        {MAIN_ITEMS.map((item) => (
          <a
            key={item.label}
            href="#"
            className={`flex items-center gap-3 px-[10px] py-2 text-[15px] no-underline transition-colors hover:bg-ivory-elevated ${
              item.active ? 'bg-ivory-elevated text-slate font-medium border-l-2 border-slate' : 'text-body'
            }`}
          >
            {item.icon}
            {item.label}
          </a>
        ))}

        <div className="font-montserrat text-xs uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-4">Система</div>
        {SYSTEM_ITEMS.map((item) => (
          <a
            key={item.label}
            href="#"
            className="flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated"
          >
            {item.icon}
            {item.label}
          </a>
        ))}
      </div>
    </aside>
  );
}
