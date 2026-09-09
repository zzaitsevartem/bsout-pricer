import { allSettled, fork } from 'effector';
import { describe, expect, it } from 'vitest';

import { $authReady, $isAuth, authHydrated, setAuth } from './store';

describe('auth store', () => {
  it('starts logged out and not ready', () => {
    const scope = fork();
    expect(scope.getState($isAuth)).toBe(false);
    expect(scope.getState($authReady)).toBe(false);
  });

  it('setAuth(true) authenticates and marks ready', async () => {
    const scope = fork();
    await allSettled(setAuth, { scope, params: true });
    expect(scope.getState($isAuth)).toBe(true);
    expect(scope.getState($authReady)).toBe(true);
  });

  it('authHydrated(false) resolves readiness without authenticating', async () => {
    const scope = fork();
    await allSettled(authHydrated, { scope, params: false });
    expect(scope.getState($isAuth)).toBe(false);
    expect(scope.getState($authReady)).toBe(true);
  });

  it('keeps forked scopes isolated from each other', async () => {
    const authed = fork();
    const anon = fork();
    await allSettled(setAuth, { scope: authed, params: true });
    expect(authed.getState($isAuth)).toBe(true);
    expect(anon.getState($isAuth)).toBe(false);
  });
});
