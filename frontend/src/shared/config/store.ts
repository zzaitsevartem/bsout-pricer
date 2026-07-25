import { createStore, createEvent } from 'effector';

export const setAuth = createEvent<boolean>();
export const authHydrated = createEvent<boolean>();

export const $isAuth = createStore(false)
  .on(setAuth, (_, value) => value)
  .on(authHydrated, (_, value) => value);

export const $authReady = createStore(false)
  .on(authHydrated, () => true)
  .on(setAuth, () => true);
