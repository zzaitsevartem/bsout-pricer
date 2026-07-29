'use client';

type Section = 'profile' | 'subscription' | 'history' | 'settings';

type NavItem = {
  section: Section;
  label: string;
  href: string;
  icon: React.ReactNode;
};

const MAIN_ITEMS: NavItem[] = [
  {
    section: 'profile',
    label: 'Профиль',
    href: '/account',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    section: 'subscription',
    label: 'Подписка',
    href: '/subscription',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="2" y="4" width="20" height="16" rx="2" />
        <path d="M12 9v6" />
        <path d="M9 12h6" />
      </svg>
    ),
  },
  {
    section: 'history',
    label: 'История поиска',
    href: '/account/history',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
];

const SETTINGS_ITEMS: NavItem[] = [
  {
    section: 'settings',
    label: 'Настройки',
    href: '/account/settings',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
];

export function AccountSidebar({ active }: { active: Section }) {
  const linkClass = (section: Section) =>
    `flex items-center gap-3 px-[10px] py-2 text-[15px] text-body no-underline transition-colors hover:bg-ivory-elevated ${
      active === section ? 'bg-ivory-elevated font-medium border-l-2 border-slate' : ''
    }`;

  return (
    <aside className="sticky top-20 self-start max-md:hidden">
      <div className="w-full">
        <div className="p-0">
          <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-4">
            Аккаунт
          </div>
          {MAIN_ITEMS.map((item) => (
            <a key={item.section} href={item.href} className={linkClass(item.section)}>
              {item.icon}
              {item.label}
            </a>
          ))}

          <div className="font-montserrat text-[12px] uppercase tracking-[0.04em] text-body-muted px-2 mb-2 mt-6">
            Настройки
          </div>
          {SETTINGS_ITEMS.map((item) => (
            <a key={item.section} href={item.href} className={linkClass(item.section)}>
              {item.icon}
              {item.label}
            </a>
          ))}
        </div>
      </div>
    </aside>
  );
}
