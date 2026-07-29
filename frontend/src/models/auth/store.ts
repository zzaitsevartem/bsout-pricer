import { createStore, createEvent } from 'effector';
import type { UserResponse } from '@/models/user/schema';

export const userLoggedIn = createEvent();
export const userLoggedOut = createEvent();
export const userDataReceived = createEvent<UserResponse | null>();

export const $isAuth = createStore<boolean>(false)
  .on([userLoggedIn, userDataReceived], (_, user) => user !== null && user !== undefined)
  .reset(userLoggedOut);

export const $user = createStore<UserResponse | null>(null)
  .on(userDataReceived, (_, user) => user)
  .reset(userLoggedOut);

export const $authPending = createStore<boolean>(true)
  .on(userDataReceived, () => false)
  .on(userLoggedIn, () => false)
  .reset(userLoggedOut);
