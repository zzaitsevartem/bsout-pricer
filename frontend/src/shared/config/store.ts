import { createStore, createEvent } from 'effector';

export interface User {
  id: string;
  email: string;
  name: string;
}

export const setAuth = createEvent<boolean>();
export const setUser = createEvent<User | null>();
export const reset = createEvent();

export const $isAuth = createStore(false)
  .on(setAuth, (_, value) => value)
  .on(reset, () => false);

export const $user = createStore<User | null>(null)
  .on(setUser, (_, value) => value)
  .on(reset, () => null);
