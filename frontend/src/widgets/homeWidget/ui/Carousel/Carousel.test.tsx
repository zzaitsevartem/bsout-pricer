import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Carousel from './Carousel';

vi.mock('next/image', () => ({ default: ({ alt }: { alt: string }) => <span>{alt}</span> }));
afterEach(() => vi.unstubAllGlobals());
describe('partner carousel', () => {
  it('pauses offscreen, in hidden tabs and at user request; disconnects on unmount', () => {
    let callback: IntersectionObserverCallback;
    const disconnect = vi.fn();
    const observe = vi.fn();
    vi.stubGlobal('IntersectionObserver', class {
      constructor(cb: IntersectionObserverCallback) { callback = cb; }
      observe = observe;
      disconnect = disconnect;
    });
    let hidden = false;
    const hiddenSpy = vi.spyOn(document, 'hidden', 'get').mockImplementation(() => hidden);
    const view = render(<Carousel />);
    const section = view.container.querySelector('section')!;
    expect(observe).toHaveBeenCalledWith(section);
    expect(section).toHaveAttribute('data-running', 'false');
    act(() => callback([{ isIntersecting: true } as IntersectionObserverEntry], {} as IntersectionObserver));
    expect(section).toHaveAttribute('data-running', 'true');
    hidden = true;
    fireEvent(document, new Event('visibilitychange'));
    expect(section).toHaveAttribute('data-running', 'false');
    hidden = false;
    fireEvent(document, new Event('visibilitychange'));
    expect(section).toHaveAttribute('data-running', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'Приостановить прокрутку магазинов' }));
    expect(section).toHaveAttribute('data-running', 'false');
    fireEvent.click(screen.getByRole('button', { name: 'Продолжить прокрутку магазинов' }));
    expect(section).toHaveAttribute('data-running', 'true');
    act(() => callback([{ isIntersecting: false } as IntersectionObserverEntry], {} as IntersectionObserver));
    expect(section).toHaveAttribute('data-running', 'false');
    view.unmount();
    expect(disconnect).toHaveBeenCalledOnce();
    hiddenSpy.mockRestore();
  });
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
