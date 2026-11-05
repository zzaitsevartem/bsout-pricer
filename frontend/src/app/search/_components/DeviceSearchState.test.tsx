import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Device } from '@/models/device';
import type { SearchControls, SearchUrlState } from './lib';
import { SearchClient } from './SearchClient';

const { push, location } = vi.hoisted(() => ({
  push: vi.fn(),
  location: { pathname: '/devices/samsung-galaxy-s20', query: '' },
}));
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
  usePathname: () => location.pathname,
  useSearchParams: () => new URLSearchParams(location.query),
}));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('./CatalogSearchView', () => ({
  CatalogSearchView: ({ state, controls }: { state: SearchUrlState; controls: SearchControls }) => (
    <div>
      <output aria-label="Catalog state">{JSON.stringify(state)}</output>
      <button onClick={() => controls.onFilterChange('part_type_id', 2)}>Choose category</button>
      <button onClick={controls.onReset}>Reset filters</button>
    </div>
  ),
}));
const device: Device = {
  id: 31,
  model_key: 'samsung-galaxy-s20',
  name: 'Galaxy S20',
  brand: { id: 1, name: 'Samsung', slug: 'samsung' },
  aliases: [],
  model_codes: [],
  images: [],
  release_year: null,
  metadata_source_url: null,
};
const readState = () => JSON.parse(screen.getByLabelText('Catalog state').textContent!);
beforeEach(() => {
  push.mockClear();
  location.pathname = '/devices/samsung-galaxy-s20';
  location.query =
    'q=old&device_id=4&part_type_id=1&page=5&store=liberti&quality_tier_id=3&in_stock=true';
});

describe('device catalog URL state', () => {
  it('pushes category changes on the device route, resets page and removes stale search identity', () => {
    render(<SearchClient device={device} />);
    expect(readState()).toMatchObject({ device_id: 31, q: '', part_type_id: 1, page: 5 });
    fireEvent.click(screen.getByRole('button', { name: 'Choose category' }));
    expect(push).toHaveBeenCalledOnce();
    const url = new URL(push.mock.calls[0][0], 'https://bscout.test');
    expect(url.pathname).toBe('/devices/samsung-galaxy-s20');
    expect(url.searchParams.get('part_type_id')).toBe('2');
    expect(url.searchParams.get('store')).toBe('liberti');
    expect(url.searchParams.get('quality_tier_id')).toBe('3');
    expect(url.searchParams.get('in_stock')).toBe('true');
    for (const key of ['q', 'device_id', 'page']) expect(url.searchParams.has(key)).toBe(false);
    expect(push.mock.calls[0][1]).toEqual({ scroll: false });
  });

  it('restores category and page from URL navigation while using route device identity', () => {
    const { rerender } = render(<SearchClient device={device} />);
    location.query = 'part_type_id=2&page=3&store=profi';
    rerender(<SearchClient device={device} />);
    expect(readState()).toMatchObject({
      device_id: 31,
      part_type_id: 2,
      page: 3,
      store: 'profi',
      q: '',
    });
    // Simulates browser Back restoring the earlier category and pagination.
    location.query = 'part_type_id=1&page=5&device_id=4';
    rerender(<SearchClient device={device} />);
    expect(readState()).toMatchObject({ device_id: 31, part_type_id: 1, page: 5 });
    expect(push).not.toHaveBeenCalled();
  });

  it('resets filters without leaving the selected device route', () => {
    const { rerender } = render(<SearchClient device={device} />);
    fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }));
    expect(push).toHaveBeenCalledWith('/devices/samsung-galaxy-s20', { scroll: false });
    location.query = '';
    // Reloaded/direct links derive identity solely from the resolved device.
    rerender(<SearchClient device={device} />);
    expect(readState()).toMatchObject({ device_id: 31, page: 1, q: '' });
    expect(readState()).not.toHaveProperty('part_type_id');
    expect(readState()).not.toHaveProperty('store');
  });
});
