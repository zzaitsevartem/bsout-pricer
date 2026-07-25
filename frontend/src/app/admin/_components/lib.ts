import axios from 'axios';

export const BADGE_BASE = 'inline-flex items-center text-xs px-2 py-0.5 border';
export const BADGE_SUCCESS = 'bg-[#EDF1E5] border-[#C7D2B0] text-[#4F5C36]';
export const BADGE_WARNING = 'bg-[#F4EBD7] border-[#E5D29B] text-[#4A3A12]';
export const BADGE_DANGER = 'bg-[#F8E5DD] border-[#E8B6A1] text-[#8E3F22]';
export const BADGE_DARK = 'bg-slate text-ivory border-slate';
export const BADGE_DEFAULT = 'bg-ivory border-border-default text-slate';

export const TABLE_WRAPPER = 'overflow-x-auto border border-slate bg-ivory mb-8';
export const TABLE = 'w-full border-collapse text-[15px]';
export const TABLE_HEAD_ROW = 'bg-ivory-elevated border-b border-slate';
export const TABLE_TH =
  'font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap';
export const TABLE_TD = 'px-4 py-[14px] border-b border-border-light-subtle';

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
  }
  return fallback;
}

export function apiErrorStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined;
}

export function formatNumber(value: number): string {
  return value.toLocaleString('ru-RU');
}

export function formatDateTime(iso: string | null): string {
  if (!iso) {
    return '—';
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
