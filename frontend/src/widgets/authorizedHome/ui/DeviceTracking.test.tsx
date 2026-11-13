import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DeviceTracking } from './DeviceTracking';
import { AuthorizedHome } from './index';
const plan = vi.hoisted(() => ({ current: null as string | null }));
const mutate = vi.hoisted(() => vi.fn());
vi.mock('@/models/tracking', () => ({
  useTrackingUsage: () => ({ data: { plan: plan.current } }),
  useTrackedDevices: () => ({
    data: [{ id: 1, name: 'iPhone 15', brand: 'Apple', model_key: 'apple-iphone-15' }],
  }),
  useDeviceTrackingMutation: () => ({ mutate, isPending: false }),
}));
vi.mock('@/models/catalog', () => ({
  useCatalogDevices: () => ({
    data: [{ id: 2, label: 'iPhone 14', model_key: 'apple-iphone-14' }],
  }),
}));
describe('device tracking', () => {
  it('adds selected devices and links/removes tracked devices', () => {
    render(<DeviceTracking />);
    expect(screen.getByRole('link', { name: 'Apple iPhone 15' })).toHaveAttribute(
      'href',
      '/devices/apple-iphone-15',
    );
    fireEvent.click(screen.getByRole('button', { name: /Удалить iPhone 15/ }));
    expect(mutate).toHaveBeenCalledWith({ id: 1, remove: true });
    fireEvent.change(screen.getByLabelText('Найти устройство'), { target: { value: 'iphone' } });
    fireEvent.click(screen.getByRole('button', { name: /iPhone 14 — добавить/ }));
    expect(mutate).toHaveBeenCalledWith({ id: 2 }, expect.any(Object));
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
