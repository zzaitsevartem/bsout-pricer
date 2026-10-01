'use client';

import React, { useState } from 'react';
import {
  useAdminUsers,
  useToggleUserActive,
  useToggleUserAdmin,
  useDeleteUser,
  type UserBriefResponse,
} from '@/models/admin';
import { useMe } from '@/models/user';
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
  isSelf,
  isActivePending,
  isAdminPending,
  isDeletePending,
  onToggleActive,
  onToggleAdmin,
  onDelete,
}: {
  user: UserBriefResponse;
  isSelf: boolean;
  isActivePending: boolean;
  isAdminPending: boolean;
  isDeletePending: boolean;
  onToggleActive: (id: number) => void;
  onToggleAdmin: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <tr>
      <td className={cn(TABLE_TD, 'font-montserrat text-[14px] text-body')}>#{user.id}</td>
      <td className={cn(TABLE_TD, 'font-semibold text-body')}>
        {user.full_name}
        {isSelf && <span className="ml-2 text-[12px] font-normal text-body-muted">(это вы)</span>}
      </td>
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
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => onToggleAdmin(user.id)}
            disabled={isSelf || isAdminPending}
            className="btn-ghost btn-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isAdminPending ? 'Сохранение…' : user.is_admin ? 'Снять права' : 'Выдать права'}
          </button>
          <button
            type="button"
            onClick={() => onToggleActive(user.id)}
            disabled={isSelf || isActivePending}
            className="btn-ghost btn-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isActivePending ? 'Сохранение…' : user.is_active ? 'Заблокировать' : 'Разблокировать'}
          </button>
          <button
            type="button"
            onClick={() => onDelete(user.id)}
            disabled={isSelf || isDeletePending}
            className="btn-ghost btn-sm text-clay disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isDeletePending ? 'Удаление…' : 'Удалить'}
          </button>
        </div>
      </td>
    </tr>
  );
}

export function UsersTable() {
  const [limit, setLimit] = useState(PREVIEW_LIMIT);
  const users = useAdminUsers(0, limit);
  const me = useMe();
  const currentUserId = me.data?.id;
  const toggleActive = useToggleUserActive();
  const toggleAdmin = useToggleUserAdmin();
  const deleteUser = useDeleteUser();

  const rows = users.data ?? [];
  const mutationError = toggleActive.error ?? toggleAdmin.error ?? deleteUser.error;

  const handleDelete = (id: number) => {
    const target = rows.find((user) => user.id === id);
    const name = target?.full_name ?? target?.email ?? `#${id}`;
    if (window.confirm(`Удалить пользователя «${name}»? Это действие необратимо.`)) {
      deleteUser.mutate(id);
    }
  };

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

      {mutationError && (
        <p className="text-[14px] text-clay mb-3">
          {apiErrorMessage(mutationError, 'Не удалось изменить данные пользователя')}
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
                  isSelf={user.id === currentUserId}
                  isActivePending={toggleActive.isPending && toggleActive.variables === user.id}
                  isAdminPending={toggleAdmin.isPending && toggleAdmin.variables === user.id}
                  isDeletePending={deleteUser.isPending && deleteUser.variables === user.id}
                  onToggleActive={(id) => toggleActive.mutate(id)}
                  onToggleAdmin={(id) => toggleAdmin.mutate(id)}
                  onDelete={handleDelete}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
