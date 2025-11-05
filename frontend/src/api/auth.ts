import { api } from '@/api/base';
import type { User } from '@/store/auth';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface VerifyEmailData {
  email: string;
  code: string;
}

export interface VerifyEmailResponse {
  success: boolean;
  message: string;
  remaining_attempts?: number | null;
}

export interface ResendVerificationData {
  email: string;
}

export interface ResendVerificationResponse {
  success: boolean;
  message: string;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    return api.post<AuthResponse>('/api/v1/auth/login', credentials);
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    return api.post<AuthResponse>('/api/v1/auth/register', data);
  },

  logout: async (): Promise<void> => {
    return api.post<void>('/api/v1/auth/logout');
  },

  getCurrentUser: async (): Promise<User> => {
    return api.get<User>('/api/v1/auth/me');
  },

  refreshToken: async (refreshToken: string): Promise<{ access_token: string }> => {
    return api.post<{ access_token: string }>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
  },

  verifyEmail: async (data: VerifyEmailData): Promise<VerifyEmailResponse> => {
    return api.post<VerifyEmailResponse>('/api/v1/auth/verify-email', data);
  },

  resendVerification: async (data: ResendVerificationData): Promise<ResendVerificationResponse> => {
    return api.post<ResendVerificationResponse>('/api/v1/auth/resend-verification', data);
  },
};
