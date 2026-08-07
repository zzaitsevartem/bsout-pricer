'use client';

import React from 'react';
import {
  PARSER_POLL_INTERVAL_MS,
  useParsers,
  useRunParser,
  type ParserStatusResponse,
} from '@/models/parser';
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

const DEFAULT_RUN_LIMIT = 500;
const MAX_RUN_LIMIT = 100000;

function parseLimit(raw: string): number | null {
  if (raw.trim() === '') {
    return null;
  }
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 1 || value > MAX_RUN_LIMIT) {
    return null;
  }
  return value;
}

function RunScopeControls({
  fullSync,
  limitInput,
  sectionInput,
  disabled,
  onFullSyncChange,
  onLimitChange,
  onSectionChange,
}: {
  fullSync: boolean;
  limitInput: string;
  sectionInput: string;
  disabled: boolean;
  onFullSyncChange: (value: boolean) => void;
  onLimitChange: (value: string) => void;
  onSectionChange: (value: string) => void;
}) {
  const limit = parseLimit(limitInput);
  const limitInvalid = limitInput.trim() !== '' && limit === null;

  const section = sectionInput.trim();
  const sectionTooShort = section.length === 1;
  const scopeHint = fullSync
    ? 'Весь каталог целиком — 3–4 часа на магазин. Запускать только ночью.'
    : `Будет обработано до ${formatNumber(limit ?? DEFAULT_RUN_LIMIT)} позиций${
        limit === null ? ' (значение по умолчанию)' : ''
      }${section.length >= 2 ? ` из адресов со словом «${section}»` : ' с начала каталога'}.`;

  return (
    <div className="border border-border-default bg-ivory-elevated px-4 py-3 mb-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={fullSync}
            disabled={disabled}
            onChange={(event) => onFullSyncChange(event.target.checked)}
            className="hidden peer"
          />
          <span className="w-[18px] h-[18px] border border-body-muted bg-ivory flex items-center justify-center flex-shrink-0 peer-checked:bg-slate peer-checked:border-slate peer-disabled:opacity-60 transition-colors">
            <svg
              width="12"
              height="6"
              viewBox="0 0 12 6"
              fill="none"
              className="hidden peer-checked:block stroke-ivory"
            >
              <path
                d="M1 3L4 6L11 1"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <span className="text-[14px] text-body">Полный обход каталога</span>
        </label>

        <label className="inline-flex items-center gap-2">
          <span className="text-[14px] text-body">Лимит позиций</span>
          <input
            type="number"
            min={1}
            max={MAX_RUN_LIMIT}
            step={1}
            value={limitInput}
            disabled={disabled || fullSync}
            onChange={(event) => onLimitChange(event.target.value)}
            placeholder={String(DEFAULT_RUN_LIMIT)}
            className="w-[110px] px-3 py-[6px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_theme(colors.slate)] disabled:opacity-60 disabled:cursor-not-allowed"
          />
        </label>

        <label className="inline-flex items-center gap-2">
          <span className="text-[14px] text-body">Раздел</span>
          <input
            type="text"
            value={sectionInput}
            disabled={disabled}
            onChange={(event) => onSectionChange(event.target.value)}
            placeholder="displey"
            className="w-[190px] px-3 py-[6px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate focus:shadow-[0_0_0_2px_theme(colors.slate)] disabled:opacity-60 disabled:cursor-not-allowed"
          />
        </label>
      </div>

      <p className="text-[13px] text-body-subtle mt-2">{scopeHint}</p>
      {sectionTooShort && (
        <p className="text-[13px] text-clay mt-1">
          Раздел — не короче двух символов; пока фильтр не применяется.
        </p>
      )}
      {limitInvalid && (
        <p className="text-[13px] text-clay mt-1">
          Лимит должен быть целым числом от 1 до {formatNumber(MAX_RUN_LIMIT)} — пока применяется
          значение по умолчанию ({formatNumber(DEFAULT_RUN_LIMIT)}).
        </p>
      )}
      <p className="text-[13px] text-body-subtle mt-1">
        Обход ставится в очередь и идёт в фоне — страницу можно закрыть. Пока парсер работает,
        статус обновляется каждые {PARSER_POLL_INTERVAL_MS / 1000} с.
      </p>
    </div>
  );
}

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
  if (status === 503) {
    return apiErrorMessage(
      error,
      'Очередь задач недоступна — проверьте, что запущен воркер (arq src.worker.WorkerSettings)',
    );
  }
  return apiErrorMessage(error, 'Не удалось поставить парсер в очередь');
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
  const [fullSync, setFullSync] = React.useState(false);
  const [limitInput, setLimitInput] = React.useState('');
  const [sectionInput, setSectionInput] = React.useState('');

  const rows = parsers.data ?? [];
  const busy = runOne.isPending || runAll.isPending;

  const buildRequest = (storeSlug: string) => {
    const limit = fullSync ? null : parseLimit(limitInput);
    const section = sectionInput.trim();
    return {
      store_slug: storeSlug,
      full_sync: fullSync,
      ...(limit === null ? {} : { limit }),
      ...(section.length >= 2 ? { section } : {}),
    };
  };

  const handleRunAll = async () => {
    for (let i = 0; i < rows.length; i += 1) {
      await runAll.mutateAsync(buildRequest(rows[i].store_slug)).catch(() => null);
    }
  };

  const queuedNotice = [runOne.data, runAll.data]
    .filter((result) => result?.status === 'already_running')
    .map((result) => result?.store_slug)
    .join(', ');

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

      <RunScopeControls
        fullSync={fullSync}
        limitInput={limitInput}
        sectionInput={sectionInput}
        disabled={busy}
        onFullSyncChange={setFullSync}
        onLimitChange={setLimitInput}
        onSectionChange={setSectionInput}
      />

      {runOne.isError && (
        <p className="text-[14px] text-clay mb-3">{runErrorMessage(runOne.error)}</p>
      )}
      {runAll.isError && (
        <p className="text-[14px] text-clay mb-3">{runErrorMessage(runAll.error)}</p>
      )}
      {queuedNotice !== '' && (
        <p className="text-[14px] text-body-subtle mb-3">
          Уже выполняется, повторный запуск пропущен: {queuedNotice}
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
                  onRun={(storeSlug) => runOne.mutate(buildRequest(storeSlug))}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
