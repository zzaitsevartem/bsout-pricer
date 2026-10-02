import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';

import { server } from '@/test/msw/server';
import { ModerationSection } from './ModerationSection';

const offer = {
  id: 42,
  store_id: 1,
  source_sku: 'sku-42',
  title: 'Дисплей iPhone 13',
  normalized_title: 'дисплей iphone 13',
  price_retail: '3490.00',
  price_opt: null,
  price_old: null,
  currency: 'RUB',
  stock_status: 'in_stock',
  url: 'https://profi.ru/offer/42',
  image_url: null,
  is_active: true,
  product_id: null,
  match_status: 'pending',
  match_confidence: null,
  last_seen_at: '2026-10-01T00:00:00Z',
  store: { id: 1, name: 'Профи', slug: 'profi' },
};

const product = {
  id: 7,
  canonical_key: 'iphone-13',
  canonical_name: 'iPhone 13',
  cluster_id: null,
  brand_id: null,
  quality_tier_id: null,
  key_attrs: null,
};

const candidate = {
  id: 100,
  offer_id: offer.id,
  product_id: product.id,
  score: '0.92',
  features: null,
  status: 'pending',
  decided_by: null,
  decided_at: null,
  created_at: '2026-10-01T00:00:00Z',
  offer,
  product,
};

function listResponse(results: unknown[]) {
  return { results, total: results.length, page: 1, per_page: 20 };
}

function renderSection() {
  const client = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={client}>
      <ModerationSection />
    </QueryClientProvider>,
  );
}

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('ModerationSection', () => {
  it('renders pending candidates with offer, product and score', async () => {
    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([candidate])),
      ),
    );

    renderSection();

    expect(await screen.findByText('Дисплей iPhone 13')).toBeInTheDocument();
    expect(screen.getByText('iPhone 13')).toBeInTheDocument();
    expect(screen.getByText('92%')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Подтвердить' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Отклонить' })).toBeInTheDocument();
  });

  it('shows an empty state when there is nothing to moderate', async () => {
    server.use(http.get('*/api/admin/match-candidates', () => HttpResponse.json(listResponse([]))));

    renderSection();

    expect(await screen.findByText(/Кандидатов нет/)).toBeInTheDocument();
  });

  it('approves a candidate through the decision endpoint', async () => {
    const user = userEvent.setup();
    let approved: number | null = null;

    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([candidate])),
      ),
      http.post('*/api/admin/match-candidates/:id/approve', ({ params }) => {
        approved = Number(params.id);
        return HttpResponse.json({
          candidate: { ...candidate, status: 'approved' },
          offer: { id: offer.id, product_id: product.id, match_status: 'linked', match_confidence: 'high' },
          rejected_candidate_ids: [],
        });
      }),
    );

    renderSection();

    await user.click(await screen.findByRole('button', { name: 'Подтвердить' }));

    await waitFor(() => expect(approved).toBe(candidate.id));
  });

  it('rejects a candidate through the decision endpoint', async () => {
    const user = userEvent.setup();
    let rejected: number | null = null;

    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([candidate])),
      ),
      http.post('*/api/admin/match-candidates/:id/reject', ({ params }) => {
        rejected = Number(params.id);
        return HttpResponse.json({
          candidate: { ...candidate, status: 'rejected' },
          offer: { id: offer.id, product_id: null, match_status: 'rejected', match_confidence: null },
          rejected_candidate_ids: [],
        });
      }),
    );

    renderSection();

    await user.click(await screen.findByRole('button', { name: 'Отклонить' }));

    await waitFor(() => expect(rejected).toBe(candidate.id));
  });

  it('links an offer to a product only after a valid product id is entered', async () => {
    const user = userEvent.setup();
    let body: unknown = null;

    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([candidate])),
      ),
      http.post('*/api/admin/offers/:id/link', async ({ request, params }) => {
        body = await request.json();
        return HttpResponse.json({
          offer: { id: Number(params.id), product_id: product.id, match_status: 'linked', match_confidence: 'high' },
          rejected_candidate_ids: [],
        });
      }),
    );

    renderSection();

    const linkButton = await screen.findByRole('button', { name: 'Связать' });
    expect(linkButton).toBeDisabled();

    const input = screen.getByRole('spinbutton', { name: /ID товара/ });
    await user.type(input, '0');
    expect(linkButton).toBeDisabled();

    await user.clear(input);
    await user.type(input, '7');
    expect(linkButton).toBeEnabled();

    await user.click(linkButton);

    await waitFor(() => expect(body).toEqual({ product_id: 7 }));
  });

  it('unlinks an already linked offer', async () => {
    const user = userEvent.setup();
    let unlinked: number | null = null;

    const linkedCandidate = {
      ...candidate,
      status: 'approved',
      offer: { ...offer, product_id: product.id },
    };

    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([linkedCandidate])),
      ),
      http.post('*/api/admin/offers/:id/unlink', ({ params }) => {
        unlinked = Number(params.id);
        return HttpResponse.json({
          offer: { id: Number(params.id), product_id: null, match_status: 'pending', match_confidence: null },
          rejected_candidate_ids: [],
        });
      }),
    );

    renderSection();

    await user.click(await screen.findByRole('button', { name: 'Отвязать' }));

    await waitFor(() => expect(unlinked).toBe(offer.id));
  });

  it('does not offer link controls when the offer payload is missing', async () => {
    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([{ ...candidate, offer: null }])),
      ),
    );

    renderSection();

    expect(await screen.findByText('Оффер недоступен')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Связать' })).not.toBeInTheDocument();
  });

  it('surfaces the backend detail when a decision fails', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([candidate])),
      ),
      http.post('*/api/admin/match-candidates/:id/approve', () =>
        HttpResponse.json({ detail: 'Связка уже занята' }, { status: 409 }),
      ),
    );

    renderSection();

    await user.click(await screen.findByRole('button', { name: 'Подтвердить' }));

    expect(await screen.findByText('Связка уже занята')).toBeInTheDocument();
  });

  it('switches the status filter and refetches', async () => {
    const user = userEvent.setup();
    const statuses: (string | null)[] = [];

    server.use(
      http.get('*/api/admin/match-candidates', ({ request }) => {
        statuses.push(new URL(request.url).searchParams.get('status'));
        return HttpResponse.json(listResponse([{ ...candidate, status: 'rejected' }]));
      }),
    );

    renderSection();

    await screen.findByText('Дисплей iPhone 13');

    const filters = screen.getByRole('button', { name: 'Отклонены' });
    expect(filters).toHaveAttribute('aria-pressed', 'false');
    await user.click(filters);
    await waitFor(() => expect(filters).toHaveAttribute('aria-pressed', 'true'));

    expect(statuses).toContain('pending');
    expect(statuses).toContain('rejected');
  });

  it('paginates when the backend reports more than one page', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('*/api/admin/match-candidates', ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get('page'));
        return HttpResponse.json({
          results: [{ ...candidate, id: 100 + page }],
          total: 45,
          page,
          per_page: 20,
        });
      }),
    );

    renderSection();

    expect(await screen.findByText(/Страница 1 из 3/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Вперёд' }));

    expect(await screen.findByText(/Страница 2 из 3/)).toBeInTheDocument();
  });

  it('keeps the table readable when a row is missing its product', async () => {
    server.use(
      http.get('*/api/admin/match-candidates', () =>
        HttpResponse.json(listResponse([{ ...candidate, product: null }])),
      ),
    );

    renderSection();

    const row = (await screen.findByText('Дисплей iPhone 13')).closest('tr');
    expect(row).not.toBeNull();
    expect(within(row as HTMLElement).getAllByText('—').length).toBeGreaterThan(0);
  });
});
