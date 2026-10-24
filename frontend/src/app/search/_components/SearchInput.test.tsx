import { fireEvent, render, screen, act } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SearchInput } from './SearchInput';
const { suggestions } = vi.hoisted(() => ({
  suggestions: vi.fn(() => ({ data: [] as { id: number; canonical_name: string }[] })),
}));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/catalog', () => ({ useCatalogSuggestions: suggestions }));

afterEach(() => vi.useRealTimers());
describe('isolated search input', () => {
  it('keeps typing local and commits once after the debounce', () => {
    vi.useFakeTimers();
    const commit = vi.fn(),
      resultsRender = vi.fn();
    function Results() {
      resultsRender();
      return <span>Выдача</span>;
    }
    render(
      <>
        <SearchInput query="" onQueryChange={commit} />
        <Results />
      </>,
    );
    const input = screen.getByRole('searchbox');
    for (const value of ['i', 'ip', 'iphone']) fireEvent.change(input, { target: { value } });
    expect(commit).not.toHaveBeenCalled();
    expect(resultsRender).toHaveBeenCalledTimes(1);
    act(() => vi.advanceTimersByTime(349));
    expect(commit).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));
    expect(commit).toHaveBeenCalledTimes(1);
    expect(commit).toHaveBeenCalledWith('iphone');
  });
  it('submits immediately without a duplicate delayed request and restores external query', () => {
    vi.useFakeTimers();
    const commit = vi.fn();
    const view = render(<SearchInput query="iphone" onQueryChange={commit} />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'nokia' } });
    fireEvent.click(screen.getByRole('button', { name: 'Найти' }));
    act(() => vi.advanceTimersByTime(350));
    expect(commit).toHaveBeenCalledTimes(1);
    expect(commit).toHaveBeenCalledWith('nokia');
    view.rerender(<SearchInput query="samsung" onQueryChange={commit} />);
    expect(screen.getByRole('searchbox')).toHaveValue('samsung');
    act(() => vi.advanceTimersByTime(350));
    expect(commit).toHaveBeenCalledTimes(1);
  });
});

describe('catalog suggestions', () => {
  it('waits for focused debounced text, carries filters and supports keyboard selection', () => {
    vi.useFakeTimers();
    suggestions.mockReturnValue({
      data: [
        { id: 1, canonical_name: 'Дисплей Nokia 5700' },
        { id: 2, canonical_name: 'Микрофон Nokia 5700' },
      ],
    });
    const commit = vi.fn();
    render(
      <SearchInput
        query=""
        onQueryChange={commit}
        suggestionsEnabled
        filters={{ store: 'liberti', min_price: 0, in_stock: false }}
      />,
    );
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Nokia' } });
    expect(suggestions).toHaveBeenLastCalledWith(
      expect.objectContaining({ store: 'liberti', min_price: 0, in_stock: false }),
      { enabled: false },
    );
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    act(() => vi.advanceTimersByTime(200));
    expect(suggestions).toHaveBeenLastCalledWith(
      expect.objectContaining({ q: 'Nokia', limit: 6 }),
      { enabled: true },
    );
    expect(input).toHaveAttribute('aria-expanded', 'true');
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByRole('option', { name: 'Дисплей Nokia 5700' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(commit).toHaveBeenCalledWith('Дисплей Nokia 5700');
    expect(input).toHaveValue('Дисплей Nokia 5700');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    act(() => vi.advanceTimersByTime(350));
    expect(commit).toHaveBeenCalledTimes(1);
  });
  it('does not show suggestions after Escape or blur', () => {
    suggestions.mockReturnValue({ data: [{ id: 1, canonical_name: 'Дисплей Nokia' }] });
    render(<SearchInput query="Nokia" onQueryChange={vi.fn()} suggestionsEnabled />);
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    fireEvent.focus(input);
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    fireEvent.blur(input);
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
});
