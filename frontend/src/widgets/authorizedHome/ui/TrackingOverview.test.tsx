import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { TrackingOverview } from './TrackingOverview';

const { query, untrack } = vi.hoisted(() => ({
  query: vi.fn(),
  untrack: {
    mutate: vi.fn(),
    reset: vi.fn(),
    error: { current: false },
  },
}));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/tracking', () => ({
  useTrackedProducts: query,
  useUntrackProduct: () => ({
    mutate: untrack.mutate,
    reset: untrack.reset,
    isPending: false,
    isError: untrack.error.current,
  }),
  isTrackingGateStatus: () => false,
  trackingGate: () => null,
}));

afterEach(() => {
  vi.clearAllMocks();
  untrack.error.current = false;
});

beforeEach(() => {
  Object.defineProperty(HTMLDialogElement.prototype, 'showModal', {
    configurable: true,
    value() {
      this.setAttribute('open', '');
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, 'close', {
    configurable: true,
    value() {
      this.removeAttribute('open');
    },
  });
});

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
    for (const [name, color] of [
      ['Ноль', 'bg-slate'],
      ['Нет', 'bg-border-subtle'],
      ['Рост', 'bg-clay'],
      ['Падение', 'bg-olive'],
    ]) {
      const row = screen.getByRole('link', { name }).parentElement;
      expect(row?.querySelectorAll(`.${color}`)).toHaveLength(4);
    }
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

  it('cancels removal with the button or Escape and confirms the product id', () => {
    query.mockReturnValue({
      data: {
        total: 1,
        results: [
          {
            id: 81,
            product_id: 42,
            canonical_name: 'Дисплей iPhone 15',
            current_price: '100',
            price_delta: '0',
          },
        ],
      },
      isPending: false,
    });
    render(<TrackingOverview />);
    const openDialog = () =>
      fireEvent.click(screen.getByRole('button', { name: /Удалить Дисплей iPhone 15/ }));

    openDialog();
    let dialog = screen.getByRole('dialog', { name: 'Перестать отслеживать?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Отмена' }));
    expect(untrack.mutate).not.toHaveBeenCalled();

    openDialog();
    dialog = screen.getByRole('dialog', { name: 'Перестать отслеживать?' });
    fireEvent.keyDown(dialog, { key: 'Escape' });
    fireEvent(dialog, new Event('cancel', { bubbles: false, cancelable: true }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(untrack.mutate).not.toHaveBeenCalled();

    openDialog();
    dialog = screen.getByRole('dialog', { name: 'Перестать отслеживать?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить' }));
    expect(untrack.mutate).toHaveBeenCalledWith(81, expect.any(Object));
  });

  it('shows a removal error in the confirmation dialog', () => {
    query.mockReturnValue({
      data: {
        total: 1,
        results: [
          {
            id: 91,
            product_id: 42,
            canonical_name: 'Дисплей iPhone 15',
            current_price: '100',
            price_delta: '0',
          },
        ],
      },
      isPending: false,
    });
    const view = render(<TrackingOverview />);
    fireEvent.click(screen.getByRole('button', { name: /Удалить Дисплей iPhone 15/ }));
    const dialog = screen.getByRole('dialog', { name: 'Перестать отслеживать?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить' }));
    untrack.error.current = true;
    view.rerender(<TrackingOverview />);

    expect(screen.getByRole('alert')).toHaveTextContent('Не удалось удалить. Попробуйте ещё раз.');
  });
});
