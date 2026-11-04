import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { server } from '@/test/msw/server';
import HistoryPage from './page';

vi.mock('@/widgets/Header/ui/Header', () => ({ Header: () => null }));
vi.mock('@/widgets/Footer/ui/Footer', () => ({ Footer: () => null }));
vi.mock('@/widgets/AccountSidebar/ui/AccountSidebar', () => ({ AccountSidebar: () => null }));
vi.mock('@/shared/lib/RequireAuth', () => ({
  RequireAuth: ({ children }: { children: React.ReactNode }) => children,
}));

const entry = {
  id: 1,
  user_id: 1,
  query: 'iPhone экран',
  filters: null,
  results_count: 3,
  created_at: '2026-11-03T10:00:00Z',
};
let entries = [entry];
let deletes = 0;
function mount() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <HistoryPage />
    </QueryClientProvider>,
  );
  return client;
}
async function openDialog() {
  await screen.findByText(entry.query);
  await userEvent.click(screen.getByRole('button', { name: 'Очистить всю историю' }));
  return screen.getByRole('dialog');
}

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
    this.setAttribute('open', '');
  });
  HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) {
    this.removeAttribute('open');
  });
});
beforeEach(() => {
  entries = [entry];
  deletes = 0;
  server.use(
    http.get('*/api/search/history', () => HttpResponse.json(entries)),
    http.delete('*/api/search/history', () => {
      deletes++;
      entries = [];
      return new HttpResponse(null, { status: 204 });
    }),
  );
});
afterEach(() => server.resetHandlers());
afterAll(() => {
  server.close();
  vi.restoreAllMocks();
});

describe('Clear search history', () => {
  it('opens a custom confirmation, cancel and Escape preserve history', async () => {
    mount();
    await openDialog();
    expect(deletes).toBe(0);
    expect(screen.getByRole('button', { name: 'Отмена' })).toHaveFocus();
    await userEvent.click(screen.getByRole('button', { name: 'Отмена' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    const dialog = await openDialog();
    fireEvent(dialog, new Event('cancel', { cancelable: true }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(deletes).toBe(0);
    expect(screen.getByText(entry.query)).toBeInTheDocument();
  });
  it('clears on confirmation and refreshes the shared query cache', async () => {
    const client = mount();
    await openDialog();
    await userEvent.click(screen.getByRole('button', { name: 'Да, очистить' }));
    await screen.findByText('История поиска пуста');
    expect(deletes).toBe(1);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(client.getQueryData(['search', 'history'])).toEqual([]);
    expect(screen.getByRole('button', { name: 'Очистить всю историю' })).toBeDisabled();
  });
  it('keeps history on failure and allows retry', async () => {
    server.use(http.delete('*/api/search/history', () => new HttpResponse(null, { status: 500 })));
    mount();
    await openDialog();
    await userEvent.click(screen.getByRole('button', { name: 'Да, очистить' }));
    await screen.findByRole('alert');
    expect(screen.getByText(entry.query)).toBeInTheDocument();
    server.use(
      http.delete('*/api/search/history', () => {
        entries = [];
        return new HttpResponse(null, { status: 204 });
      }),
    );
    await userEvent.click(screen.getByRole('button', { name: 'Да, очистить' }));
    await screen.findByText('История поиска пуста');
  });
  it('prevents duplicate requests and dismissing while pending', async () => {
    let complete!: () => void;
    server.use(
      http.delete('*/api/search/history', async () => {
        deletes++;
        await new Promise<void>((resolve) => {
          complete = resolve;
        });
        entries = [];
        return new HttpResponse(null, { status: 204 });
      }),
    );
    mount();
    const dialog = await openDialog();
    await userEvent.click(screen.getByRole('button', { name: 'Да, очистить' }));
    await waitFor(() => expect(deletes).toBe(1));
    expect(screen.getByRole('button', { name: 'Очищаем…' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Отмена' })).toBeDisabled();
    fireEvent(dialog, new Event('cancel', { cancelable: true }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    complete();
    await screen.findByText('История поиска пуста');
  });
});
