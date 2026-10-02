import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import { server } from '@/test/msw/server';
import { setAuth } from '@/shared/config/store';
import { AuthProvider } from '@/shared/providers/AuthProvider';
import { ThemeProvider } from '@/shared/providers/ThemeProvider';
import SubscriptionPage from './page';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/subscription',
}));

const subscription = {
  id: 5,
  user_id: 1,
  plan: 'basic',
  start_date: '2026-10-01',
  end_date: '2026-11-01',
  is_active: true,
  auto_renew: true,
};

const plan = {
  plan: 'basic',
  name_ru: 'Базовый',
  price: 490,
  first_payment_price: 490,
  currency: 'RUB',
  duration_days: 30,
  tracked_products: 10,
  stores: 5,
  fuzzy_search: false,
  price_alerts: true,
  export_reports: false,
  support_ru: 'email',
  featured: false,
  sort_order: 1,
};

function mockApi(usage: { used: number; limit: number; remaining: number }) {
  server.use(
    http.get('*/api/users/me', () =>
      HttpResponse.json({ id: 1, email: 'user@example.com', full_name: 'Иван', is_active: true }),
    ),
    http.get('*/api/notifications/unread-count', () => HttpResponse.json({ count: 0 })),
    http.get('*/api/users/me/subscription', () => HttpResponse.json(subscription)),
    http.get('*/api/payment/plans', () => HttpResponse.json([plan])),
    http.get('*/api/payment/history', () => HttpResponse.json([])),
    http.get('*/api/tracking/usage', () =>
      HttpResponse.json({ ...usage, plan: 'basic' }),
    ),
  );
}

function renderPage() {
  localStorage.setItem('access_token', 'test-access-token');
  localStorage.setItem('refresh_token', 'test-refresh-token');
  setAuth(true);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <AuthProvider>
          <SubscriptionPage />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('SubscriptionPage tracking usage', () => {
  it('shows the real counter instead of promising it for later', async () => {
    mockApi({ used: 3, limit: 10, remaining: 7 });

    renderPage();

    expect(await screen.findByText('Отслеживаемых товаров: 3 из 10')).toBeInTheDocument();
    expect(screen.queryByText(/появится позже/)).not.toBeInTheDocument();
  });

  it('falls back to the plan limit when usage is unavailable', async () => {
    mockApi({ used: 0, limit: 10, remaining: 10 });
    server.use(
      http.get('*/api/tracking/usage', () =>
        HttpResponse.json({ detail: 'Нет подписки' }, { status: 404 }),
      ),
    );

    renderPage();

    expect(await screen.findByText('Лимит отслеживаемых товаров: 10')).toBeInTheDocument();
    expect(screen.queryByText(/появится позже/)).not.toBeInTheDocument();
  });

  it('reports a full quota', async () => {
    mockApi({ used: 10, limit: 10, remaining: 0 });

    renderPage();

    expect(await screen.findByText('Отслеживаемых товаров: 10 из 10')).toBeInTheDocument();
  });
});
