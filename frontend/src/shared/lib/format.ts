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
