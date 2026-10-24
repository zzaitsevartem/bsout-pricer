import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { SearchControls } from './lib';
import { CatalogSearchView } from './CatalogSearchView';

const { catalog, offers, exportButton } = vi.hoisted(() => ({
  catalog: vi.fn(),
  offers: vi.fn(),
  exportButton: vi.fn(),
}));
vi.mock('@/models/catalog', () => ({
  useCatalogSearch: catalog,
  useCatalogSuggestions: () => ({ data: [] }),
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
    catalog.mockReturnValue({
      data: { results: [{ id: 1 }], total: 21, per_page: 20 },
      isLoading: false,
    });
    // Facet sampling is independent of the selected filters and needs dictionary-shaped rows.
    catalog.mockImplementation((params) => ({
      data: { results: params.per_page === 100 ? [] : [{ id: 1 }], total: 21, per_page: 20 },
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
});
