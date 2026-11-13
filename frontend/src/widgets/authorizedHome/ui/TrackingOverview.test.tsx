import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TrackingOverview } from './TrackingOverview';

const query = vi.hoisted(() => vi.fn());
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/tracking', () => ({
  useTrackedProducts: query,
  isTrackingGateStatus: () => false,
  trackingGate: () => null,
}));

describe('tracking overview', () => {
  it('links products and displays neutral, missing, rising and falling prices', () => {
    query.mockReturnValue({
      data: {
        total: 4,
        results: [
          { id: 1, product_id: 1, canonical_name: 'Ноль', price_delta: '0', current_price: '100' },
          { id: 2, product_id: 2, canonical_name: 'Нет', price_delta: null, current_price: null },
          { id: 3, product_id: 3, canonical_name: 'Рост', price_delta: '10', current_price: '110' },
          {
            id: 4,
            product_id: 4,
            canonical_name: 'Падение',
            price_delta: '-10',
            current_price: '90',
          },
        ],
      },
      isPending: false,
    });
    render(<TrackingOverview />);
    expect(screen.getByRole('link', { name: 'Ноль' })).toHaveAttribute('href', '/product/1');
    expect(screen.getByText('без изменений')).toHaveClass('text-body-muted');
    expect(screen.getByText('нет данных')).toHaveClass('text-body-muted');
    expect(screen.getByText(/\+10/)).toHaveClass('text-clay');
    expect(screen.getByText(/−10|-10/)).toHaveClass('text-olive');
  });
  it('does not claim prices are unchanged when the baseline is missing', () => {
    query.mockReturnValue({
      data: {
        total: 1,
        results: [
          {
            id: 5,
            product_id: 5,
            canonical_name: 'Без базовой цены',
            price_delta: null,
            current_price: '100',
          },
        ],
      },
      isPending: false,
    });
    render(<TrackingOverview />);
    expect(screen.getByText('нет данных для сравнения')).toHaveClass('text-body-muted');
  });
  it('reports request failures rather than an empty state', () => {
    query.mockReturnValue({ isPending: false, error: new Error('offline') });
    render(<TrackingOverview />);
    expect(screen.getByRole('alert')).toHaveTextContent('Не удалось загрузить');
  });
});
