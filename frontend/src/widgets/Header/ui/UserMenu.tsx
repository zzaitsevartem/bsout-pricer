'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useLogout } from '@/models/auth';
import { useUnreadNotificationCount } from '@/models/notification';
import { useMe } from '@/models/user';
import { BellIcon, LogoutIcon, PersonIcon, ShieldIcon } from '@/shared/ui/IconSVG';

const itemClass =
  'group flex w-full items-center gap-2 px-[10px] py-2 text-[15px] text-left text-body no-underline bg-transparent border-none cursor-pointer transition-colors duration-150 hover:bg-ivory-elevated hover:text-slate';
const itemIconClass = 'shrink-0 text-body-subtle transition-colors duration-150 group-hover:text-slate';

const UserMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const router = useRouter();
  const pathname = usePathname();
  const { data: me } = useMe({ enabled: true });
  const { data: unread } = useUnreadNotificationCount({ enabled: true });
  const logout = useLogout();
  const unreadCount = unread?.unread_count ?? 0;

  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!isOpen) return;

    const handlePointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false);
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      setIsOpen(false);
      triggerRef.current?.focus();
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleLogout = () => {
    setIsOpen(false);
    logout.mutate(undefined, {
      onSettled: () => router.push('/login'),
    });
  };

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="btn-icon rounded-full"
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label={unreadCount > 0 ? `Меню профиля, непрочитанных уведомлений: ${unreadCount}` : 'Меню профиля'}
      >
        <PersonIcon />
        {unreadCount > 0 && <span className="absolute top-[7px] right-[7px] w-2 h-2 rounded-full bg-clay" />}
      </button>

      {isOpen && (
        <div
          role="menu"
          aria-label="Меню профиля"
          className="absolute right-0 top-full z-50 mt-2 min-w-[232px] overflow-hidden rounded-2xl border border-border-subtle bg-ivory shadow-lg"
        >
          <div className="px-3 py-3 border-b border-border-light-subtle">
            <p className="text-[15px] font-semibold text-slate truncate">{me?.full_name || 'Аккаунт'}</p>
            {me?.email && <p className="text-[14px] text-body-subtle truncate">{me.email}</p>}
          </div>

          <div className="p-2">
            <Link href="/account" role="menuitem" className={itemClass}>
              <PersonIcon width={16} height={16} className={itemIconClass} />
              Кабинет
            </Link>

            <Link href="/account/notifications" role="menuitem" className={itemClass}>
              <BellIcon className={itemIconClass} />
              Уведомления
              {unreadCount > 0 && (
                <span className="ml-auto min-w-[20px] h-5 px-1 flex items-center justify-center text-[12px] font-medium bg-clay text-ivory">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </Link>

            {me?.is_admin && (
              <Link href="/admin" role="menuitem" className={itemClass}>
                <ShieldIcon className={itemIconClass} />
                Админка
              </Link>
            )}

            <div className="my-1 border-t border-border-light-subtle" />

            <button
              type="button"
              role="menuitem"
              onClick={handleLogout}
              disabled={logout.isPending}
              className={`${itemClass} disabled:opacity-60 disabled:cursor-not-allowed`}
            >
              <LogoutIcon className={itemIconClass} />
              Выйти
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export { UserMenu };
