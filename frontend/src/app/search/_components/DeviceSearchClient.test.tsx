import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { SearchControls } from './lib';
import { SearchClient } from './SearchClient';

const { replace, location } = vi.hoisted(() => ({
  replace: vi.fn(),
  location: { query: '' },
}));
vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
  usePathname: () => '/search',
  useSearchParams: () => new URLSearchParams(location.query),
}));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('./CatalogSearchView', () => ({
  CatalogSearchView: ({ controls }: { controls: SearchControls }) => <div>
    <button onClick={() => controls.onFilterChange('device_id', 13)}>model</button>
    <button onClick={() => controls.onQueryChange('samsung a52')}>query</button>
    <button onClick={() => controls.onQueryChange('')}>submit unchanged</button>
    <button onClick={() => controls.onFilterChange('part_type_id', 2)}>category</button>
  </div>,
}));

beforeEach(() => {
  replace.mockClear();
  location.query = 'q=ip13&device_id=7&part_type_id=1&quality_tier_id=3&page=4&store=liberti&in_stock=true';
});

function changedParams() {
  return new URL(replace.mock.calls[0][0], 'http://localhost').searchParams;
}

describe('device search URL state', () => {
  it('selects a model, removing stale query and category while preserving offer constraints', () => {
    render(<SearchClient />);
    fireEvent.click(screen.getByText('model'));
    const params = changedParams();
    expect(params.get('device_id')).toBe('13');
    for (const key of ['q', 'part_type_id', 'quality_tier_id', 'page']) expect(params.has(key)).toBe(false);
    expect(params.get('store')).toBe('liberti');
    expect(params.get('in_stock')).toBe('true');
  });

  it('does not keep the old device when the user searches for another one', () => {
    render(<SearchClient />);
    fireEvent.click(screen.getByText('query'));
    const params = changedParams();
    expect(params.get('q')).toBe('samsung a52');
    for (const key of ['device_id', 'part_type_id', 'quality_tier_id', 'page']) expect(params.has(key)).toBe(false);
    expect(params.get('store')).toBe('liberti');
  });

  it('keeps the selected model when narrowing by part category', () => {
    render(<SearchClient />);
    fireEvent.click(screen.getByText('category'));
    const params = changedParams();
    expect(params.get('device_id')).toBe('7');
    expect(params.get('part_type_id')).toBe('2');
    expect(params.has('page')).toBe(false);
  });

  it('keeps a model-only search when submitting its unchanged empty text field', () => {
    location.query = 'device_id=13';
    render(<SearchClient />);
    fireEvent.click(screen.getByText('submit unchanged'));
    expect(replace).not.toHaveBeenCalled();
  });
});
