import { useMutation, useQueryClient } from '@tanstack/react-query';
import { setAuth } from '@/shared/config/store';
import { authApi } from './service';
import type { RegisterRequest, LoginRequest } from './schema';

export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: (response) => {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      setAuth(true);
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (response) => {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      setAuth(true);
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSettled: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setAuth(false);
      queryClient.clear();
    },
  });
}
