import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DeviceTracking } from './DeviceTracking';
import { AuthorizedHome } from './index';
const {
  plan,
  catalogDevices,
  catalogSuggestions,
  catalogApiDevices,
  trackedDevices,
  mutationError,
} = vi.hoisted(() => ({
  plan: { current: null as string | null },
  catalogDevices: vi.fn(() => ({
    data: [{ id: 2, label: 'iPhone 14', model_key: 'apple-iphone-14' }],
    isSuccess: true,
  })),
  catalogSuggestions: vi.fn(() => ({ data: [] })),
  catalogApiDevices: vi.fn(async () => ({
    data: [
      { id: 14, label: 'iPhone 14', model_key: 'apple-iphone-14' },
      { id: 15, label: 'iPhone 15', model_key: 'apple-iphone-15' },
    ],
  })),
  trackedDevices: {
    current: [{ id: 1, name: 'iPhone 15', brand: 'Apple', model_key: 'apple-iphone-15' }],
  },
  mutationError: { current: false },
}));
const { mutate, reset } = vi.hoisted(() => ({
  mutate: vi.fn(),
  reset: vi.fn(() => {
    mutationError.current = false;
  }),
}));
vi.mock('@/models/tracking', () => ({
  useTrackingUsage: () => ({ data: { plan: plan.current } }),
  useTrackedDevices: () => ({ data: trackedDevices.current }),
  useDeviceTrackingMutation: () => ({
    mutate,
    reset,
    isPending: false,
    isError: mutationError.current,
  }),
}));
vi.mock('@/models/catalog', () => ({
  useCatalogDevices: catalogDevices,
  useCatalogSuggestions: catalogSuggestions,
  catalogApi: { devices: catalogApiDevices },
}));
afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  trackedDevices.current = [
    { id: 1, name: 'iPhone 15', brand: 'Apple', model_key: 'apple-iphone-15' },
  ];
  mutationError.current = false;
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
describe('device tracking', () => {
  it('adds selected devices and links/removes tracked devices', async () => {
    render(<DeviceTracking />);
    const header = screen.getByText('Устройство').parentElement;
    const card = header?.parentElement;
    expect(header).toHaveClass('bg-slate', 'p-3', 'text-ivory');
    expect(card).toHaveClass('min-h-[340px]', 'gap-4', 'rounded-[24px]', 'bg-ivory-warm', 'p-6');
    expect(screen.getByText('Действие')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Apple iPhone 15' }).parentElement).toHaveClass(
      'min-h-[58px]',
      'bg-ivory',
      'p-3',
    );
    expect(card).not.toContainElement(screen.getByLabelText('Найти устройство'));
    expect(screen.getByRole('link', { name: 'Apple iPhone 15' })).toHaveAttribute(
      'href',
      '/devices/apple-iphone-15',
    );
    fireEvent.click(screen.getByRole('button', { name: /Удалить iPhone 15/ }));
    expect(screen.getByRole('dialog', { name: 'Перестать отслеживать?' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Отмена' }));
    expect(mutate).not.toHaveBeenCalled();
    const searchInput = screen.getByLabelText('Найти устройство');
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: 'iphone' } });
    fireEvent.click(await screen.findByRole('option', { name: /iPhone 14/ }));
    expect(mutate).toHaveBeenCalledWith({ id: 2 }, expect.any(Object));
  });

  it('cancels removal with Escape and confirms the selected device id', () => {
    render(<DeviceTracking />);
    const openDialog = () =>
      fireEvent.click(screen.getByRole('button', { name: /Удалить iPhone 15/ }));

    openDialog();
    let dialog = screen.getByRole('dialog', { name: 'Перестать отслеживать?' });
    fireEvent.keyDown(dialog, { key: 'Escape' });
    fireEvent(dialog, new Event('cancel', { bubbles: false, cancelable: true }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(mutate).not.toHaveBeenCalled();

    openDialog();
    dialog = screen.getByRole('dialog', { name: 'Перестать отслеживать?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить' }));
    expect(mutate).toHaveBeenCalledWith({ id: 1, remove: true }, expect.any(Object));
  });

  it('shows a removal error in the confirmation dialog', () => {
    const view = render(<DeviceTracking />);
    fireEvent.click(screen.getByRole('button', { name: /Удалить iPhone 15/ }));
    const dialog = screen.getByRole('dialog', { name: 'Перестать отслеживать?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить' }));
    mutationError.current = true;
    view.rerender(<DeviceTracking />);

    expect(screen.getByText('Не удалось удалить. Попробуйте ещё раз.')).toHaveAttribute(
      'role',
      'alert',
    );
  });

  it('asks the user to add the first device when none are tracked', () => {
    trackedDevices.current = [];
    render(<DeviceTracking />);

    expect(screen.getByText('Добавьте первое устройство')).toBeInTheDocument();
  });

  it.each(['click', 'keyboard'] as const)(
    'shows and selects a device suggestion by %s',
    (method) => {
      vi.useFakeTimers();
      render(<DeviceTracking />);
      const input = screen.getByRole('combobox', { name: 'Найти устройство' });
      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: 'iPhone' } });
      act(() => vi.advanceTimersByTime(200));

      expect(screen.getByRole('option', { name: /iPhone 14/ })).toBeInTheDocument();
      expect(catalogDevices).toHaveBeenLastCalledWith({ q: 'iPhone', limit: 6 }, { enabled: true });
      expect(catalogSuggestions).toHaveBeenLastCalledWith(
        { q: 'iPhone', limit: 6 },
        { enabled: false },
      );

      if (method === 'click') {
        fireEvent.click(screen.getByRole('option', { name: /iPhone 14/ }));
      } else {
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(screen.getByRole('option', { name: /iPhone 14/ })).toHaveAttribute(
          'aria-selected',
          'true',
        );
        fireEvent.keyDown(input, { key: 'Enter' });
      }

      expect(mutate).toHaveBeenCalledWith({ id: 2 }, expect.any(Object));
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    },
  );

  it.each(['click', 'keyboard'] as const)(
    'shows frequent devices on empty focus and selects the exact model by %s',
    async (method) => {
      render(<DeviceTracking />);
      const input = screen.getByRole('combobox', { name: 'Найти устройство' });
      fireEvent.focus(input);

      expect(screen.getByText('Часто ищут')).toBeInTheDocument();
      const option = screen.getByRole('option', { name: 'iPhone 15' });
      expect(option).toBeInTheDocument();

      if (method === 'click') {
        fireEvent.click(option);
      } else {
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(option).toHaveAttribute('aria-selected', 'true');
        fireEvent.keyDown(input, { key: 'Enter' });
      }

      await waitFor(() => expect(mutate).toHaveBeenCalledWith({ id: 15 }, expect.any(Object)));
      expect(catalogApiDevices).toHaveBeenCalledWith({ q: 'iPhone 15', limit: 8 });
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    },
  );

  it('shows an error when model suggestions cannot be loaded', () => {
    vi.useFakeTimers();
    catalogDevices.mockReturnValue({ data: undefined, isError: true });
    render(<DeviceTracking />);
    const input = screen.getByRole('combobox', { name: 'Найти устройство' });
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'iPhone' } });
    act(() => vi.advanceTimersByTime(200));

    expect(screen.getByRole('alert')).toHaveTextContent('Не удалось найти устройства.');
  });

  it('shows an error when a frequent model key cannot be resolved', async () => {
    catalogApiDevices.mockRejectedValueOnce(new Error('catalog unavailable'));
    render(<DeviceTracking />);
    fireEvent.focus(screen.getByRole('combobox', { name: 'Найти устройство' }));
    fireEvent.click(screen.getByRole('option', { name: 'iPhone 15' }));

    expect(
      await screen.findByText('Не удалось найти устройство. Попробуйте ещё раз.'),
    ).toBeInTheDocument();
    expect(mutate).not.toHaveBeenCalledWith({ id: 15 }, expect.any(Object));
  });
});

vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/user', () => ({ useMe: () => ({}) }));
vi.mock('@/models/notification', () => ({ useUnreadNotificationCount: () => ({}) }));
vi.mock('./AuthorizedHero', () => ({ AuthorizedHero: () => null }));
vi.mock('./TariffStrip', () => ({ TariffStrip: () => null }));
vi.mock('./TrackingOverview', () => ({ TrackingOverview: () => null }));
vi.mock('./QuickAccess', () => ({ QuickAccess: () => null }));
vi.mock('./NotificationsFeed', () => ({ NotificationsFeed: () => null }));

describe('authorized home device tracking visibility', () => {
  it.each(['basic', 'trial', null])('hides the block for %s', (value) => {
    plan.current = value;
    render(<AuthorizedHome />);
    expect(
      screen.queryByRole('region', { name: 'Отслеживание устройств' }),
    ).not.toBeInTheDocument();
  });
  it('shows the block for advanced', () => {
    plan.current = 'advanced';
    render(<AuthorizedHome />);
    expect(screen.getByRole('region', { name: 'Отслеживание устройств' })).toBeInTheDocument();
  });
});
