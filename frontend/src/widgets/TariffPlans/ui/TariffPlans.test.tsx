import { describe, expect, it } from 'vitest';
import { planSchema } from '@/models/payment/schema';
import { planFeatures } from './TariffPlans';

describe('device tracking tariff feature', () => {
  it.each([
    ['trial', false],
    ['basic', false],
    ['advanced', true],
  ] as const)('parses and displays the server capability for %s', (plan, enabled) => {
    const parsed = planSchema.parse({
      plan,
      name_ru: plan,
      price: '0',
      first_payment_price: '0',
      currency: 'RUB',
      duration_days: 30,
      tracked_products: 10,
      stores: 5,
      fuzzy_search: false,
      price_alerts: false,
      device_tracking: enabled,
      export_reports: false,
      support_ru: '—',
      featured: false,
      sort_order: 0,
    });
    expect(planFeatures(parsed).includes('Отслеживание новых запчастей устройств')).toBe(enabled);
  });
});
