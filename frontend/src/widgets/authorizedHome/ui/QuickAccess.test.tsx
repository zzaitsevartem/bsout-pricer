import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { QuickAccess } from './QuickAccess';

afterEach(() => vi.useRealTimers());

describe('Quick access supplied icons', () => {
  it.each([
    ['Мои отслеживаемые', '/account/tracking', 'eye'],
    ['Настройки', '/account/settings', 'settings'],
  ])(
    'uses static and hover assets for %s without changing its destination',
    (title, href, name) => {
      render(<QuickAccess used={2} />);
      const card = screen.getByRole('link', { name: new RegExp(title) });
      expect(card).toHaveAttribute('href', href);
      expect(card.querySelector('img')?.getAttribute('src')).toContain(`${name}-static.svg`);
      fireEvent.pointerEnter(card);
      expect(card.querySelector('img')?.getAttribute('src')).toContain(`${name}-hover.webp`);
      fireEvent.pointerLeave(card);
      expect(card.querySelector('img')?.getAttribute('src')).toContain(`${name}-static.svg`);
    },
  );

  it('restarts the eye animation while the tracking card remains hovered', () => {
    vi.useFakeTimers();
    render(<QuickAccess used={2} />);
    const card = screen.getByRole('link', { name: /Мои отслеживаемые/ });
    fireEvent.pointerEnter(card);
    const firstRun = card.querySelector('img');
    expect(firstRun?.getAttribute('src')).toContain('eye-hover.webp?cycle=');

    act(() => vi.advanceTimersByTime(3499));
    expect(card.querySelector('img')).toBe(firstRun);
    act(() => vi.advanceTimersByTime(1));
    const secondRun = card.querySelector('img');
    expect(secondRun).not.toBe(firstRun);
    expect(secondRun?.getAttribute('src')).toContain('eye-hover.webp?cycle=');
    expect(secondRun?.getAttribute('src')).not.toBe(firstRun?.getAttribute('src'));
  });
});
