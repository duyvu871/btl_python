import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/api/auth';
import type { VerifyEmailData, ResendVerificationData } from '@/api/auth';

export function useVerifyEmail() {
  return useMutation({
    mutationFn: (data: VerifyEmailData) => authApi.verifyEmail(data),
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: (data: ResendVerificationData) => authApi.resendVerification(data),
  });
}

