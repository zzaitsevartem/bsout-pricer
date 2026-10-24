import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SearchFilters } from './SearchFilters';

const state = {
  q: '',
  sort_by: 'min_price_asc' as const,
  page: 3,
  store: 'liberti',
  min_price: 100,
  max_price: 500,
  in_stock: false,
};
const facets = {
  devices: [],
  partTypes: [],
  qualityTiers: [],
  stores: [{ slug: 'liberti', name: 'Либерти' }],
};

describe('catalog offer filters', () => {
  it('restores values, changes stock, and applies the price range together', () => {
    const onFilterChange = vi.fn(),
      onPriceChange = vi.fn();
    render(
      <SearchFilters
        facets={facets}
        state={state}
        onFilterChange={onFilterChange}
        onPriceChange={onPriceChange}
        onReset={vi.fn()}
        hasActiveFilters
      />,
    );
    expect(screen.getByLabelText('Магазин')).toHaveValue('liberti');
    expect(screen.getByLabelText('Наличие')).toHaveValue('false');
    fireEvent.change(screen.getByLabelText('Наличие'), { target: { value: 'true' } });
    expect(onFilterChange).toHaveBeenCalledWith('in_stock', true);
    fireEvent.change(screen.getByLabelText('От'), { target: { value: '0' } });
    fireEvent.click(screen.getByRole('button', { name: 'Применить цену' }));
    expect(onPriceChange).toHaveBeenCalledWith(0, 500);
  });
  it('blocks an inverted range and allows correction', () => {
    const onPriceChange = vi.fn();
    render(
      <SearchFilters
        facets={facets}
        state={state}
        onFilterChange={vi.fn()}
        onPriceChange={onPriceChange}
        onReset={vi.fn()}
        hasActiveFilters
      />,
    );
    fireEvent.change(screen.getByLabelText('От'), { target: { value: '600' } });
    fireEvent.click(screen.getByRole('button', { name: 'Применить цену' }));
    expect(onPriceChange).not.toHaveBeenCalled();
    expect(screen.getByLabelText('До')).toBeInvalid();
    fireEvent.input(screen.getByLabelText('До'), { target: { value: '700' } });
    fireEvent.click(screen.getByRole('button', { name: 'Применить цену' }));
    expect(onPriceChange).toHaveBeenCalledWith(600, 700);
  });
});

describe('long device filters', () => {
  it('searches options while retaining the selected device', () => {
    const onFilterChange = vi.fn();
    render(
      <SearchFilters
        facets={{
          ...facets,
          devices: Array.from({ length: 30 }, (_, i) => ({ id: i + 1, label: `Device ${i + 1}` })),
        }}
        state={{ ...state, device_id: 2 }}
        onFilterChange={onFilterChange}
        onPriceChange={vi.fn()}
        onReset={vi.fn()}
        hasActiveFilters
      />,
    );
    fireEvent.change(screen.getByRole('searchbox', { name: 'Найти: устройство' }), {
      target: { value: 'Device 30' },
    });
    expect(screen.getByRole('button', { name: 'Device 2' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    expect(screen.queryByRole('button', { name: 'Device 3' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Device 30' }));
    expect(onFilterChange).toHaveBeenCalledWith('device_id', 30);
  });
});
