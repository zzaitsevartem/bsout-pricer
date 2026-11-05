import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { SearchControls } from './lib';
import { CatalogSearchView } from './CatalogSearchView';

const { catalog, facets, offers, exportButton } = vi.hoisted(() => ({
  catalog: vi.fn(),
  facets: vi.fn(),
  offers: vi.fn(),
  exportButton: vi.fn(),
}));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('@/models/catalog', () => ({
  useCatalogSearch: catalog,
  useCatalogFacets: facets,
  useCatalogSuggestions: () => ({ data: [] }),
  useCatalogDevices: () => ({ data: [] }),
}));
vi.mock('@/models/product', () => ({ useProductSearch: offers }));
vi.mock('@/models/store', () => ({
  useStores: () => ({ data: [{ slug: 'liberti', name: 'Либерти', is_active: true }] }),
}));
vi.mock('@/models/export', () => ({ useExportCatalog: () => ({}) }));
vi.mock('@/widgets/CatalogExport/ui/CatalogExport', () => ({
  ExportCsvButton: (props: unknown) => {
    exportButton(props);
    return null;
  },
  ExportNotice: () => null,
}));
vi.mock('@/widgets/TrackButton/ui/TrackButton', () => ({
  TrackingButtonsProvider: ({ children }: { children: React.ReactNode }) => children,
}));
vi.mock('./CatalogResultCard', () => ({ CatalogResultCard: () => <span>Дисплей</span> }));

describe('catalog filtered requests', () => {
  it('passes offer filters to results, offers and export and uses filtered total for pagination', () => {
    facets.mockReturnValue({ data: { devices: [], part_types: [], quality_tiers: [] } });
    catalog.mockReturnValue({
      data: { results: [{ id: 1 }], total: 21, per_page: 20 },
      isLoading: false,
    });
    catalog.mockImplementation((params) => ({
      data: { results: [{ id: 1 }], total: 21, per_page: 20 },
      isLoading: false,
    }));
    offers.mockReturnValue({ data: { results: [], total: 0 }, isLoading: false });
    const controls: SearchControls = {
      onQueryChange: vi.fn(),
      onFilterChange: vi.fn(),
      onPriceChange: vi.fn(),
      onSortChange: vi.fn(),
      onPageChange: vi.fn(),
      onReset: vi.fn(),
    };
    render(
      <CatalogSearchView
        state={{
          q: 'дисплей',
          store: 'liberti',
          min_price: 0,
          max_price: 500,
          in_stock: false,
          sort_by: 'min_price_asc',
          page: 1,
        }}
        controls={controls}
      />,
    );
    const filters = { store: 'liberti', min_price: 0, max_price: 500, in_stock: false };
    expect(catalog).toHaveBeenCalledWith(expect.objectContaining({ ...filters, page: 1 }));
    expect(facets).toHaveBeenCalledWith(expect.objectContaining({ q: 'дисплей', store: 'liberti', min_price: 0, max_price: 500, in_stock: false }));
    expect(offers).toHaveBeenLastCalledWith(expect.objectContaining(filters), { enabled: false });
    fireEvent.click(screen.getByRole('button', { name: 'Показать предложения магазинов' }));
    expect(offers).toHaveBeenLastCalledWith(expect.objectContaining(filters), { enabled: true });
    fireEvent.click(screen.getByRole('button', { name: 'Скрыть предложения магазинов' }));
    expect(offers).toHaveBeenLastCalledWith(expect.objectContaining(filters), { enabled: false });
    expect(exportButton).toHaveBeenCalledWith(
      expect.objectContaining({ params: expect.objectContaining(filters) }),
    );
    expect(screen.getByText('Найдено: 21 товар')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument();
    expect(screen.getByLabelText('Магазин')).toHaveValue('liberti');
  });

  it('shows all quality options after the query changes', () => {
    catalog.mockReturnValue({ data: { results: [], total: 0, per_page: 20 }, isLoading: false });
    offers.mockReturnValue({ data: { results: [], total: 0 }, isLoading: false });
    facets.mockReturnValue({
      data: {
        devices: [],
        part_types: [],
        quality_tiers: [{ id: 1, label: 'OEM' }, { id: 2, label: 'Оригинал' }],
      },
    });
    const controls: SearchControls = {
      onQueryChange: vi.fn(), onFilterChange: vi.fn(), onPriceChange: vi.fn(),
      onSortChange: vi.fn(), onPageChange: vi.fn(), onReset: vi.fn(),
    };
    const state = { q: '', sort_by: 'min_price_asc' as const, page: 1 };
    const { rerender } = render(<CatalogSearchView state={state} controls={controls} />);
    rerender(<CatalogSearchView state={{ ...state, q: 'дисплей' }} controls={controls} />);
    expect(facets).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'дисплей' }));
    expect(screen.getByText('OEM')).toBeInTheDocument();
    expect(screen.getByText('Оригинал')).toBeInTheDocument();
  });
});

it('keeps visible All/category counts and distinguishes empty results from retry errors', () => {
  const refetch = vi.fn();
  catalog.mockReturnValue({ data: { results: [], total: 0 }, isLoading: false });
  facets.mockReturnValue({ data: { total: 23, devices: [], part_types: [{ id: 2, label: 'Камеры', count: 8 }], quality_tiers: [] } });
  offers.mockReturnValue({ data: { results: [], total: 0 } });
  const controls: SearchControls = { onQueryChange: vi.fn(), onFilterChange: vi.fn(), onPriceChange: vi.fn(), onSortChange: vi.fn(), onPageChange: vi.fn(), onReset: vi.fn() };
  const device = { id: 7, model_key: 'xiaomi', name: 'Redmi', brand: { id: 1, name: 'Xiaomi', slug: 'xiaomi' }, aliases: [], model_codes: [], images: [], release_year: null, metadata_source_url: null };
  const props = { device, state: { q: '', device_id: 7, part_type_id: 2, sort_by: 'min_price_asc' as const, page: 4 }, controls };
  const { rerender } = render(<CatalogSearchView {...props} />);
  expect(screen.getByRole('button', { name: 'Все 23' })).toBeVisible();
  expect(screen.getAllByRole('button', { name: 'Камеры 8', pressed: true })[0]).toHaveClass('btn-primary');
  fireEvent.click(screen.getByRole('button', { name: 'Все 23' }));
  expect(controls.onFilterChange).toHaveBeenCalledWith('part_type_id', null);
  expect(screen.getByText('Ничего не найдено')).toBeVisible();
  catalog.mockReturnValue({ isError: true, refetch });
  rerender(<CatalogSearchView {...props} />);
  fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
  expect(refetch).toHaveBeenCalledOnce();
  expect(screen.queryByText('Ничего не найдено')).not.toBeInTheDocument();
});
