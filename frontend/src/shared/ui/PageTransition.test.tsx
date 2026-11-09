import { act, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PageTransition } from './PageTransition';

const route = vi.hoisted(() => ({ pathname: '/first' }));
vi.mock('next/navigation', () => ({ usePathname: () => route.pathname }));
let preference: EventTarget & { matches: boolean };
let cancel: ReturnType<typeof vi.fn>;
let animate: ReturnType<typeof vi.fn>;
beforeEach(() => {
  route.pathname = '/first';
  preference = Object.assign(new EventTarget(), { matches: false });
  vi.stubGlobal('matchMedia', vi.fn(() => preference));
  cancel = vi.fn();
  animate = vi.fn(() => ({ cancel }));
  Object.defineProperty(HTMLElement.prototype, 'animate', { configurable: true, value: animate });
});
afterEach(() => {
  vi.unstubAllGlobals();
  delete (HTMLElement.prototype as Partial<HTMLElement>).animate;
});
function StatefulChild() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
describe('PageTransition', () => {
  it('only replays on pathname changes and preserves child DOM, state and focus', () => {
    const view = render(<PageTransition><StatefulChild /></PageTransition>);
    const button = screen.getByRole('button');
    button.focus();
    fireEvent.click(button);
    view.rerender(<PageTransition><StatefulChild /></PageTransition>);
    expect(animate).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button')).toBe(button);
    expect(button).toHaveFocus();
    expect(button).toHaveTextContent('1');
    route.pathname = '/second';
    view.rerender(<PageTransition><StatefulChild /></PageTransition>);
    expect(cancel).toHaveBeenCalledTimes(1);
    expect(animate).toHaveBeenCalledTimes(2);
    expect(screen.getByRole('button')).toBe(button);
    expect(button).toHaveFocus();
  });
  it('cancels on navigation, preference change, visibility change and unmount', () => {
    const view = render(<PageTransition>content</PageTransition>);
    route.pathname = '/second';
    view.rerender(<PageTransition>content</PageTransition>);
    expect(cancel).toHaveBeenCalledTimes(1);
    act(() => preference.dispatchEvent(new Event('change')));
    expect(cancel).toHaveBeenCalledTimes(2);
    fireEvent(document, new Event('visibilitychange'));
    expect(cancel).toHaveBeenCalledTimes(3);
    view.unmount();
    expect(cancel).toHaveBeenCalledTimes(4);
    act(() => preference.dispatchEvent(new Event('change')));
    expect(cancel).toHaveBeenCalledTimes(4);
  });
  it('renders content for reduced motion or unsupported WAAPI', () => {
    preference.matches = true;
    const view = render(<PageTransition>content</PageTransition>);
    expect(screen.getByText('content')).toBeVisible();
    expect(animate).not.toHaveBeenCalled();
    view.unmount();
    delete (HTMLElement.prototype as Partial<HTMLElement>).animate;
    render(<PageTransition>still visible</PageTransition>);
    expect(screen.getByText('still visible')).toBeVisible();
  });
});
