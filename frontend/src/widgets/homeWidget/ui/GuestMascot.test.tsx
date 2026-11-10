import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { GuestMascot } from './GuestMascot';

const scene = vi.hoisted(() => {
  const head = { rotation: { x: 0, y: 0 } };
  const eyes = ['Left', 'Right'].flatMap((side) => ['EyeWhite', 'Iris', 'Pupil', 'EyeGlint'].map((part) => ({ name: side + part, visible: true })));
  const lashes = ['ClosedLashLeft', 'ClosedLashRight'].map((name) => ({ name, visible: true, geometry: { dispose: vi.fn() }, material: { dispose: vi.fn() } }));
  const model = { rotation: { y: 0 }, getObjectByName: vi.fn((name: string) => name === 'HeadPivot' ? head : undefined), traverse: (cb: (part: object) => void) => [...eyes, ...lashes].forEach(cb) };
  return { head, eyes, lashes, model, load: vi.fn(), render: vi.fn(), dispose: vi.fn(), resizeDisconnect: vi.fn() };
});
vi.mock('three', () => {
  class Renderer {
    domElement = document.createElement('canvas');
    setPixelRatio = vi.fn(); setSize = vi.fn(); render = scene.render; dispose = scene.dispose;
  }
  class Object3D { position = { set: vi.fn() }; add = vi.fn(); lookAt = vi.fn(); updateProjectionMatrix = vi.fn(); }
  return { WebGLRenderer: Renderer, Scene: Object3D, HemisphereLight: Object3D, DirectionalLight: Object3D, PerspectiveCamera: Object3D, SRGBColorSpace: 'srgb', ACESFilmicToneMapping: 'aces' };
});
vi.mock('three/addons/loaders/GLTFLoader.js', () => ({ GLTFLoader: class { loadAsync = scene.load; } }));

let visibility: IntersectionObserverCallback;
let frame: FrameRequestCallback | undefined;
const disconnect = vi.fn();
let finePointer = true;
let reducedMotion = false;
beforeEach(() => {
  vi.useFakeTimers(); vi.spyOn(Math, 'random').mockReturnValue(0);
  scene.head.rotation.x = 0; scene.head.rotation.y = 0;
  scene.eyes.forEach((part) => { part.visible = true; });
  scene.lashes.forEach((part) => { part.visible = true; });
  scene.load.mockResolvedValue({ scene: scene.model });
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => { frame = callback; return 1; });
  vi.stubGlobal('cancelAnimationFrame', vi.fn());
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() { scene.resizeDisconnect(); } });
  vi.stubGlobal('IntersectionObserver', class {
    constructor(callback: IntersectionObserverCallback) { visibility = callback; }
    observe() {} disconnect() { disconnect(); }
  });
  vi.stubGlobal('matchMedia', (query: string) => ({ matches: query.includes('reduced-motion') ? reducedMotion : finePointer, media: query, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
});
afterEach(() => {
  vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.clearAllMocks();
  finePointer = true; reducedMotion = false; frame = undefined;
});
async function setup() {
  const view = render(<section><GuestMascot pose="hero" /></section>);
  const mascot = screen.getByTestId('guest-mascot');
  const section = mascot.closest('section')!;
  vi.spyOn(section, 'getBoundingClientRect').mockReturnValue({ left: 0, top: 0, width: 100, height: 100 } as DOMRect);
  await act(async () => { visibility([{ isIntersecting: true } as IntersectionObserverEntry], {} as IntersectionObserver); });
  return { ...view, section, mascot };
}
function move(section: HTMLElement, pointerType: string, clientX: number) {
  const event = new Event('pointermove', { bubbles: true });
  Object.assign(event, { pointerType, clientX, clientY: 50 }); fireEvent(section, event);
}
function tick() { act(() => frame?.(0)); }

describe('guest mascot 3D scene', () => {
  it('loads a canvas model, turns only its head, and blinks', async () => {
    const { section, mascot } = await setup();
    expect(scene.load).toHaveBeenCalledWith('/redesign/3d/rabbit.glb');
    expect(mascot).toHaveAttribute('data-ready', 'true');
    expect(mascot.querySelectorAll('canvas')).toHaveLength(1);
    expect(mascot.querySelectorAll('img')).toHaveLength(0);
    expect(scene.render).toHaveBeenCalled();
    expect(scene.model.getObjectByName).toHaveBeenCalledWith('HeadPivot');
    expect(scene.eyes.every((part) => part.visible)).toBe(true);
    expect(scene.lashes.every((part) => !part.visible)).toBe(true);
    const bodyRotation = scene.model.rotation.y;
    move(section, 'mouse', 100); tick();
    expect(scene.head.rotation.y).toBeGreaterThan(0);
    expect(scene.model.rotation.y).toBe(bodyRotation);
    move(section, 'mouse', 0); tick(); tick();
    expect(scene.head.rotation.y).toBeLessThan(0);
    const beforeCenter = Math.abs(scene.head.rotation.y);
    fireEvent.pointerLeave(section); tick();
    expect(Math.abs(scene.head.rotation.y)).toBeLessThan(beforeCenter);
    act(() => vi.advanceTimersByTime(3000));
    expect(mascot).toHaveAttribute('data-blinking', 'true');
    expect(scene.eyes.every((part) => !part.visible)).toBe(true);
    expect(scene.lashes.every((part) => part.visible)).toBe(true);
    act(() => vi.advanceTimersByTime(125));
    expect(mascot).toHaveAttribute('data-blinking', 'false');
    expect(scene.eyes.every((part) => part.visible)).toBe(true);
    expect(scene.lashes.every((part) => !part.visible)).toBe(true);
  });
  it('ignores touch and cleans up when it leaves view', async () => {
    const { section, mascot, unmount } = await setup();
    move(section, 'touch', 100); tick(); expect(scene.head.rotation.y).toBe(0);
    act(() => visibility([{ isIntersecting: false } as IntersectionObserverEntry], {} as IntersectionObserver));
    expect(mascot.querySelector('canvas')).toBeNull();
    expect(scene.dispose).toHaveBeenCalled(); expect(scene.resizeDisconnect).toHaveBeenCalled();
    expect(scene.lashes[0].geometry.dispose).toHaveBeenCalled(); expect(scene.lashes[0].material.dispose).toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
    move(section, 'mouse', 100); expect(scene.head.rotation.y).toBe(0);
    unmount(); expect(disconnect).toHaveBeenCalled();
  });
  it.each(['reduced motion', 'coarse pointer'])('does not track on %s', async (setting) => {
    reducedMotion = setting === 'reduced motion'; finePointer = setting !== 'coarse pointer';
    const { section } = await setup();
    move(section, 'mouse', 100); tick(); expect(scene.head.rotation.y).toBe(0);
    if (reducedMotion) expect(vi.getTimerCount()).toBe(0);
  });
  it('removes active listeners, animation and timers on unmount', async () => {
    const { section, unmount } = await setup();
    move(section, 'mouse', 100); tick(); const rotation = scene.head.rotation.y;
    unmount(); expect(disconnect).toHaveBeenCalled(); expect(cancelAnimationFrame).toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
    move(section, 'mouse', 0); expect(scene.head.rotation.y).toBe(rotation);
  });
});
