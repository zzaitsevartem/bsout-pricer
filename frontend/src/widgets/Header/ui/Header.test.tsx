import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Header } from './Header';

vi.mock('next/navigation', () => ({ usePathname: () => '/', useRouter: () => ({ push: vi.fn() }) }));
vi.mock('effector-react', () => ({ useUnit: () => false }));
vi.mock('@/models/user', () => ({ useMe: () => ({}) }));
vi.mock('@/models/auth', () => ({ useLogout: () => ({ mutate: vi.fn() }) }));
vi.mock('@/models/notification', () => ({ useUnreadNotificationCount: () => ({}) }));
vi.mock('./ThemeToggle', () => ({ ThemeToggle: () => null }));
vi.mock('./HeaderSearch', () => ({ HeaderSearch: () => null }));
vi.mock('./UserMenu', () => ({ UserMenu: () => null }));

describe('mobile menu', () => {
  it('keeps closed navigation inert and re-enables it while open', () => {
    const view = render(<Header />);
    const panel = view.container.querySelector<HTMLElement>('[data-open]')!;
    expect(panel.inert).toBe(true);
    expect(panel).toHaveAttribute('aria-hidden', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'Открыть меню' }));
    expect(panel.inert).toBe(false);
    expect(panel).toHaveAttribute('aria-hidden', 'false');
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть меню' }));
    expect(panel.inert).toBe(true);
    expect(panel).toHaveAttribute('aria-hidden', 'true');
  });
});
