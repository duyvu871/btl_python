// Generic API response type for success
export interface SuccessResponse<T = any> {
  success: true;
  message?: string;
  data: T;
}

// Generic API response type for error
export interface ErrorResponse {
  success: false;
  error_code: string;
  message: string;
  data?: any;
}
