import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProductSearchField } from './ProductSearchField';
import { SearchInput } from '@/app/search/_components/SearchInput';
import { HeaderSearch } from '@/widgets/Header/ui/HeaderSearch';

const { push, devices } = vi.hoisted(() => ({ push: vi.fn(), devices: vi.fn() }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/catalog', () => ({
  useCatalogDevices: devices,
  useCatalogSuggestions: () => ({
    data: [{ id: 13, canonical_name: 'Дисплей iPhone 13' }],
  }),
}));

afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

function enableDevices() {
  devices.mockReturnValue({ data: [{ id: 7, label: 'iPhone 13', model_key: 'apple-iphone-13', count: 2 }] });
}

describe('device-first search', () => {
  it('offers devices before products and selects a model independently of its alias', () => {
    enableDevices();
    const onDeviceSelect = vi.fn();
    const onSelect = vi.fn();
    render(<ProductSearchField value="ip13" onValueChange={vi.fn()} onSelect={onSelect}
      onDeviceSelect={onDeviceSelect} label="Устройство" />);
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    expect(screen.getByText('Поиск по моделям')).toBeInTheDocument();
    expect(screen.getByText('Поиск по запчастям')).toBeInTheDocument();
    expect(screen.getAllByRole('option')[0]).toHaveTextContent('iPhone 13');
    expect(screen.getAllByRole('option')[1]).toHaveTextContent('Дисплей iPhone 13');
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onDeviceSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 7, label: 'iPhone 13' }));
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('clears alias text after selecting a model without a delayed stale query commit', () => {
    vi.useFakeTimers();
    enableDevices();
    const onDeviceSelect = vi.fn();
    const onQueryChange = vi.fn();
    render(<SearchInput query="ip13" onQueryChange={onQueryChange}
      onDeviceSelect={onDeviceSelect} suggestionsEnabled />);
    fireEvent.focus(screen.getByRole('combobox'));
    fireEvent.click(screen.getByRole('option', { name: /^iPhone 13/ }));
    expect(onDeviceSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 7 }));
    expect(screen.getByRole('combobox')).toHaveValue('');
    act(() => vi.advanceTimersByTime(600));
    expect(onQueryChange).not.toHaveBeenCalled();
  });

  it('navigates from the header with the stable model key and closes its containing menu', () => {
    vi.useFakeTimers();
    enableDevices();
    const onSubmitted = vi.fn();
    render(<HeaderSearch onSubmitted={onSubmitted} />);
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'айфон 13' } });
    act(() => vi.advanceTimersByTime(250));
    fireEvent.click(screen.getByRole('option', { name: /^iPhone 13/ }));
    expect(push).toHaveBeenCalledWith('/devices/apple-iphone-13');
    expect(onSubmitted).toHaveBeenCalledOnce();
    expect(input).toHaveValue('');
  });
});
