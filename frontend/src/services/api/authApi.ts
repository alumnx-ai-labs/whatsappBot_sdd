import { apiRequest } from './client';

export type AdminSession = {
  authenticated: boolean;
  adminId?: string;
  email?: string;
};

export async function login(email: string, password: string) {
  return apiRequest<{ adminId: string; email: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}

export function getSession() {
  return apiRequest<AdminSession>('/auth/session');
}

export function logout() {
  return apiRequest<{ success: boolean }>('/auth/logout', { method: 'POST' });
}
