import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Footer } from './Footer';

describe('Footer social icons', () => {
  it.each([
    ['Telegram', 'logo-tg'],
    ['VK', 'logo-vk'],
  ])('uses the provided %s assets and animates on hover', (label, iconName) => {
    render(<Footer />);
    const link = screen.getByRole('link', { name: label });
    const image = link.querySelector('img');
    expect(image?.getAttribute('src')).toContain(`${iconName}-static.svg`);
    expect(image).toHaveAttribute('width', '40');
    expect(image).toHaveAttribute('height', '40');
    expect(link).not.toHaveClass('border');
    fireEvent.pointerEnter(link);
    expect(link.querySelector('img')?.getAttribute('src')).toContain(`${iconName}-hover.webp`);
  });
});
