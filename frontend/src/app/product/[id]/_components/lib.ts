import axios from 'axios';

export const BADGE_BASE =
  'inline-flex items-center text-xs font-montserrat uppercase tracking-[0.04em] px-2 py-0.5 border';
export const BADGE_SUCCESS = 'bg-[#EDF1E5] border-[#C7D2B0] text-[#4F5C36]';
export const BADGE_WARNING = 'bg-[#F4EBD7] border-[#E5D29B] text-[#4A3A12]';
export const BADGE_DANGER = 'bg-[#F8E5DD] border-[#E8B6A1] text-[#8E3F22]';
export const BADGE_INFO = 'bg-[#E6EEF7] border-[#B4CBE4] text-[#2F4A66]';
export const BADGE_DEFAULT = 'bg-ivory border-border-default text-slate';

export const CHIP =
  'inline-flex items-center text-[13px] px-2.5 py-1 bg-ivory-elevated border border-border-light text-body-subtle';

export const TABLE_WRAPPER = 'overflow-x-auto border border-slate bg-ivory';
export const TABLE = 'w-full border-collapse text-[15px]';
export const TABLE_HEAD_ROW = 'bg-ivory-elevated border-b border-slate';
export const TABLE_TH =
  'font-montserrat text-[13px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap';
export const TABLE_TD = 'px-4 py-[14px] border-b border-border-light-subtle align-middle';

export const DASH = '—';

export function parseMoney(value: string | null | undefined): number | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatMoneyValue(parsed: number | null | undefined): string {
  if (parsed === null || parsed === undefined || !Number.isFinite(parsed)) {
    return DASH;
  }
  const digits = Number.isInteger(parsed) ? 0 : 2;
  return `${parsed.toLocaleString('ru-RU', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })} ₽`;
}

export function formatMoney(value: string | null | undefined): string {
  return formatMoneyValue(parseMoney(value));
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return DASH;
  }
  return value.toLocaleString('ru-RU');
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return DASH;
  }
  const digits = Number.isInteger(value) ? 0 : 1;
  return `${value.toLocaleString('ru-RU', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}%`;
}

export function plural(count: number, one: string, few: string, many: string): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return one;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return few;
  }
  return many;
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) {
    return DASH;
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

export function formatDayShort(day: string | null | undefined): string {
  if (!day) {
    return DASH;
  }
  const date = new Date(day);
  if (Number.isNaN(date.getTime())) {
    return day;
  }
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
}

const STOCK_LABELS: Record<string, string> = {
  in_stock: 'В наличии',
  low: 'Мало',
  out: 'Нет в наличии',
  preorder: 'Под заказ',
  unknown: 'Неизвестно',
};

export function stockLabel(status: string): string {
  return STOCK_LABELS[status] ?? 'Неизвестно';
}

export function stockBadgeClass(status: string): string {
  if (status === 'in_stock') {
    return BADGE_SUCCESS;
  }
  if (status === 'low') {
    return BADGE_WARNING;
  }
  if (status === 'out') {
    return BADGE_DANGER;
  }
  if (status === 'preorder') {
    return BADGE_INFO;
  }
  return BADGE_DEFAULT;
}

export function apiErrorStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined;
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
  }
  return fallback;
}

export function parseProductId(raw: string | string[] | undefined): number | null {
  const value = Array.isArray(raw) ? raw[0] : raw;
  if (!value || !/^\d+$/.test(value)) {
    return null;
  }
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= 1 ? parsed : null;
}
