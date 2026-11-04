import { act, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SearchIcon } from './SearchIcon';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
function mount() {
  const view = render(
    <button aria-label="Найти">
      <SearchIcon />
    </button>,
  );
  const button = screen.getByRole('button', { name: 'Найти' });
  const source = () => view.container.querySelector('img')?.getAttribute('src');
  return { button, source };
}

describe('Shared magnifier', () => {
  it('uses supplied static asset, starts animation on the host and restores static on leave', () => {
    const { button, source } = mount();
    expect(source()).toContain('magnifier-static.svg');
    fireEvent.pointerEnter(button);
    expect(source()).toContain('magnifier-hover.webp');
    fireEvent.pointerLeave(button);
    expect(source()).toContain('magnifier-static.svg');
    fireEvent.pointerEnter(button);
    expect(source()).toContain('magnifier-hover.webp');
  });
  it('supports keyboard focus and keeps the control accessible', async () => {
    const { button, source } = mount();
    await userEvent.tab();
    expect(button).toHaveFocus();
    expect(source()).toContain('magnifier-hover.webp');
    await userEvent.tab();
    expect(source()).toContain('magnifier-static.svg');
  });
  it('retains animation until both hover and focus end', () => {
    const { button, source } = mount();
    fireEvent.pointerEnter(button);
    fireEvent.focusIn(button);
    fireEvent.pointerLeave(button);
    expect(source()).toContain('magnifier-hover.webp');
    fireEvent.focusOut(button);
    expect(source()).toContain('magnifier-static.svg');
  });
  it('retains the static icon for reduced motion', () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn(() => ({ matches: true })),
    );
    const { button, source } = mount();
    fireEvent.pointerEnter(button);
    fireEvent.focusIn(button);
    expect(source()).toContain('magnifier-static.svg');
  });
  it('replays after the icon animation while hover remains active, and stops on leave', () => {
    vi.useFakeTimers();
    const view = render(<button aria-label="Найти"><SearchIcon /></button>);
    const button = screen.getByRole('button', { name: 'Найти' });
    fireEvent.pointerEnter(button);
    const firstRun = view.container.querySelector('img');
    expect(firstRun?.getAttribute('src')).toContain('magnifier-hover.webp');

    act(() => vi.advanceTimersByTime(2999));
    expect(view.container.querySelector('img')).toBe(firstRun);
    act(() => vi.advanceTimersByTime(1));
    const secondRun = view.container.querySelector('img');
    expect(secondRun).not.toBe(firstRun);
    expect(secondRun?.getAttribute('src')).toContain('magnifier-hover.webp');

    fireEvent.pointerLeave(button);
    const staticIcon = view.container.querySelector('img');
    act(() => vi.advanceTimersByTime(3000));
    expect(view.container.querySelector('img')).toBe(staticIcon);
    expect(staticIcon?.getAttribute('src')).toContain('magnifier-static.svg');
    vi.useRealTimers();
  });
});
