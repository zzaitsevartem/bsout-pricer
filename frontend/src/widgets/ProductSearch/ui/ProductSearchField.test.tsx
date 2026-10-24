import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { HeaderSearch } from '@/widgets/Header/ui/HeaderSearch';
import { AuthorizedHero } from '@/widgets/authorizedHome/ui/AuthorizedHero';

const { push, query, auth } = vi.hoisted(() => ({
  push: vi.fn(),
  query: vi.fn(),
  auth: { value: true },
}));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
vi.mock('effector-react', () => ({ useUnit: () => auth.value }));
vi.mock('@/models/catalog', () => ({ useCatalogSuggestions: query }));

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  auth.value = true;
});
describe('shared product search entry points', () => {
  it.each([
    ['header', () => <HeaderSearch />, 'Поиск запчастей'],
    ['home', () => <AuthorizedHero />, 'Артикул, название или бренд'],
  ] as const)('%s shows suggestions and navigates on keyboard selection', (_, component, label) => {
    vi.useFakeTimers();
    query.mockReturnValue({ data: [{ id: 1, canonical_name: 'Дисплей Nokia 5700' }] });
    render(component());
    const input = screen.getByRole('combobox', { name: label });
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Nokia' } });
    act(() => vi.advanceTimersByTime(200));
    expect(screen.getByRole('option', { name: 'Дисплей Nokia 5700' })).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith(`/search?q=${encodeURIComponent('Дисплей Nokia 5700')}`);
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
  it('keeps the header submit callback and clear action', () => {
    query.mockReturnValue({ data: [] });
    const onSubmitted = vi.fn();
    render(<HeaderSearch onSubmitted={onSubmitted} />);
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'Nokia' } });
    fireEvent.click(screen.getByRole('button', { name: 'Найти' }));
    expect(onSubmitted).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith('/search?q=Nokia');
    fireEvent.click(screen.getByRole('button', { name: 'Очистить поиск' }));
    expect(input).toHaveValue('');
  });
  it('does not request suggestions for logged-out visitors', () => {
    vi.useFakeTimers();
    auth.value = false;
    query.mockReturnValue({ data: [{ id: 1, canonical_name: 'Nokia' }] });
    render(<HeaderSearch />);
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Nokia' } });
    act(() => vi.advanceTimersByTime(200));
    expect(query).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'Nokia' }), {
      enabled: false,
    });
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
});
