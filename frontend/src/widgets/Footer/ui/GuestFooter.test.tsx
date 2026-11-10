import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Footer } from './Footer';

describe('guest homepage footer', () => {
  it('contains only known routes and configured destinations', () => {
    render(<Footer variant="guest-home" />);
    const allowedRoutes = [
      '/',
      '/search',
      '/register',
      '/tariffs',
      '/faq',
      '/contacts',
      '/privacy',
      '/terms',
      '/#how-it-works',
    ];
    for (const link of screen.getAllByRole('link')) {
      const href = link.getAttribute('href');
      expect(href).toBeTruthy();
      expect(href).not.toBe('#');
      expect(
        allowedRoutes.includes(href!) ||
          ['mailto:hello@bscout.ru', 'mailto:support@bscout.ru'].includes(href!),
      ).toBe(true);
      if (href!.startsWith('/')) {
        const path = href!.split('#')[0];
        const pages = import.meta.glob('/src/app/**/page.tsx');
        expect(Object.keys(pages)).toContain(`/src/app${path === '/' ? '' : path}/page.tsx`);
      }
    }
  });
});
