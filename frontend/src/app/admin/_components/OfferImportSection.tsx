'use client';

import React from 'react';
import { useImportOffers } from '@/models/admin';
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
  formatNumber,
} from '@/app/admin/_components/lib';
import { parseOfferImportPayload } from '@/app/admin/_components/offerImport';

const ISSUE_PREVIEW_LIMIT = 10;

export function OfferImportSection() {
  const importOffers = useImportOffers();
  const [text, setText] = React.useState('');
  const [parsed, setParsed] = React.useState<ReturnType<typeof parseOfferImportPayload> | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleTextChange = (value: string) => {
    setText(value);
    setParsed(value.trim() === '' ? null : parseOfferImportPayload(value));
  };

  const handleFile = async (file: File | undefined) => {
    if (!file) {
      return;
    }
    const content = await file.text();
    handleTextChange(content);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const rows = parsed?.ok === true ? parsed.rows : [];
  const issues = parsed?.ok === true ? parsed.issues : [];
  const parseError = parsed?.ok === false ? parsed.error : null;
  const canImport = rows.length > 0 && !importOffers.isPending;

  const result = importOffers.data;
  const visibleIssues = issues.slice(0, ISSUE_PREVIEW_LIMIT);

  return (
    <section id="import">
      <div className="flex justify-between items-center mb-4 flex-wrap gap-3">
        <div>
          <h3 className="text-2xl font-semibold text-slate mb-0">Импорт офферов</h3>
          <p className="text-[15px] text-body-subtle mb-0 mt-1">
            JSON-массив в формате <code className="font-mono text-[13px]">OfferImportItem</code>.
          </p>
        </div>
        <div className="flex gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(event) => {
              void handleFile(event.target.files?.[0]);
            }}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="btn-secondary btn-sm"
          >
            Загрузить файл
          </button>
        </div>
      </div>

      <div className="mb-4">
        <label htmlFor="offer-import-payload" className="text-[14px] text-body block mb-2">
          Данные офферов
        </label>
        <textarea
          id="offer-import-payload"
          value={text}
          onChange={(event) => handleTextChange(event.target.value)}
          rows={8}
          spellCheck={false}
          placeholder='[{"store_slug":"profi","source_sku":"123","title":"Дисплей iPhone 13","price_retail":"3490"}]'
          className="w-full rounded-2xl px-4 py-3 text-[14px] font-mono text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default"
        />
      </div>

      {parseError !== null && (
        <p className="text-[14px] text-clay mb-3">{parseError}</p>
      )}

      {parsed?.ok === true && (
        <div className="flex gap-3 flex-wrap mb-4">
          <span className={cn(BADGE_BASE, BADGE_WARNING)}>
            В файле строк: {formatNumber(parsed.total)}
          </span>
          <span className={cn(BADGE_BASE, rows.length > 0 ? BADGE_SUCCESS : BADGE_DANGER)}>
            Готово к импорту: {formatNumber(rows.length)}
          </span>
          {issues.length > 0 && (
            <span className={cn(BADGE_BASE, BADGE_DANGER)}>
              Пропущено: {formatNumber(issues.length)}
            </span>
          )}
        </div>
      )}

      {issues.length > 0 && (
        <div className={TABLE_WRAPPER}>
          <table className={TABLE}>
            <thead>
              <tr className={TABLE_HEAD_ROW}>
                <th className={TABLE_TH}>Строка</th>
                <th className={TABLE_TH}>Причина</th>
              </tr>
            </thead>
            <tbody>
              {visibleIssues.map((issue) => (
                <tr key={issue.index}>
                  <td className={cn(TABLE_TD, 'font-mono text-[13px] text-body-subtle')}>
                    {issue.index + 1}
                  </td>
                  <td className={cn(TABLE_TD, 'text-[14px] text-clay')}>{issue.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {issues.length > visibleIssues.length && (
            <p className="text-[13px] text-body-subtle px-4 py-3 mb-0">
              Ещё {formatNumber(issues.length - visibleIssues.length)} строк с ошибками — исправьте
              их в исходном файле.
            </p>
          )}
        </div>
      )}

      <div className="flex gap-3 items-center flex-wrap">
        <button
          type="button"
          onClick={() => importOffers.mutate(rows)}
          disabled={!canImport}
          className="btn-primary btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {importOffers.isPending
            ? 'Импорт…'
            : `Импортировать${rows.length > 0 ? ` ${formatNumber(rows.length)}` : ''}`}
        </button>
        {issues.length > 0 && rows.length > 0 && (
          <p className="text-[13px] text-body-subtle mb-0">
            Будет отправлено только {formatNumber(rows.length)} корректных строк.
          </p>
        )}
      </div>

      {importOffers.isError && (
        <p className="text-[14px] text-clay mt-3 mb-0">
          {apiErrorMessage(importOffers.error, 'Не удалось импортировать офферы')}
        </p>
      )}

      {result !== undefined && !importOffers.isError && (
        <div className="border border-border-default bg-ivory-elevated px-4 py-3 mt-4">
          <div className="flex gap-3 flex-wrap mb-2">
            <span className={cn(BADGE_BASE, BADGE_SUCCESS)}>Создано: {formatNumber(result.created)}</span>
            <span className={cn(BADGE_BASE, BADGE_WARNING)}>
              Обновлено: {formatNumber(result.updated)}
            </span>
            <span className={cn(BADGE_BASE, BADGE_DEFAULT)}>
              Пропущено: {formatNumber(result.skipped)}
            </span>
            {result.errors.length > 0 && (
              <span className={cn(BADGE_BASE, BADGE_DANGER)}>
                Ошибок: {formatNumber(result.errors.length)}
              </span>
            )}
          </div>
          {result.errors.length > 0 && (
            <ul className="text-[13px] text-clay mb-0 pl-4">
              {result.errors.slice(0, ISSUE_PREVIEW_LIMIT).map((issue) => (
                <li key={issue.index}>
                  Строка {issue.index + 1}
                  {issue.store_slug ? ` (${issue.store_slug})` : ''} — {issue.reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
