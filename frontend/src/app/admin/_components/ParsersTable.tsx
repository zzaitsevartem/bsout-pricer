'use client';

import React from 'react';
import { useParsers, useRunParser, type ParserStatusResponse } from '@/models/parser';
import { cn } from '@/shared/lib/utils';
import {
  BADGE_BASE,
  BADGE_DANGER,
  BADGE_DEFAULT,
  BADGE_SUCCESS,
  BADGE_WARNING,
  TABLE,
  TABLE_HEAD_ROW,
  TABLE_TD,
  TABLE_TH,
  TABLE_WRAPPER,
  apiErrorMessage,
  apiErrorStatus,
  formatDateTime,
  formatNumber,
} from '@/app/admin/_components/lib';

const COLUMNS = ['Магазин', 'Статус', 'Товаров', 'Последний запуск', 'Действия'];

function parserBadge(parser: ParserStatusResponse) {
  if (parser.is_running) {
    return { label: 'Выполняется', className: BADGE_WARNING };
  }
  if (parser.errors.length > 0) {
    return { label: 'Ошибка', className: BADGE_DANGER };
  }
  if (parser.last_run) {
    return { label: 'Готов', className: BADGE_SUCCESS };
  }
  return { label: 'Не запускался', className: BADGE_DEFAULT };
}

function runErrorMessage(error: unknown): string {
  const status = apiErrorStatus(error);
  if (status === 404) {
    return apiErrorMessage(error, 'Парсер не зарегистрирован на бэкенде — запускать нечего');
  }
  if (status === 502) {
    return apiErrorMessage(error, 'Парсер завершился с ошибкой');
  }
  return apiErrorMessage(error, 'Не удалось запустить парсер');
}

function ParserRow({
  parser,
  isPending,
  onRun,
}: {
  parser: ParserStatusResponse;
  isPending: boolean;
  onRun: (storeSlug: string) => void;
}) {
  const badge = parserBadge(parser);

  return (
    <tr>
      <td className={cn(TABLE_TD, 'font-semibold text-body')}>{parser.store_slug}</td>
      <td className={TABLE_TD}>
        <span
          className={cn(BADGE_BASE, badge.className)}
          title={parser.errors.length > 0 ? parser.errors.join('\n') : undefined}
        >
          {badge.label}
        </span>
      </td>
      <td className={cn(TABLE_TD, 'text-body')}>{formatNumber(parser.products_found)}</td>
      <td className={cn(TABLE_TD, 'text-[14px] text-body-subtle')}>
        {formatDateTime(parser.last_run)}
      </td>
      <td className={TABLE_TD}>
        <button
          type="button"
          onClick={() => onRun(parser.store_slug)}
          disabled={isPending || parser.is_running}
          className="btn-ghost btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isPending ? 'Запуск…' : 'Запустить'}
        </button>
      </td>
    </tr>
  );
}

export function ParsersTable() {
  const parsers = useParsers();
  const runOne = useRunParser();
  const runAll = useRunParser();

  const rows = parsers.data ?? [];
  const busy = runOne.isPending || runAll.isPending;

  const handleRunAll = async () => {
    for (let i = 0; i < rows.length; i += 1) {
      await runAll.mutateAsync({ store_slug: rows[i].store_slug }).catch(() => null);
    }
  };

  return (
    <section id="parsers">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-2xl font-semibold text-slate mb-0">Парсеры</h3>
        <button
          type="button"
          onClick={handleRunAll}
          disabled={rows.length === 0 || busy}
          className="btn-primary btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {runAll.isPending ? 'Запуск…' : 'Запустить все'}
        </button>
      </div>

      {runOne.isError && (
        <p className="text-[14px] text-clay mb-3">{runErrorMessage(runOne.error)}</p>
      )}
      {runAll.isError && (
        <p className="text-[14px] text-clay mb-3">{runErrorMessage(runAll.error)}</p>
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
            {parsers.isLoading ? (
              <tr>
                <td colSpan={COLUMNS.length} className={cn(TABLE_TD, 'text-body-subtle')}>
                  Загрузка…
                </td>
              </tr>
            ) : parsers.isError ? (
              <tr>
                <td colSpan={COLUMNS.length} className={cn(TABLE_TD, 'text-clay')}>
                  <span className="mr-3">
                    {apiErrorMessage(parsers.error, 'Не удалось загрузить список парсеров')}
                  </span>
                  <button type="button" onClick={() => parsers.refetch()} className="btn-arrow">
                    Повторить
                  </button>
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length} className={cn(TABLE_TD, 'text-body-subtle')}>
                  Ни один парсер не зарегистрирован на бэкенде — запускать нечего
                </td>
              </tr>
            ) : (
              rows.map((parser) => (
                <ParserRow
                  key={parser.store_slug}
                  parser={parser}
                  isPending={runOne.isPending && runOne.variables?.store_slug === parser.store_slug}
                  onRun={(storeSlug) => runOne.mutate({ store_slug: storeSlug })}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
