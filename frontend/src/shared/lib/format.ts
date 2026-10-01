type Plan = 'trial' | 'basic' | 'advanced';

const PLAN_LABELS: Record<Plan, string> = {
  trial: 'Пробный',
  basic: 'Базовый',
  advanced: 'Продвинутый',
};

const PLAN_PRICES: Record<Plan, string> = {
  trial: '0 ₽',
  basic: '399 ₽ / месяц',
  advanced: '499 ₽ / месяц',
};

export function planLabel(plan: Plan): string {
  return PLAN_LABELS[plan] ?? plan;
}

export function planPrice(plan: Plan): string {
  return PLAN_PRICES[plan] ?? '';
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

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

export function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return '—';
  }
  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}
