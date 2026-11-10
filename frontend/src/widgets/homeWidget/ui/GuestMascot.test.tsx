import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { GuestMascot } from './GuestMascot';
import { readFileSync } from 'node:fs';

let visibility: IntersectionObserverCallback;
const disconnect = vi.fn();
let finePointer = true;
let reducedMotion = false;

beforeEach(() => {
  vi.useFakeTimers();
  vi.spyOn(Math, 'random').mockReturnValue(0);
  vi.stubGlobal(
    'IntersectionObserver',
    class {
      constructor(callback: IntersectionObserverCallback) {
        visibility = callback;
      }
      observe() {}
      disconnect() {
        disconnect();
      }
    },
  );
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: query.includes('reduced-motion') ? reducedMotion : finePointer,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  finePointer = true;
  reducedMotion = false;
  disconnect.mockClear();
});

function setup() {
  const view = render(
    <section>
      <GuestMascot pose="hero" />
    </section>,
  );
  const mascot = screen.getByTestId('guest-mascot');
  vi.spyOn(mascot, 'getBoundingClientRect').mockReturnValue({
    left: 0,
    top: 0,
    width: 100,
    height: 100,
  } as DOMRect);
  act(() =>
    visibility([{ isIntersecting: true } as IntersectionObserverEntry], {} as IntersectionObserver),
  );
  return {
    ...view,
    section: mascot.closest('section')!,
    head: screen.getByTestId('mascot-head'),
    mascot,
  };
}

function move(section: HTMLElement, pointerType: string, clientX: number) {
  const event = new Event('pointermove', { bubbles: true });
  Object.assign(event, { pointerType, clientX, clientY: 33 });
  fireEvent(section, event);
}

describe('guest mascot motion', () => {
  it('turns toward a mouse, recenters, and blinks open again', () => {
    const { section, head, mascot } = setup();
    const body = mascot.querySelector<HTMLElement>('.guest-mascot-body')!;
    const bodyTransform = body.style.transform;
    move(section, 'mouse', 100);
    const rightTurn = head.style.transform;
    expect(rightTurn).not.toBe('');
    expect(body.style.transform).toBe(bodyTransform);
    expect(readFileSync('src/app/globals.css', 'utf8')).toMatch(
      /\.guest-mascot-head\s*\{[^}]*mask-image:\s*linear-gradient\([^}]*transparent/s,
    );
    move(section, 'mouse', 0);
    expect(head.style.transform).not.toBe(rightTurn);
    fireEvent.pointerLeave(section);
    expect(head.style.transform).toContain('rotateY(0deg)');
    const eyelids = mascot.querySelector('[data-blinking]')!;
    expect(eyelids).toHaveAttribute('data-blinking', 'false');
    act(() => vi.advanceTimersByTime(3000));
    expect(eyelids).toHaveAttribute('data-blinking', 'true');
    act(() => vi.advanceTimersByTime(120));
    expect(eyelids).toHaveAttribute('data-blinking', 'false');
  });

  it('ignores touch and stops timers and listeners when no longer visible', () => {
    const { section, head, unmount } = setup();
    move(section, 'touch', 100);
    expect(head.style.transform).toBe('');
    act(() =>
      visibility(
        [{ isIntersecting: false } as IntersectionObserverEntry],
        {} as IntersectionObserver,
      ),
    );
    move(section, 'mouse', 100);
    expect(head.style.transform).toContain('rotateY(0deg)');
    expect(vi.getTimerCount()).toBe(0);
    unmount();
    expect(disconnect).toHaveBeenCalled();
  });

  it.each(['reduced motion', 'coarse pointer'])('does not track on %s', (setting) => {
    reducedMotion = setting === 'reduced motion';
    finePointer = setting !== 'coarse pointer';
    const { section, head } = setup();
    move(section, 'mouse', 100);
    expect(head.style.transform).toBe('');
    expect(vi.getTimerCount()).toBe(0);
  });

  it('removes active listeners and timers when unmounted while visible', () => {
    const { section, head, unmount } = setup();
    move(section, 'mouse', 100);
    expect(vi.getTimerCount()).toBeGreaterThan(0);
    unmount();
    expect(disconnect).toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
    const transform = head.style.transform;
    move(section, 'mouse', 0);
    expect(head.style.transform).toBe(transform);
  });
});
