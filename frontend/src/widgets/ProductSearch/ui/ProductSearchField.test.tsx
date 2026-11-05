import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { HeaderSearch } from '@/widgets/Header/ui/HeaderSearch';
import { AuthorizedHero } from '@/widgets/authorizedHome/ui/AuthorizedHero';
import { ProductSearchField } from '@/widgets/ProductSearch/ui/ProductSearchField';

const { push, query, devices, auth } = vi.hoisted(() => ({
  push: vi.fn(),
  query: vi.fn(),
  devices: vi.fn(() => ({ data: [] })),
  auth: { value: true },
}));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
vi.mock('effector-react', () => ({ useUnit: () => auth.value }));
vi.mock('@/models/catalog', () => ({
  useCatalogSuggestions: query,
  useCatalogDevices: devices,
}));

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  auth.value = true;
});
describe('shared product search entry points', () => {
  it.each([true, false])('shows local frequent searches on empty focus (auth: %s)', (isAuth) => {
    auth.value = isAuth;
    query.mockReturnValue({ data: [] });
    render(<HeaderSearch />);
    fireEvent.focus(screen.getByRole('combobox'));
    expect(screen.getByText('Часто ищут')).toBeInTheDocument();
    expect(screen.getAllByRole('option').map((option) => option.textContent)).toEqual([
      'iPhone 15',
      'iPhone 14',
      'iPhone 13',
      'iPhone 12',
      'iPhone 11',
    ]);
    expect(query).toHaveBeenLastCalledWith(expect.objectContaining({ q: '' }), { enabled: false });
    expect(devices).toHaveBeenLastCalledWith(expect.objectContaining({ q: '' }), {
      enabled: false,
    });
  });

  it.each(
    ['header', 'home'].flatMap((host) =>
      [15, 14, 13, 12, 11].flatMap((model, index) =>
        ['click', 'keyboard'].map((method) => ({ host, model, index, method })),
      ),
    ),
  )('$host opens iPhone $model by $method', ({ host, model, index, method }) => {
    query.mockReturnValue({ data: [] });
    const onSubmitted = vi.fn();
    render(host === 'header' ? <HeaderSearch onSubmitted={onSubmitted} /> : <AuthorizedHero />);
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    if (method === 'click')
      fireEvent.click(screen.getByRole('option', { name: `iPhone ${model}` }));
    else {
      for (let i = 0; i <= index; i++) fireEvent.keyDown(input, { key: 'ArrowDown' });
      expect(screen.getByRole('option', { name: `iPhone ${model}` })).toHaveAttribute(
        'aria-selected',
        'true',
      );
      fireEvent.keyDown(input, { key: 'Enter' });
    }
    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith(`/devices/apple-iphone-${model}`);
    expect(onSubmitted).toHaveBeenCalledTimes(host === 'header' ? 1 : 0);
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('passes only label and model key to the frequent callback', () => {
    query.mockReturnValue({ data: [] });
    const onFrequentSelect = vi.fn();
    const onDeviceSelect = vi.fn();
    const onSelect = vi.fn();
    render(
      <ProductSearchField
        value=""
        onValueChange={vi.fn()}
        onSelect={onSelect}
        onDeviceSelect={onDeviceSelect}
        onFrequentSelect={onFrequentSelect}
        label="Search"
      />,
    );
    fireEvent.focus(screen.getByRole('combobox'));
    fireEvent.click(screen.getByRole('option', { name: 'iPhone 13' }));
    expect(onFrequentSelect).toHaveBeenCalledTimes(1);
    expect(onFrequentSelect).toHaveBeenCalledWith({
      label: 'iPhone 13',
      model_key: 'apple-iphone-13',
    });
    expect(onDeviceSelect).not.toHaveBeenCalled();
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('falls back to the text callback when no frequent callback is supplied', () => {
    query.mockReturnValue({ data: [] });
    const onSelect = vi.fn();
    const onDeviceSelect = vi.fn();
    render(
      <ProductSearchField
        value=""
        onValueChange={vi.fn()}
        onSelect={onSelect}
        onDeviceSelect={onDeviceSelect}
        label="Search"
      />,
    );
    fireEvent.focus(screen.getByRole('combobox'));
    fireEvent.click(screen.getByRole('option', { name: 'iPhone 13' }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith('iPhone 13');
    expect(onDeviceSelect).not.toHaveBeenCalled();
  });

  it('dismisses and reopens frequent searches, transitions on typing and clear', () => {
    vi.useFakeTimers();
    query.mockReturnValue({ data: [{ id: 1, canonical_name: 'Дисплей Nokia 5700' }] });
    render(<HeaderSearch />);
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    fireEvent.blur(input);
    fireEvent.focus(input);
    expect(screen.getByText('Часто ищут')).toBeInTheDocument();
    fireEvent.change(input, { target: { value: 'Nokia' } });
    expect(screen.queryByText('Часто ищут')).not.toBeInTheDocument();
    act(() => vi.advanceTimersByTime(200));
    expect(screen.getByRole('option', { name: 'Дисплей Nokia 5700' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Очистить поиск' }));
    expect(screen.getByText('Часто ищут')).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'Дисплей Nokia 5700' })).not.toBeInTheDocument();
    fireEvent.blur(input);
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('respects disabled suggestions for an empty field', () => {
    query.mockReturnValue({ data: [] });
    render(
      <ProductSearchField
        value=""
        onValueChange={vi.fn()}
        onSelect={vi.fn()}
        suggestionsEnabled={false}
        label="Search"
      />,
    );
    fireEvent.focus(screen.getByLabelText('Search'));
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    expect(query).toHaveBeenLastCalledWith(expect.objectContaining({ q: '' }), { enabled: false });
    expect(devices).toHaveBeenLastCalledWith(expect.objectContaining({ q: '' }), {
      enabled: false,
    });
  });

  it('displays a model-first non-Apple name but selects the canonical query', () => {
    vi.useFakeTimers();
    query.mockReturnValue({
      data: [
        {
          id: 1,
          canonical_name: 'Дисплей Samsung Galaxy A53 OLED',
          display_name: 'Samsung Galaxy A53 Дисплей OLED',
        },
      ],
    });
    render(<HeaderSearch />);
    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Samsung' } });
    act(() => vi.advanceTimersByTime(200));
    fireEvent.click(screen.getByRole('option', { name: 'Samsung Galaxy A53 Дисплей OLED' }));
    expect(push).toHaveBeenCalledWith(
      `/search?q=${encodeURIComponent('Дисплей Samsung Galaxy A53 OLED')}`,
    );
  });
  it.each([
    ['header', () => <HeaderSearch />, 'Поиск запчастей'],
    ['home', () => <AuthorizedHero />, 'Модель устройства, артикул или запчасть'],
  ] as const)('%s shows suggestions and navigates on keyboard selection', (_, component, label) => {
    vi.useFakeTimers();
    query.mockReturnValue({ data: [{ id: 1, canonical_name: 'Дисплей Nokia 5700' }] });
    render(component());
    const input = screen.getByRole('combobox', { name: label });
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Nokia' } });
    act(() => vi.advanceTimersByTime(200));
    expect(screen.getByRole('option', { name: 'Дисплей Nokia 5700' })).toBeInTheDocument();
    expect(screen.getByText('Nokia', { selector: 'strong' })).toBeInTheDocument();
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
