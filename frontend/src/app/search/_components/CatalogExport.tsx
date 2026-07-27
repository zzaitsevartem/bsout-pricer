'use client';

import React from 'react';
import Link from 'next/link';
import type { UseMutationResult } from '@tanstack/react-query';
import { EXPORT_FEATURE_UNAVAILABLE, EXPORT_SUBSCRIPTION_REQUIRED } from '@/models/export';
import type { ExportCatalogParams, ExportError, ExportedFile } from '@/models/export';

export type ExportCatalogMutation = UseMutationResult<
  ExportedFile,
  ExportError,
  ExportCatalogParams
>;

const FEATURE_TITLE = 'Экспорт доступен на тарифе «Продвинутый»';
const SUBSCRIPTION_TITLE = 'Нужна активная подписка';
const UPGRADE_FALLBACK = 'Ваш тариф не включает выгрузку отчётов.';

function isUpgradeError(error: ExportError): boolean {
  return (
    error.code === EXPORT_FEATURE_UNAVAILABLE ||
    error.code === EXPORT_SUBSCRIPTION_REQUIRED ||
    error.status === 403
  );
}

function upgradeTitle(error: ExportError): string {
  return error.code === EXPORT_SUBSCRIPTION_REQUIRED ? SUBSCRIPTION_TITLE : FEATURE_TITLE;
}

type ExportCsvButtonProps = {
  mutation: ExportCatalogMutation;
  params: ExportCatalogParams;
  disabled?: boolean;
};

export function ExportCsvButton({ mutation, params, disabled }: ExportCsvButtonProps) {
  return (
    <button
      type="button"
      onClick={() => mutation.mutate(params)}
      disabled={disabled || mutation.isPending}
      aria-busy={mutation.isPending}
      className="btn-secondary btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden="true"
      >
        <path d="M12 3v12" />
        <path d="m7 11 5 5 5-5" />
        <path d="M4 20h16" />
      </svg>
      {mutation.isPending ? 'Готовим файл…' : 'Выгрузить CSV'}
    </button>
  );
}

export function ExportNotice({ error }: { error: ExportError }) {
  if (isUpgradeError(error)) {
    return (
      <div
        role="status"
        className="flex items-start gap-3 border border-border-default bg-ivory-elevated px-5 py-4 mb-6"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden="true"
          className="mt-1 flex-shrink-0 text-slate"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5" />
          <path d="M12 8h.01" />
        </svg>
        <div>
          <p className="text-base font-semibold text-slate mb-1">{upgradeTitle(error)}</p>
          <p className="text-[15px] text-body-subtle">{error.message || UPGRADE_FALLBACK}</p>
          <Link href="/tariffs" className="btn-arrow mt-3">
            Посмотреть тарифы
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      role="alert"
      className="flex items-start gap-3 border border-clay bg-ivory-elevated px-5 py-4 mb-6"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden="true"
        className="mt-1 flex-shrink-0 text-clay-ember"
      >
        <path d="M12 4 2.5 20h19L12 4Z" />
        <path d="M12 10v4" />
        <path d="M12 17h.01" />
      </svg>
      <p className="text-[15px] text-clay-ember">{error.message}</p>
    </div>
  );
}
