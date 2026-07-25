'use client';

import React, { useState } from 'react';
import { useAdminUsers, useToggleUserActive, type UserBriefResponse } from '@/models/admin';
import { formatDate } from '@/shared/lib/format';
import { cn } from '@/shared/lib/utils';
import {
  BADGE_BASE,
  BADGE_DANGER,
  BADGE_DARK,
  BADGE_DEFAULT,
  BADGE_SUCCESS,
  TABLE,
  TABLE_HEAD_ROW,
  TABLE_TD,
  TABLE_TH,
  TABLE_WRAPPER,
  apiErrorMessage,
} from '@/app/admin/_components/lib';

const COLUMNS = ['ID', 'Имя', 'Email', 'Роль', 'Статус', 'Дата регистрации', 'Действия'];
const PREVIEW_LIMIT = 10;
const FULL_LIMIT = 200;

function UserRow({
  user,
  isPending,
  onToggle,
}: {
  user: UserBriefResponse;
  isPending: boolean;
  onToggle: (id: number) => void;
}) {
  return (
    <tr>
      <td className={cn(TABLE_TD, 'font-montserrat text-[14px] text-body')}>#{user.id}</td>
      <td className={cn(TABLE_TD, 'font-semibold text-body')}>{user.full_name}</td>
      <td className={cn(TABLE_TD, 'text-body')}>{user.email}</td>
      <td className={TABLE_TD}>
        <span className={cn(BADGE_BASE, user.is_admin ? BADGE_DARK : BADGE_DEFAULT)}>
          {user.is_admin ? 'Администратор' : 'Пользователь'}
        </span>
      </td>
      <td className={TABLE_TD}>
        <span className={cn(BADGE_BASE, user.is_active ? BADGE_SUCCESS : BADGE_DANGER)}>
          {user.is_active ? 'Активен' : 'Заблокирован'}
        </span>
      </td>
      <td className={cn(TABLE_TD, 'text-[14px] text-body-subtle')}>
        {formatDate(user.created_at)}
      </td>
      <td className={TABLE_TD}>
        <button
          type="button"
          onClick={() => onToggle(user.id)}
          disabled={isPending}
          className="btn-ghost btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isPending ? 'Сохранение…' : user.is_active ? 'Заблокировать' : 'Разблокировать'}
        </button>
      </td>
    </tr>
  );
}

export function UsersTable() {
  const [limit, setLimit] = useState(PREVIEW_LIMIT);
  const users = useAdminUsers(0, limit);
  const toggleActive = useToggleUserActive();

  const rows = users.data ?? [];

  return (
    <section id="users">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-2xl font-semibold text-slate mb-0">
          {limit === PREVIEW_LIMIT ? 'Последние пользователи' : 'Все пользователи'}
        </h3>
        {limit === PREVIEW_LIMIT && (
          <button type="button" onClick={() => setLimit(FULL_LIMIT)} className="btn-arrow">
            Все пользователи
          </button>
        )}
      </div>

      {toggleActive.isError && (
        <p className="text-[14px] text-clay mb-3">
          {apiErrorMessage(toggleActive.error, 'Не удалось изменить статус пользователя')}
        </p>
      )}

      <div className={TABLE_WRAPPER}>
        <table className={TABLE}>
          <thead>
            <tr className={TABLE_HEAD_ROW}>
              {COLUMNS.map((column) => (
                <th key={column} className={TABLE_TH}>
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.isLoading ? (
              <tr>
                <td colSpan={COLUMNS.length} className={cn(TABLE_TD, 'text-body-subtle')}>
                  Загрузка…
                </td>
              </tr>
            ) : users.isError ? (
              <tr>
                <td colSpan={COLUMNS.length} className={cn(TABLE_TD, 'text-clay')}>
                  <span className="mr-3">
                    {apiErrorMessage(users.error, 'Не удалось загрузить пользователей')}
                  </span>
                  <button type="button" onClick={() => users.refetch()} className="btn-arrow">
                    Повторить
                  </button>
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length} className={cn(TABLE_TD, 'text-body-subtle')}>
                  Пользователей пока нет
                </td>
              </tr>
            ) : (
              rows.map((user) => (
                <UserRow
                  key={user.id}
                  user={user}
                  isPending={toggleActive.isPending && toggleActive.variables === user.id}
                  onToggle={(id) => toggleActive.mutate(id)}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
