import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { CatalogItemResponse } from '@/models/catalog';
import { CatalogResultCard } from './CatalogResultCard';

vi.mock('@/widgets/TrackButton/ui/TrackButton', () => ({ TrackButton: () => null }));

const item: CatalogItemResponse = {
  id: 1, canonical_key: 'product', canonical_name: 'Дисплей', cluster_id: null,
  key_attrs: null, brand: null, device: null, part_type: null,
  quality_tier: { id: 1, code: 'original', name_ru: 'Оригинал', rank: 0 },
  min_price_retail: '100', min_price_opt: null, offers_count: 1, stores_count: 1,
  store_slugs: ['store'], stock_status: 'in_stock',
  source: { offer_id: 1, store_id: 1, store_name: 'Магазин', store_slug: 'store', url: 'https://store.example/offer' },
};

describe('CatalogResultCard', () => {
  it('links the price source to the matching offer in a safe new tab', () => {
    render(<CatalogResultCard item={item} />);
    const link = screen.getByRole('link', { name: /Магазин/ });
    expect(link).toHaveAttribute('href', 'https://store.example/offer');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'));
    expect(link).toHaveAttribute('rel', expect.stringContaining('noreferrer'));
  });

  it('shows an explicit fallback when the source is unavailable', () => {
    render(<CatalogResultCard item={{ ...item, source: null }} />);
    expect(screen.getByText('Источник недоступен')).toBeInTheDocument();
  });

  it('shows original and the available status as green text', () => {
    render(<CatalogResultCard item={item} />);
    expect(screen.getByText('Оригинал')).toHaveClass('text-brand-green');
    expect(screen.getByText('Оригинал')).not.toHaveClass('border');
    expect(screen.getByText('В наличии')).toHaveClass('text-brand-green');
    expect(screen.getByText('В наличии')).not.toHaveClass('border');
  });

  it('hides undefined quality and marks out of stock in red', () => {
    render(<CatalogResultCard item={{
      ...item, stock_status: 'out',
      quality_tier: { id: 2, code: 'unknown', name_ru: 'Не определено', rank: 9 },
    }} />);
    expect(screen.queryByText('Не определено')).not.toBeInTheDocument();
    expect(screen.getByText('Нет в наличии')).toHaveClass('text-stock-unavailable');
    expect(screen.getByText('Нет в наличии')).not.toHaveClass('border');
  });

  it('does not claim that unknown stock is out of stock', () => {
    render(<CatalogResultCard item={{ ...item, stock_status: 'unknown' }} />);
    expect(screen.queryByText('Наличие неизвестно')).not.toBeInTheDocument();
    expect(screen.queryByText('Нет в наличии')).not.toBeInTheDocument();
  });
});
