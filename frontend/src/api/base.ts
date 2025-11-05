import { axiosInstance } from '@/lib/axios';
import type { SuccessResponse } from '@/types/api';
import axios, { AxiosError, type AxiosRequestConfig } from 'axios';

export class ApiError extends Error {
    constructor(
    message: string,
    // @ts-ignore
    public statusCode?: number,
    // @ts-ignore
    public errorCode?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Base API request handler with proper error handling
 * @param config - Axios request configuration
 * @returns The data from the response
 * @throws ApiError with message from backend
 */
export async function apiRequest<T>(
  config: AxiosRequestConfig
): Promise<T> {
  try {
    const response = await axiosInstance.request<SuccessResponse<T>>(config);
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ message?: string; error_code?: string }>;

      // Extract error message from response
      const message = axiosError.response?.data?.message || axiosError.message || 'An error occurred';
      const statusCode = axiosError.response?.status;
      const errorCode = axiosError.response?.data?.error_code;

      throw new ApiError(message, statusCode, errorCode);
    }

    // For non-axios errors
    throw new ApiError(error instanceof Error ? error.message : 'Unknown error occurred');
  }
}

/**
 * Helper functions for common HTTP methods
 */
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'GET', url }),

  post: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'POST', url, data }),

  put: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'PUT', url, data }),

  patch: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'PATCH', url, data }),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiRequest<T>({ ...config, method: 'DELETE', url }),
};

