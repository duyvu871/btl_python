import { api } from '@/api/base';

export interface User {
  id: string;
  user_name: string;
  email: string;
  verified: boolean;
  role: string;
  preferences: string[];
  created_at: string;
}

export interface UserListResponse {
  total: number;
  page: number;
  page_size: number;
  users: User[];
}

export interface UserStats {
  total_users: number;
  verified_users: number;
  unverified_users: number;
  admin_users: number;
  recent_users: number;
}

export interface UserUpdateData {
  user_name?: string;
  email?: string;
  verified?: boolean;
  role?: string;
  preferences?: string[];
}

export interface UserCreateData {
  email: string;
  password: string;
  user_name?: string;
  role?: string;
  verified?: boolean;
  preferences?: string[];
}

export interface UserListParams {
  page?: number;
  page_size?: number;
  search?: string;
  role?: string;
  verified?: boolean;
}

export interface BulkActionResponse {
  success: boolean;
  action: string;
  updated_count: number;
  total_requested: number;
}

export const adminApi = {
  // Get list of users with filters
  getUsers: async (params?: UserListParams): Promise<UserListResponse> => {
    return api.get<UserListResponse>('/api/v1/admin/users', { params });
  },

  // Get single user by ID
  getUser: async (userId: string): Promise<User> => {
    return api.get<User>(`/api/v1/admin/users/${userId}`);
  },

  // Update user
  updateUser: async (userId: string, data: UserUpdateData): Promise<User> => {
    return api.patch<User>(`/api/v1/admin/users/${userId}`, data);
  },

  // Delete user
  deleteUser: async (userId: string): Promise<void> => {
    return api.delete<void>(`/api/v1/admin/users/${userId}`);
  },

  // Get user statistics
  getStats: async (): Promise<UserStats> => {
    return api.get<UserStats>('/api/v1/admin/stats');
  },

  // Bulk action on multiple users
  bulkAction: async (userIds: string[], action: string): Promise<BulkActionResponse> => {
    return api.post<BulkActionResponse>(`/api/v1/admin/users/bulk-action?action=${action}`, userIds);
  },

  // Create user
  createUser: async (data: UserCreateData): Promise<User> => {
    return api.post<User>('/api/v1/admin/users', data);
  },
};
