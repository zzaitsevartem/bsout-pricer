'use client';

import React from 'react';
import {
  useApproveMatchCandidate,
  useLinkOffer,
  useMatchCandidates,
  useRejectMatchCandidate,
  useUnlinkOffer,
  type MatchCandidateResponse,
  type MatchCandidateStatusFilter,
} from '@/models/admin';
import { cn } from '@/shared/lib/utils';
import {
  BADGE_BASE,
  BADGE_DANGER,
  BADGE_SUCCESS,
  BADGE_WARNING,
  TABLE,
  TABLE_HEAD_ROW,
  TABLE_TD,
  TABLE_TH,
  TABLE_WRAPPER,
  apiErrorMessage,
  formatDateTime,
} from '@/app/admin/_components/lib';

const COLUMNS = ['Оффер', 'Товар', 'Совпадение', 'Статус', 'Решено', 'Действия'];
const PAGE_SIZE = 20;

const STATUS_FILTERS: { value: MatchCandidateStatusFilter; label: string }[] = [
  { value: 'pending', label: 'Ожидают' },
  { value: 'approved', label: 'Подтверждены' },
  { value: 'rejected', label: 'Отклонены' },
  { value: 'all', label: 'Все' },
];

function scorePercent(score: string): string {
  const value = Number(score);
  if (!Number.isFinite(value)) {
    return '—';
  }
  const percent = value <= 1 ? value * 100 : value;
  return `${percent.toFixed(0)}%`;
}

function scoreBadge(score: string) {
  const value = Number(score);
  const percent = Number.isFinite(value) ? (value <= 1 ? value * 100 : value) : 0;
  if (percent >= 80) {
    return { label: scorePercent(score), className: BADGE_SUCCESS };
  }
  if (percent >= 50) {
    return { label: scorePercent(score), className: BADGE_WARNING };
  }
  return { label: scorePercent(score), className: BADGE_DANGER };
}

function statusBadge(status: string) {
  if (status === 'approved') {
    return { label: 'Подтверждена', className: BADGE_SUCCESS };
  }
  if (status === 'rejected') {
    return { label: 'Отклонена', className: BADGE_DANGER };
  }
  return { label: 'Ожидает', className: BADGE_WARNING };
}

function CandidateRow({
  candidate,
  busy,
  onApprove,
  onReject,
  onLink,
  onUnlink,
}: {
  candidate: MatchCandidateResponse;
  busy: boolean;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  onLink: (offerId: number, productId: number) => void;
  onUnlink: (offerId: number) => void;
}) {
  const [linkValue, setLinkValue] = React.useState('');
  const productId = Number(linkValue);
  const canLink = Number.isInteger(productId) && productId > 0 && !busy;

  const status = statusBadge(candidate.status);
  const score = scoreBadge(candidate.score);
  const offerId = candidate.offer?.id;
  const linked = candidate.offer?.product_id != null;

  return (
    <tr>
      <td className={TABLE_TD}>
        <div className="font-semibold text-body">{candidate.offer?.title ?? '—'}</div>
        <div className="text-[13px] text-body-subtle">
          {candidate.offer?.store?.name ?? candidate.offer?.store?.slug ?? '—'}
          {candidate.offer?.source_sku ? ` · ${candidate.offer.source_sku}` : ''}
        </div>
      </td>
      <td className={TABLE_TD}>
        <div className="text-body">{candidate.product?.canonical_name ?? '—'}</div>
        <div className="text-[13px] text-body-subtle font-mono">
          {candidate.product?.canonical_key ?? '—'}
        </div>
      </td>
      <td className={TABLE_TD}>
        <span className={cn(BADGE_BASE, score.className)}>{score.label}</span>
      </td>
      <td className={TABLE_TD}>
        <span className={cn(BADGE_BASE, status.className)}>{status.label}</span>
      </td>
      <td className={cn(TABLE_TD, 'text-[13px] text-body-subtle')}>
        {candidate.decided_at ? formatDateTime(candidate.decided_at) : '—'}
      </td>
      <td className={TABLE_TD}>
        <div className="flex items-center gap-2 flex-wrap">
          {candidate.status === 'pending' && (
            <>
              <button
                type="button"
                onClick={() => onApprove(candidate.id)}
                disabled={busy}
                className="btn-primary btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Подтвердить
              </button>
              <button
                type="button"
                onClick={() => onReject(candidate.id)}
                disabled={busy}
                className="btn-ghost btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Отклонить
              </button>
            </>
          )}
          {offerId === undefined ? (
            <span className="text-[13px] text-body-subtle">Оффер недоступен</span>
          ) : linked ? (
            <button
              type="button"
              onClick={() => onUnlink(offerId)}
              disabled={busy}
              className="btn-ghost btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
            >
              Отвязать
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={1}
                value={linkValue}
                onChange={(event) => setLinkValue(event.target.value)}
                placeholder="ID товара"
                aria-label={`ID товара для связывания с оффером ${candidate.offer?.source_sku ?? candidate.id}`}
                className="w-[100px] rounded-full px-3 py-[6px] text-[14px] text-slate bg-ivory border border-border-input transition-colors focus:outline-none focus:border-border-default disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => onLink(offerId, productId)}
                disabled={!canLink}
                className="btn-secondary btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Связать
              </button>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

export function ModerationSection() {
  const [status, setStatus] = React.useState<MatchCandidateStatusFilter>('pending');
  const [page, setPage] = React.useState(1);

  const candidates = useMatchCandidates({ status, page, per_page: PAGE_SIZE });
  const approve = useApproveMatchCandidate();
  const reject = useRejectMatchCandidate();
  const link = useLinkOffer();
  const unlink = useUnlinkOffer();

  const busy = approve.isPending || reject.isPending || link.isPending || unlink.isPending;
  const list = candidates.data;
  const rows = list?.results ?? [];
  const totalPages = list ? Math.max(1, Math.ceil(list.total / (list.per_page || PAGE_SIZE))) : 1;

  const mutationError = approve.error ?? reject.error ?? link.error ?? unlink.error;

  return (
    <section id="moderation">
      <div className="flex justify-between items-center mb-4 flex-wrap gap-3">
        <div>
          <h3 className="text-2xl font-semibold text-slate mb-0">Модерация связок</h3>
          <p className="text-[15px] text-body-subtle mb-0 mt-1">
            Кандидаты матчинга, которые ждут решения.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              onClick={() => {
                setStatus(filter.value);
                setPage(1);
              }}
              aria-pressed={status === filter.value}
              className={cn(
                'rounded-full px-3 py-1 text-[14px] border transition-colors',
                status === filter.value
                  ? 'bg-slate text-ivory border-slate'
                  : 'bg-ivory text-body border-border-default hover:bg-ivory-elevated',
              )}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {candidates.isLoading ? (
        <p className="text-[15px] text-body-subtle">Загрузка…</p>
      ) : candidates.isError ? (
        <p className="text-[14px] text-clay mb-4">
          <span className="mr-3">
            {apiErrorMessage(candidates.error, 'Не удалось загрузить кандидатов')}
          </span>
          <button type="button" onClick={() => candidates.refetch()} className="btn-arrow">
            Повторить
          </button>
        </p>
      ) : rows.length === 0 ? (
        <div className={cn(TABLE_WRAPPER, 'mb-8')}>
          <table className={TABLE}>
            <tbody>
              <tr>
                <td className={cn(TABLE_TD, 'text-body-subtle')}>
                  {status === 'pending'
                    ? 'Кандидатов нет — всё разобрано'
                    : 'По этому фильтру кандидатов нет'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ) : (
        <>
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
                {rows.map((candidate) => (
                  <CandidateRow
                    key={candidate.id}
                    candidate={candidate}
                    busy={busy}
                    onApprove={(id) => approve.mutate(id)}
                    onReject={(id) => reject.mutate(id)}
                    onLink={(offerId, productId) => link.mutate({ offerId, data: { product_id: productId } })}
                    onUnlink={(offerId) => unlink.mutate(offerId)}
                  />
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center gap-3 mb-8">
              <button
                type="button"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1}
                className="btn-ghost btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Назад
              </button>
              <span className="text-[14px] text-body-subtle">
                Страница {page} из {totalPages} · всего {list?.total ?? 0}
              </span>
              <button
                type="button"
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={page >= totalPages}
                className="btn-ghost btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Вперёд
              </button>
            </div>
          )}
        </>
      )}

      {mutationError !== null && mutationError !== undefined && (
        <p className="text-[14px] text-clay mb-3">
          {apiErrorMessage(mutationError, 'Не удалось применить решение по связке')}
        </p>
      )}
    </section>
  );
}
