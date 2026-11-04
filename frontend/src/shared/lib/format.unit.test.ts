import { describe, expect, it } from 'vitest';

import { formatDate, formatTariffAmount, initials, planLabel, planPrice } from './format';

describe('formatTariffAmount', () => {
  it('rounds fractional tariff prices and marks them as approximate', () => {
    expect(formatTariffAmount(319.2)).toBe('≈319');
    expect(formatTariffAmount(399.8)).toBe('≈400');
    expect(formatTariffAmount(399)).toBe('399');
    expect(formatTariffAmount(0)).toBe('0');
  });
});

describe('planLabel / planPrice', () => {
  it('maps known plans to Russian labels', () => {
    expect(planLabel('trial')).toBe('Пробный');
    expect(planLabel('basic')).toBe('Базовый');
    expect(planLabel('advanced')).toBe('Продвинутый');
  });

  it('maps known plans to prices', () => {
    expect(planPrice('trial')).toBe('0 ₽');
    expect(planPrice('basic')).toBe('399 ₽ / месяц');
    expect(planPrice('advanced')).toBe('499 ₽ / месяц');
  });
});

describe('formatDate', () => {
  it('formats an ISO date as dd.mm.yyyy', () => {
    expect(formatDate('2026-07-25T10:00:00Z')).toMatch(/^\d{2}\.\d{2}\.\d{4}$/);
  });

  it('returns the raw input for an unparseable date', () => {
    expect(formatDate('not-a-date')).toBe('not-a-date');
  });
});

describe('initials', () => {
  it('takes the first two name parts', () => {
    expect(initials('Ivan Petrov')).toBe('IP');
  });

  it('uppercases a single name', () => {
    expect(initials('ivan')).toBe('I');
  });

  it('collapses extra whitespace', () => {
    expect(initials('  Anna   Maria  Sidorova ')).toBe('AM');
  });

  it('returns a dash for an empty name', () => {
    expect(initials('   ')).toBe('—');
  });
});
