import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import Hero from './Hero';

const push = vi.hoisted(() => vi.fn());
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));

describe('guest hero search', () => {
  it('sends a typed search to registration', () => {
    render(<Hero />);
    fireEvent.change(screen.getByLabelText('Название запчасти'), {
      target: { value: 'дисплей iPhone' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Найти запчасть' }));
    expect(push).toHaveBeenCalledWith('/register');
  });

  it('directs example searches to registration', () => {
    render(<Hero />);
    for (const label of ['Дисплей iPhone 13', 'Аккумулятор Samsung', 'Шлейф зарядки']) {
      expect(screen.getByRole('link', { name: label })).toHaveAttribute('href', '/register');
    }
  });
});
