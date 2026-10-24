import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { SearchControls, SearchUrlState } from './lib';
import { SearchClient } from './SearchClient';
import { renderToString } from 'react-dom/server';
import { hydrateRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
  usePathname: () => '/search',
  useSearchParams: () =>
    new URLSearchParams('q=iphone&store=liberti&min_price=0&max_price=500&in_stock=false&page=3'),
}));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('./CatalogSearchView', () => ({
  CatalogSearchView: ({ state, controls }: { state: SearchUrlState; controls: SearchControls }) => (
    <div>
      <span>{JSON.stringify(state)}</span>
      <button onClick={() => controls.onFilterChange('store', 'profi')}>store</button>
      <button onClick={() => controls.onPriceChange(100, 300)}>price</button>
      <button onClick={() => controls.onReset()}>reset</button>
    </div>
  ),
}));
describe('search filter URL', () => {
  it('restores zero and false, resets page on changes and clears all filters', () => {
    render(<SearchClient />);
    expect(screen.getByText(/"min_price":0/)).toHaveTextContent('"in_stock":false');
    fireEvent.click(screen.getByText('store'));
    let url = new URL(replace.mock.calls.at(-1)![0], 'https://bscout.test');
    expect(url.searchParams.get('store')).toBe('profi');
    expect(url.searchParams.has('page')).toBe(false);
    expect(url.searchParams.get('in_stock')).toBe('false');
    fireEvent.click(screen.getByText('price'));
    url = new URL(replace.mock.calls.at(-1)![0], 'https://bscout.test');
    expect(url.searchParams.get('min_price')).toBe('100');
    expect(url.searchParams.get('max_price')).toBe('300');
    expect(url.searchParams.has('page')).toBe(false);
    fireEvent.click(screen.getByText('reset'));
    expect(replace.mock.calls.at(-1)![0]).toBe('/search?q=iphone');
  });
});

describe('search hydration', () => {
  it('hydrates the loading shell even when auth is already ready before hydration', async () => {
    const queryClient = new QueryClient();
    const app = (
      <QueryClientProvider client={queryClient}>
        <SearchClient />
      </QueryClientProvider>
    );
    const container = document.createElement('div');
    container.innerHTML = renderToString(app);
    expect(container.textContent).toContain('Загрузка');
    const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
    let root: ReturnType<typeof hydrateRoot>;
    try {
      await act(async () => {
        root = hydrateRoot(container, app);
      });
      expect(container.textContent).toContain('"in_stock":false');
      expect(
        errors.mock.calls.some((args) =>
          /hydration|did not match|server HTML/i.test(args.join(' ')),
        ),
      ).toBe(false);
    } finally {
      await act(async () => root?.unmount());
      errors.mockRestore();
    }
  });
});
