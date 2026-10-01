import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { OfferResultCard } from './OfferResultCard';
import type { ProductResponse } from '@/models/product';

const offer: ProductResponse = {
  id: 16,
  store_id: 3,
  category_id: null,
  product_id: 1,
  source_sku: 'sku-1',
  title: 'Корпус Sony Xperia Z (черный) HIGH COPY',
  description: null,
  image_url: null,
  price_retail: '1560.00',
  price_opt: '1460.00',
  price_old: null,
  currency: 'RUB',
  stock_status: 'in_stock',
  stock_qty: null,
  url: 'https://liberti.ru/offer/1',
  last_seen_at: '2026-09-26T00:00:00Z',
  is_cheapest: true,
  store: { id: 3, name: 'Либерти', slug: 'liberti' },
};

describe('OfferResultCard', () => {
  it('renders title, store, prices and stock status', () => {
    render(<OfferResultCard item={offer} />);

    const link = screen.getByRole('link', { name: offer.title });
    expect(link).toHaveAttribute('href', 'https://liberti.ru/offer/1');
    expect(screen.getByText('Либерти')).toBeInTheDocument();
    expect(screen.getByText('1 560 ₽')).toBeInTheDocument();
    expect(screen.getByText('опт 1 460 ₽')).toBeInTheDocument();
    expect(screen.getByText('В наличии')).toBeInTheDocument();
  });

  it('renders without optional fields', () => {
    render(<OfferResultCard item={{ ...offer, price_opt: null, store: null }} />);

    expect(screen.getByText('Корпус Sony Xperia Z (черный) HIGH COPY')).toBeInTheDocument();
    expect(screen.queryByText('Либерти')).not.toBeInTheDocument();
  });
});
