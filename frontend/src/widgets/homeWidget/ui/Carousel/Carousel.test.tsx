import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import Carousel from './Carousel';

vi.mock('next/image', () => ({ default: ({ alt }: { alt: string }) => <span>{alt}</span> }));
describe('partner carousel', () => {
  it('keeps duplicate links out of the accessibility tree and tab order', () => {
    const view = render(<Carousel />);
    expect(screen.getAllByRole('link')).toHaveLength(4);
    const copies = view.container.querySelectorAll('[data-partner-copy]');
    expect(copies).toHaveLength(12);
    copies.forEach((link) => {
      expect(link).toHaveAttribute('aria-hidden', 'true');
      expect(link).toHaveAttribute('tabindex', '-1');
    });
  });
});
