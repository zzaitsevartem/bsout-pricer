import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Header } from './Header';

const state = vi.hoisted(() => ({ authenticated: false, pathname: '/', push: vi.fn() }));
vi.mock('next/navigation', () => ({
  usePathname: () => state.pathname,
  useRouter: () => ({ push: state.push }),
}));
vi.mock('effector-react', () => ({ useUnit: () => state.authenticated }));
vi.mock('@/models/user', () => ({ useMe: () => ({}) }));
vi.mock('@/models/auth', () => ({ useLogout: () => ({ mutate: vi.fn() }) }));
vi.mock('@/models/notification', () => ({ useUnreadNotificationCount: () => ({}) }));
vi.mock('./ThemeToggle', () => ({ ThemeToggle: () => null }));
vi.mock('./UserMenu', () => ({ UserMenu: () => null }));
vi.mock('@/widgets/ProductSearch/ui/ProductSearchField', () => ({
  ProductSearchField: ({
    id,
    value,
    onValueChange,
    onSelect,
    onDeviceSelect,
    onFrequentSelect,
  }: {
    id: string;
    value: string;
    onValueChange: (value: string) => void;
    onSelect: (value: string) => void;
    onDeviceSelect: (device: { model_key: string }) => void;
    onFrequentSelect: (device: { model_key: string }) => void;
  }) => (
    <>
      <input id={id} value={value} onChange={(event) => onValueChange(event.target.value)} />
      <button type="button" onClick={() => onSelect('дисплей')}>
        Текстовая подсказка
      </button>
      <button type="button" onClick={() => onDeviceSelect({ model_key: 'iphone-13' })}>
        Устройство
      </button>
      <button type="button" onClick={() => onFrequentSelect({ model_key: 'iphone-13' })}>
        Частое устройство
      </button>
    </>
  ),
}));

beforeEach(() => {
  state.authenticated = false;
  state.pathname = '/';
  state.push.mockReset();
});

describe('header search routing', () => {
  it('directs a guest search on the homepage to registration, including mobile entry', () => {
    render(<Header />);
    fireEvent.change(screen.getAllByLabelText('Поиск запчастей', { selector: 'input' })[0], {
      target: { value: 'iPhone 13' },
    });
    fireEvent.submit(screen.getAllByRole('search', { hidden: true })[0]);
    expect(state.push).toHaveBeenCalledWith('/register');
    expect(screen.getByRole('link', { name: 'Поиск запчастей' })).toHaveAttribute(
      'href',
      '/register',
    );
  });

  it('preserves authenticated query search', () => {
    state.authenticated = true;
    render(<Header />);
    fireEvent.change(screen.getAllByLabelText('Поиск запчастей', { selector: 'input' })[0], {
      target: { value: 'iPhone 13' },
    });
    fireEvent.submit(screen.getAllByRole('search', { hidden: true })[0]);
    expect(state.push).toHaveBeenCalledWith('/search?q=iPhone%2013');
    expect(screen.getByRole('link', { name: 'Поиск запчастей' })).toHaveAttribute(
      'href',
      '/search',
    );
  });

  it('submits mobile menu search to registration', () => {
    render(<Header />);
    fireEvent.click(screen.getByRole('button', { name: 'Открыть меню' }));
    const forms = screen.getAllByRole('search');
    const mobileForm = forms[forms.length - 1];
    fireEvent.change(within(mobileForm).getByLabelText('Поиск запчастей'), {
      target: { value: 'дисплей' },
    });
    fireEvent.submit(mobileForm);
    expect(state.push).toHaveBeenCalledWith('/register');
  });

  it.each(['Текстовая подсказка', 'Устройство', 'Частое устройство'])(
    'directs guest suggestion %s to registration',
    (label) => {
      render(<Header />);
      fireEvent.click(screen.getAllByRole('button', { name: label, hidden: true })[0]);
      expect(state.push).toHaveBeenCalledWith('/register');
    },
  );

  it('preserves guest search on other routes', () => {
    state.pathname = '/faq';
    render(<Header />);
    fireEvent.change(screen.getAllByLabelText('Поиск запчастей', { selector: 'input' })[0], {
      target: { value: 'дисплей' },
    });
    fireEvent.submit(screen.getAllByRole('search', { hidden: true })[0]);
    expect(state.push).toHaveBeenCalledWith(`/search?q=${encodeURIComponent('дисплей')}`);
  });
});
