import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TrackButton, TrackingButtonsProvider } from './TrackButton';
const { query, track, untrack } = vi.hoisted(() => ({
  query: vi.fn(),
  track: vi.fn(),
  untrack: vi.fn(),
}));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/tracking', () => ({
  useEveryTrackedProduct: query,
  useTrackProduct: () => ({ mutate: track, isPending: false }),
  useUntrackProduct: () => ({ mutate: untrack, isPending: false }),
  trackingGate: () => null,
}));
describe('shared catalog tracking state', () => {
  it('reads tracking once for multiple buttons and preserves track/untrack actions', () => {
    query.mockReturnValue({
      data: [
        { id: 42, product_id: 1, is_active: true },
        { id: 43, product_id: 2, is_active: false },
      ],
      isLoading: false,
    });
    render(
      <TrackingButtonsProvider>
        <TrackButton productId={1} />
        <TrackButton productId={2} />
        <TrackButton productId={3} />
      </TrackingButtonsProvider>,
    );
    expect(query).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: 'Отслеживается' }));
    expect(untrack).toHaveBeenCalledWith(42, expect.any(Object));
    fireEvent.click(screen.getAllByRole('button', { name: 'Отслеживать' })[0]);
    expect(track).toHaveBeenCalledWith({ product_id: 2 }, expect.any(Object));
  });
  it('still reads tracking when used outside a catalog provider', () => {
    query.mockClear();
    query.mockReturnValue({ data: [], isLoading: true });
    render(<TrackButton productId={4} />);
    expect(query).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Отслеживать' })).toBeDisabled();
  });
});
