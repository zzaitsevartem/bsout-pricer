'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  useBroadcastRecipients,
  useBroadcasts,
  useCancelBroadcast,
  useCreateBroadcast,
  useDeleteBroadcast,
  useLaunchBroadcast,
  usePreviewBroadcast,
  useSendBroadcastTest,
  type BroadcastAudience,
  type BroadcastResponse,
  type BroadcastStatus,
  type RecipientStatus,
} from '@/models/admin';
import { useMe } from '@/models/user';
import { cn } from '@/shared/lib/utils';
import {
  BADGE_BASE,
  BADGE_DANGER,
  BADGE_DARK,
  BADGE_DEFAULT,
  BADGE_SUCCESS,
  BADGE_WARNING,
  TABLE,
  TABLE_HEAD_ROW,
  TABLE_TD,
  TABLE_TH,
  TABLE_WRAPPER,
  apiErrorMessage,
  formatDateTime,
  formatNumber,
} from '@/app/admin/_components/lib';

const AUDIENCE_LABELS: Record<BroadcastAudience, string> = {
  all_active: 'Все активные',
  verified: 'Подтверждённые',
  subscribers: 'Подписчики',
  custom: 'Список адресов',
};

const AUDIENCE_OPTIONS: Array<{ value: BroadcastAudience; label: string; description: string }> = [
  {
    value: 'custom',
    label: 'Конкретные адреса',
    description: 'Письмо придёт только на адреса, которые вы укажете ниже',
  },
  {
    value: 'all_active',
    label: 'Все активные пользователи',
    description: 'Все зарегистрированные активные аккаунты',
  },
  {
    value: 'verified',
    label: 'Подтверждённые пользователи',
    description: 'Только те, кто подтвердил свою почту',
  },
  {
    value: 'subscribers',
    label: 'Подписчики',
    description: 'Пользователи с активной подпиской',
  },
];

const STATUS_LABELS: Record<BroadcastStatus, string> = {
  draft: 'Черновик',
  queued: 'В очереди',
  running: 'Отправляется',
  completed: 'Завершена',
  failed: 'Ошибка',
  cancelled: 'Отменена',
};

function statusBadge(status: BroadcastStatus): string {
  const label = STATUS_LABELS[status];
  const tone =
    status === 'completed'
      ? BADGE_SUCCESS
      : status === 'failed'
        ? BADGE_DANGER
        : status === 'running' || status === 'queued'
          ? BADGE_WARNING
          : status === 'draft'
            ? BADGE_DEFAULT
            : BADGE_DARK;
  return cn(BADGE_BASE, tone);
}

const RECIPIENT_STATUS_LABELS: Record<RecipientStatus, string> = {
  pending: 'Ожидает',
  sending: 'Отправка',
  sent: 'Доставлено',
  failed: 'Ошибка',
};

const INPUT_CLASS =
  'w-full border border-border-default bg-ivory px-3 py-2.5 text-[15px] text-slate placeholder:text-body-muted hover:border-slate-soft focus:border-slate focus:outline-none transition-colors duration-150';

function Modal({
  onClose,
  children,
  maxWidth = 'max-w-[720px]',
}: {
  onClose: () => void;
  children: React.ReactNode;
  maxWidth?: string;
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = '';
      previous?.focus();
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-slate/50 px-4 pt-20 pb-8 backdrop-blur-[8px]"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        tabIndex={-1}
        className={cn(
          'w-full bg-ivory rounded-[16px] border border-slate shadow-[0_16px_40px_-12px_rgba(20,20,19,0.25)] max-h-[calc(100vh-112px)] overflow-hidden flex flex-col outline-none',
          maxWidth,
        )}
      >
        {children}
      </div>
    </div>
  );
}

function ModalHeader({ title, subtitle, onClose }: { title: string; subtitle?: string; onClose: () => void }) {
  return (
    <div className="flex items-start justify-between gap-4 px-6 py-5 border-b border-border-light-subtle">
      <div>
        <h3 className="text-xl font-semibold text-slate leading-none">{title}</h3>
        {subtitle && <p className="mt-1 text-[13px] text-body-muted">{subtitle}</p>}
      </div>
      <button
        type="button"
        onClick={onClose}
        aria-label="Закрыть"
        className="flex h-10 w-10 items-center justify-center rounded-full bg-ivory-elevated border border-border-light-subtle text-body-subtle transition-colors hover:bg-ivory-warm hover:text-slate"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

function BroadcastFormModal({
  onClose,
}: {
  onClose: () => void;
}) {
  const [name, setName] = useState('');
  const [audience, setAudience] = useState<BroadcastAudience>('custom');
  const [subject, setSubject] = useState('');
  const [text, setText] = useState('');
  const [emails, setEmails] = useState('');
  const [mode, setMode] = useState<'draft' | 'launch'>('draft');
  const [formError, setFormError] = useState<string | null>(null);

  const preview = usePreviewBroadcast();
  const create = useCreateBroadcast();
  const launch = useLaunchBroadcast();
  const createPending = create.isPending || launch.isPending;

  const recipients = emails
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  useEffect(() => {
    if (preview.data) {
      setFormError(null);
    }
  }, [preview.data]);

  const payload = (): Parameters<typeof create.mutate>[0] => ({
    name: name.trim(),
    audience,
    subject: subject.trim(),
    text,
    html: undefined,
    recipient_emails: audience === 'custom' ? recipients : undefined,
  });

  const handlePreview = () => {
    if (!name.trim() || !subject.trim() || !text.trim()) {
      setFormError('Заполните название, тему и текст письма');
      return;
    }
    if (audience === 'custom' && recipients.length === 0) {
      setFormError('Для аудитории «Список адресов» укажите хотя бы один email');
      return;
    }
    if (audience === 'custom' && recipients.some((email) => !email.includes('@'))) {
      setFormError('Проверьте введённые адреса — один из них похож на некорректный');
      return;
    }
    preview.mutate(payload());
  };

  const handleSubmit = () => {
    setFormError(null);
    if (!name.trim() || !subject.trim() || !text.trim()) {
      setFormError('Заполните название, тему и текст письма');
      return;
    }
    if (audience === 'custom' && recipients.length === 0) {
      setFormError('Для аудитории «Список адресов» укажите хотя бы один email');
      return;
    }
    if (mode === 'launch' && audience !== 'custom') {
      const ok = window.confirm(
        `Рассылка «${name.trim()}» пойдёт всем ${AUDIENCE_LABELS[audience]} (введённые адреса будут проигнорированы). Продолжить?`,
      );
      if (!ok) {
        return;
      }
    }
    create.mutate(payload(), {
      onSuccess: async (broadcast) => {
        if (mode === 'draft') {
          onClose();
          return;
        }
        launch.mutate(broadcast.id, {
          onSuccess: () => onClose(),
          onError: (error) => setFormError(apiErrorMessage(error, 'Не удалось запустить рассылку')),
        });
      },
      onError: (error) => setFormError(apiErrorMessage(error, 'Не удалось создать рассылку')),
    });
  };

  return (
    <Modal onClose={onClose} maxWidth="max-w-[720px]">
      <ModalHeader
        title="Новая рассылка"
        subtitle="Письмо будет отправлено от BScout.Pricer@yandex.ru"
        onClose={onClose}
      />
      <div className="flex-1 min-h-0 overflow-y-auto px-6 py-5 space-y-4">
        <div>
          <label htmlFor="broadcast-name" className="mb-2 block text-[15px] font-medium text-slate">
            Название
          </label>
          <input
            id="broadcast-name"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className={INPUT_CLASS}
            placeholder="Например: Анонс новой функции"
            maxLength={120}
          />
        </div>

        <div>
          <span className="mb-2 block text-[15px] font-medium text-slate">Кому отправить</span>
          <div className="space-y-2" role="radiogroup" aria-label="Кому отправить">
            {AUDIENCE_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={cn(
                  'flex cursor-pointer items-start gap-3 border px-4 py-3 transition-colors hover:bg-ivory-elevated',
                  audience === option.value
                    ? 'border-slate bg-ivory-elevated'
                    : 'border-border-default bg-ivory',
                )}
              >
                <input
                  type="radio"
                  name="broadcast-audience"
                  value={option.value}
                  checked={audience === option.value}
                  onChange={() => setAudience(option.value)}
                  className="mt-0.5 accent-slate"
                />
                <span>
                  <span className="block text-[15px] font-medium text-slate">{option.label}</span>
                  <span className="block text-[13px] text-body-subtle">{option.description}</span>
                </span>
              </label>
            ))}
          </div>
          <p className="mt-1.5 text-[14px] text-body-subtle">Получатели фиксируются при запуске.</p>
        </div>

        {audience === 'custom' && (
          <div>
            <label htmlFor="broadcast-emails" className="mb-2 block text-[15px] font-medium text-slate">
              Адреса получателей
            </label>
            <textarea
              id="broadcast-emails"
              value={emails}
              onChange={(event) => setEmails(event.target.value)}
              className={cn(INPUT_CLASS, 'min-h-[96px] resize-y')}
              placeholder={'user@example.com\npartner@example.com'}
            />
            <p className="mt-1.5 text-[14px] text-body-subtle">
              По одному адресу на строку. Максимум 500 адресов. Письмо уйдёт только этим адресам.
            </p>
          </div>
        )}

        {audience !== 'custom' && recipients.length > 0 && (
          <div className="border border-clay bg-ivory-elevated px-4 py-3">
            <p className="text-[14px] text-clay">
              Вы ввели адреса ранее, но выбрали «{AUDIENCE_LABELS[audience]}»: письмо уйдёт всем получателям этой аудитории, введённые адреса будут проигнорированы.
            </p>
            <button
              type="button"
              onClick={() => setAudience('custom')}
              className="mt-2 inline-flex items-center gap-1 p-0 text-[14px] font-medium text-clay normal-case bg-transparent border-0 underline underline-offset-[3px] cursor-pointer"
            >
              Отправить только введённые адреса
            </button>
          </div>
        )}

        <div>
          <label htmlFor="broadcast-subject" className="mb-2 block text-[15px] font-medium text-slate">
            Тема письма
          </label>
          <input
            id="broadcast-subject"
            type="text"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            className={INPUT_CLASS}
            placeholder="Тема сообщения"
            maxLength={200}
          />
        </div>

        <div>
          <label htmlFor="broadcast-text" className="mb-2 block text-[15px] font-medium text-slate">
            Текст письма
          </label>
          <textarea
            id="broadcast-text"
            value={text}
            onChange={(event) => setText(event.target.value)}
            className={cn(INPUT_CLASS, 'min-h-[160px] resize-y')}
            placeholder="Основной текст письма"
            maxLength={200000}
          />
        </div>

        {preview.data && (
          <div className="border border-border-default bg-ivory-elevated px-4 py-3">
            <p className="text-[15px] text-slate">
              Получателей: <span className="font-semibold">{formatNumber(preview.data.recipient_count)}</span>
            </p>
            {preview.data.sample_emails.length > 0 && (
              <p className="mt-1 text-[14px] text-body-subtle break-all">
                Например: {preview.data.sample_emails.join(', ')}
              </p>
            )}
          </div>
        )}

        {(formError || preview.error) && (
          <p className="text-[14px] text-clay">
            {formError ?? apiErrorMessage(preview.error, 'Не удалось получить предпросмотр')}
          </p>
        )}
      </div>
      <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-border-light-subtle">
        <button type="button" onClick={handlePreview} className="btn-ghost btn-sm" disabled={preview.isPending}>
          {preview.isPending ? 'Подсчёт…' : 'Предпросмотр'}
        </button>
        <div className="flex items-center gap-3">
          <button type="button" onClick={onClose} className="btn-ghost btn-sm" disabled={createPending}>
            Отмена
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('draft');
              handleSubmit();
            }}
            className="btn-secondary btn-sm"
            disabled={createPending}
          >
            {createPending && mode === 'draft' ? 'Сохранение…' : 'Сохранить черновик'}
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('launch');
              handleSubmit();
            }}
            className="btn-primary btn-sm"
            disabled={createPending}
          >
            {createPending && mode === 'launch' ? 'Запуск…' : 'Создать и запустить'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

const RECIPIENT_FILTERS: Array<{ value: RecipientStatus | ''; label: string }> = [
  { value: '', label: 'Все' },
  { value: 'pending', label: 'Ожидают' },
  { value: 'sending', label: 'Отправка' },
  { value: 'sent', label: 'Доставлено' },
  { value: 'failed', label: 'Ошибки' },
];

function BroadcastDetailModal({
  broadcast,
  onClose,
}: {
  broadcast: BroadcastResponse;
  onClose: () => void;
}) {
  const [filter, setFilter] = useState<RecipientStatus | ''>('');
  const [page, setPage] = useState(1);
  const recipients = useBroadcastRecipients(broadcast.id, filter || undefined, page, 20);
  const rows = recipients.data?.items ?? [];
  const total = recipients.data?.total ?? 0;
  const perPage = recipients.data?.per_page ?? 20;

  useEffect(() => {
    setPage(1);
  }, [filter]);

  const isLive = broadcast.status === 'running' || broadcast.status === 'queued';

  return (
    <Modal onClose={onClose} maxWidth="max-w-[960px]">
      <ModalHeader
        title={broadcast.name}
        subtitle={`Отправляется от BScout.Pricer · ${STATUS_LABELS[broadcast.status]}`}
        onClose={onClose}
      />
      <div className="flex-1 min-h-0 overflow-y-auto px-6 py-5 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className={statusBadge(broadcast.status)}>{STATUS_LABELS[broadcast.status]}</span>
          <span className="text-[14px] text-body-subtle">
            Получатели: <span className="font-semibold text-slate">{formatNumber(broadcast.total_recipients)}</span>
          </span>
          <span className="text-[14px] text-body-subtle">
            Отправлено: <span className="font-semibold text-slate">{formatNumber(broadcast.sent_count)}</span>
          </span>
          <span className="text-[14px] text-body-subtle">
            Ошибки: <span className="font-semibold text-slate">{formatNumber(broadcast.failed_count)}</span>
          </span>
          {isLive && (
            <span className="animate-pulse text-[14px] text-body-subtle">
              {broadcast.total_recipients > 0
                ? `${Math.round((broadcast.sent_count / broadcast.total_recipients) * 100)}%`
                : ''}
            </span>
          )}
        </div>
        {broadcast.error_summary && (
          <p className="text-[14px] text-clay">Ошибки: {broadcast.error_summary}</p>
        )}

        <div>
          <h4 className="mb-1 text-[15px] font-semibold text-slate">Тема</h4>
          <p className="text-[15px] text-body">{broadcast.subject}</p>
        </div>
        <div>
          <h4 className="mb-1 text-[15px] font-semibold text-slate">Текст письма</h4>
          <p className="text-[15px] text-body whitespace-pre-wrap">{broadcast.text}</p>
        </div>

        <div className="border-t border-border-light-subtle pt-4">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            {RECIPIENT_FILTERS.map(({ value, label }) => (
              <button
                key={value || 'all'}
                type="button"
                onClick={() => setFilter(value)}
                className={cn(
                  'rounded-full border px-3 py-1 text-[13px] transition-colors',
                  filter === value
                    ? 'border-slate bg-slate text-ivory'
                    : 'border-border-default bg-ivory text-body hover:bg-ivory-elevated',
                )}
              >
                {label}
              </button>
            ))}
          </div>

          <div className={TABLE_WRAPPER}>
            <table className={TABLE}>
              <thead>
                <tr className={TABLE_HEAD_ROW}>
                  <th className={TABLE_TH}>Email</th>
                  <th className={TABLE_TH}>Статус</th>
                  <th className={TABLE_TH}>Отправлено</th>
                  <th className={TABLE_TH}>Ошибка</th>
                </tr>
              </thead>
              <tbody>
                {recipients.isLoading ? (
                  <tr>
                    <td colSpan={4} className={cn(TABLE_TD, 'text-body-subtle')}>
                      Загрузка…
                    </td>
                  </tr>
                ) : recipients.isError ? (
                  <tr>
                    <td colSpan={4} className={cn(TABLE_TD, 'text-clay')}>
                      {apiErrorMessage(recipients.error, 'Не удалось загрузить получателей')}
                    </td>
                  </tr>
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={4} className={cn(TABLE_TD, 'text-body-subtle')}>
                      Получатели появятся после запуска рассылки
                    </td>
                  </tr>
                ) : (
                  rows.map((recipient) => (
                    <tr key={recipient.id}>
                      <td className={cn(TABLE_TD, 'text-body break-all')}>{recipient.email}</td>
                      <td className={TABLE_TD}>
                        <span className={cn(BADGE_BASE, recipient.status === 'sent' ? BADGE_SUCCESS : recipient.status === 'failed' ? BADGE_DANGER : recipient.status === 'sending' ? BADGE_WARNING : BADGE_DEFAULT)}>
                          {RECIPIENT_STATUS_LABELS[recipient.status]}
                        </span>
                      </td>
                      <td className={cn(TABLE_TD, 'text-[14px] text-body-subtle')}>
                        {formatDateTime(recipient.sent_at)}
                      </td>
                      <td className={cn(TABLE_TD, 'text-[14px] text-body-subtle')}>
                        {recipient.error ?? '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[14px] text-body-subtle">Всего: {formatNumber(total)}</span>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="btn-ghost btn-sm disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Назад
              </button>
              <span className="text-[14px] text-body-subtle">Стр. {page}</span>
              <button
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={page * perPage >= total}
                className="btn-ghost btn-sm disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Вперёд
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light-subtle">
        <button type="button" onClick={onClose} className="btn-primary btn-sm">
          Закрыть
        </button>
      </div>
    </Modal>
  );
}

export function MailingsSection() {
  const [showForm, setShowForm] = useState(false);
  const [detail, setDetail] = useState<BroadcastResponse | null>(null);
  const broadcasts = useBroadcasts(1, 20);
  const sendTest = useSendBroadcastTest();
  const launch = useLaunchBroadcast();
  const cancel = useCancelBroadcast();
  const deleteBroadcast = useDeleteBroadcast();

  const rows = broadcasts.data?.items ?? [];
  const mutationError = sendTest.error ?? launch.error ?? cancel.error ?? deleteBroadcast.error;
  const me = useMe();
  const adminEmail = me.data?.email;

  const handleSendTest = (broadcast: BroadcastResponse) => {
    const target = adminEmail ?? 'ваш адрес администратора';
    const ok = window.confirm(
      `Отправить тестовую версию «${broadcast.name}» только на ваш адрес (${target})? Получатели рассылки не затрагиваются.`,
    );
    if (!ok) {
      return;
    }
    sendTest.mutate({ id: broadcast.id, email: undefined });
  };

  const handleLaunch = (broadcast: BroadcastResponse) => {
    if (!window.confirm(`Запустить рассылку «${broadcast.name}»? Отправка начнётся автоматически.`)) {
      return;
    }
    launch.mutate(broadcast.id);
  };

  const handleCancel = (broadcast: BroadcastResponse) => {
    if (!window.confirm(`Отменить рассылку «${broadcast.name}»? Оставшиеся получатели не будут обработаны.`)) {
      return;
    }
    cancel.mutate(broadcast.id);
  };

  const handleDelete = (broadcast: BroadcastResponse) => {
    if (!window.confirm(`Удалить рассылку «${broadcast.name}»? Это действие необратимо.`)) {
      return;
    }
    deleteBroadcast.mutate(broadcast.id);
  };

  return (
    <section id="mailings">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-2xl font-semibold text-slate mb-0">Рассылки</h3>
          <p className="mt-1 text-[14px] text-body-subtle">
            Отправка выполняется фоном через воркер. Прогресс обновляется автоматически.
          </p>
        </div>
        <button type="button" onClick={() => setShowForm(true)} className="btn-primary btn-sm">
          Новая рассылка
        </button>
      </div>

      {mutationError && (
        <p className="mb-3 text-[14px] text-clay">
          {apiErrorMessage(mutationError, 'Не удалось выполнить операцию')}
        </p>
      )}

      <div className={TABLE_WRAPPER}>
        <table className={TABLE}>
          <thead>
            <tr className={TABLE_HEAD_ROW}>
              <th className={TABLE_TH}>ID</th>
              <th className={TABLE_TH}>Название</th>
              <th className={TABLE_TH}>Аудитория</th>
              <th className={TABLE_TH}>Статус</th>
              <th className={TABLE_TH}>Прогресс</th>
              <th className={TABLE_TH}>Создана</th>
              <th className={TABLE_TH}>Действия</th>
            </tr>
          </thead>
          <tbody>
            {broadcasts.isLoading ? (
              <tr>
                <td colSpan={7} className={cn(TABLE_TD, 'text-body-subtle')}>
                  Загрузка…
                </td>
              </tr>
            ) : broadcasts.isError ? (
              <tr>
                <td colSpan={7} className={cn(TABLE_TD, 'text-clay')}>
                  <span className="mr-3">
                    {apiErrorMessage(broadcasts.error, 'Не удалось загрузить рассылки')}
                  </span>
                  <button type="button" onClick={() => broadcasts.refetch()} className="btn-arrow">
                    Повторить
                  </button>
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={7} className={cn(TABLE_TD, 'text-body-subtle')}>
                  Рассылок пока нет — создайте первую
                </td>
              </tr>
            ) : (
              rows.map((broadcast) => (
                <tr key={broadcast.id}>
                  <td className={cn(TABLE_TD, 'font-montserrat text-[14px] text-body')}>
                    #{broadcast.id}
                  </td>
                  <td className={cn(TABLE_TD, 'font-semibold text-body')}>
                    <button type="button" onClick={() => setDetail(broadcast)} className="btn-arrow">
                      {broadcast.name}
                    </button>
                  </td>
                  <td className={cn(TABLE_TD, 'text-[14px] text-body-subtle')}>
                    {AUDIENCE_LABELS[broadcast.audience]}
                  </td>
                  <td className={TABLE_TD}>
                    <span className={statusBadge(broadcast.status)}>{STATUS_LABELS[broadcast.status]}</span>
                  </td>
                  <td className={cn(TABLE_TD, 'text-[14px] text-body-subtle')}>
                    {broadcast.total_recipients > 0
                      ? `${formatNumber(broadcast.sent_count)} / ${formatNumber(broadcast.total_recipients)}`
                      : '—'}
                  </td>
                  <td className={cn(TABLE_TD, 'text-[14px] text-body-subtle')}>
                    {formatDateTime(broadcast.created_at)}
                  </td>
                  <td className={TABLE_TD}>
                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        type="button"
                        onClick={() => setDetail(broadcast)}
                        className="btn-ghost btn-sm"
                      >
                        Детали
                      </button>
                      {(broadcast.status === 'draft' ||
                        broadcast.status === 'queued' ||
                        broadcast.status === 'running') && (
                        <button
                          type="button"
                          onClick={() => handleSendTest(broadcast)}
                          disabled={sendTest.isPending && sendTest.variables?.id === broadcast.id}
                          className="btn-ghost btn-sm disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {sendTest.isPending && sendTest.variables?.id === broadcast.id
                            ? 'Отправка…'
                            : 'Тест'}
                        </button>
                      )}
                      {broadcast.status === 'draft' && (
                        <button
                          type="button"
                          onClick={() => handleLaunch(broadcast)}
                          disabled={launch.isPending && launch.variables === broadcast.id}
                          className="btn-primary btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                          {launch.isPending && launch.variables === broadcast.id
                            ? 'Запуск…'
                            : 'Запустить'}
                        </button>
                      )}
                      {(broadcast.status === 'queued' || broadcast.status === 'running') && (
                        <button
                          type="button"
                          onClick={() => handleCancel(broadcast)}
                          disabled={cancel.isPending && cancel.variables === broadcast.id}
                          className="btn-ghost btn-sm text-clay disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {cancel.isPending && cancel.variables === broadcast.id
                            ? 'Отмена…'
                            : 'Отменить'}
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => handleDelete(broadcast)}
                        disabled={deleteBroadcast.isPending && deleteBroadcast.variables === broadcast.id}
                        className="btn-ghost btn-sm text-clay disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {deleteBroadcast.isPending && deleteBroadcast.variables === broadcast.id
                          ? 'Удаление…'
                          : 'Удалить'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showForm && <BroadcastFormModal onClose={() => setShowForm(false)} />}
      {detail && <BroadcastDetailModal broadcast={detail} onClose={() => setDetail(null)} />}
    </section>
  );
}