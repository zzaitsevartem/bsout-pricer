import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';

import { server } from '@/test/msw/server';
import { OfferImportSection } from './OfferImportSection';

const validRow = {
  store_slug: 'profi',
  source_sku: '12345',
  title: 'Дисплей iPhone 13',
  price_retail: '3490',
};

function renderSection() {
  const client = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={client}>
      <OfferImportSection />
    </QueryClientProvider>,
  );
}

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('OfferImportSection', () => {
  it('keeps the import button disabled until a valid payload is entered', async () => {
    const user = userEvent.setup();
    renderSection();

    const button = screen.getByRole('button', { name: /Импортировать/ });
    expect(button).toBeDisabled();

    await user.type(screen.getByLabelText('Данные офферов'), 'не json');
    expect(await screen.findByText(/Не удалось разобрать JSON/)).toBeInTheDocument();
    expect(button).toBeDisabled();
  });

  it('shows a row summary and enables import for a valid payload', async () => {
    const user = userEvent.setup();
    renderSection();

    await user.click(screen.getByLabelText('Данные офферов'));
    await user.paste(JSON.stringify([validRow]));

    expect(await screen.findByText('В файле строк: 1')).toBeInTheDocument();
    expect(screen.getByText('Готово к импорту: 1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Импортировать 1/ })).toBeEnabled();
  });

  it('imports the batch and renders the backend result', async () => {
    const user = userEvent.setup();
    let received: unknown = null;

    server.use(
      http.post('*/api/admin/offers/import', async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({
          total: 1,
          created: 1,
          updated: 0,
          skipped: 0,
          errors: [],
        });
      }),
    );

    renderSection();

    await user.click(screen.getByLabelText('Данные офферов'));
    await user.paste(JSON.stringify([validRow]));
    await user.click(await screen.findByRole('button', { name: /Импортировать 1/ }));

    expect(await screen.findByText('Создано: 1')).toBeInTheDocument();
    expect(screen.getByText('Обновлено: 0')).toBeInTheDocument();
    expect(received).toEqual([validRow]);
  });

  it('surfaces backend row errors', async () => {
    const user = userEvent.setup();

    server.use(
      http.post('*/api/admin/offers/import', () =>
        HttpResponse.json({
          total: 1,
          created: 0,
          updated: 0,
          skipped: 1,
          errors: [{ index: 0, reason: 'неизвестный store_slug', store_slug: 'nope', source_sku: null }],
        }),
      ),
    );

    renderSection();

    await user.click(screen.getByLabelText('Данные офферов'));
    await user.paste(JSON.stringify([validRow]));
    await user.click(await screen.findByRole('button', { name: /Импортировать 1/ }));

    expect(await screen.findByText(/неизвестный store_slug/)).toBeInTheDocument();
    expect(screen.getByText('Ошибок: 1')).toBeInTheDocument();
  });

  it('sends only the valid rows and lists the rejected ones', async () => {
    const user = userEvent.setup();
    let received: unknown = null;

    server.use(
      http.post('*/api/admin/offers/import', async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ total: 1, created: 1, updated: 0, skipped: 0, errors: [] });
      }),
    );

    renderSection();

    await user.click(screen.getByLabelText('Данные офферов'));
    await user.paste(JSON.stringify([validRow, { ...validRow, source_sku: '' }]));

    expect(await screen.findByText('Пропущено: 1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Импортировать 1/ })).toBeEnabled();

    await user.click(screen.getByRole('button', { name: /Импортировать 1/ }));

    await waitFor(() => expect(received).toEqual([validRow]));
  });

  it('shows an error message when the request fails', async () => {
    const user = userEvent.setup();

    server.use(
      http.post('*/api/admin/offers/import', () =>
        HttpResponse.json({ detail: 'Нет прав на импорт' }, { status: 403 }),
      ),
    );

    renderSection();

    await user.click(screen.getByLabelText('Данные офферов'));
    await user.paste(JSON.stringify([validRow]));
    await user.click(await screen.findByRole('button', { name: /Импортировать 1/ }));

    expect(await screen.findByText('Нет прав на импорт')).toBeInTheDocument();
  });
});
