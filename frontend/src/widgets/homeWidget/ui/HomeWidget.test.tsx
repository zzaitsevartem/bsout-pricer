import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { HomeWidget } from './index';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('@/models/payment', () => ({
  usePlans: () => ({ data: [], isLoading: false, isError: false }),
}));

describe('homepage navigation', () => {
  it('exposes unique section targets and resolves in-page links', () => {
    const { container } = render(<HomeWidget />);
    for (const id of ['home', 'compare', 'advantages', 'how-it-works', 'tariffs', 'start']) {
      expect(container.querySelectorAll(`[id="${id}"]`)).toHaveLength(1);
      expect(container.querySelector(`#${id}`)?.tagName).toBe('SECTION');
    }
    const links = Array.from(container.querySelectorAll<HTMLAnchorElement>('a[href^="#"]'));
    expect(links.length).toBeGreaterThan(0);
    for (const link of links)
      expect(container.querySelector(link.getAttribute('href')!)).not.toBeNull();
    expect(screen.getByRole('link', { name: 'Начать поиск' })).toHaveAttribute('href', '/register');
  });
});
