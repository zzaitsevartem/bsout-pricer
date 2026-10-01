import axios from 'axios';
import { setAuth } from '@/shared/config/store';

export const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

function failAuth() {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  setAuth(false);
  window.location.href = '/login';
}

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

let refreshInFlight: Promise<string> | null = null;

const runRefresh = (refreshToken: string): Promise<string> => {
  refreshInFlight ??= axios
    .post('/api/auth/refresh', { refresh_token: refreshToken })
    .then(({ data }) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return data.access_token as string;
    })
    .finally(() => {
      refreshInFlight = null;
    });

  return refreshInFlight;
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken =
        typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;

      if (!refreshToken) {
        failAuth();
        return Promise.reject(error);
      }

      try {
        const accessToken = await runRefresh(refreshToken);

        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch {
        failAuth();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);
