import { api } from '@/api/base';
import type { Plan, SubscriptionDetail } from './subscription';

export interface PlanCreateData {
  code: string;
  name: string;
  description?: string | null;
  plan_type: string;
  billing_cycle?: string;
  plan_cost?: number;
  plan_discount?: number;
  monthly_minutes: number;
  monthly_usage_limit: number;
  is_default?: boolean;
  is_active?: boolean;
}

export interface PlanUpdateData {
  name?: string;
  description?: string | null;
  plan_cost?: number;
  plan_discount?: number;
  monthly_minutes?: number;
  monthly_usage_limit?: number;
  is_active?: boolean;
}

export interface SubscriptionListItem {
  id: string;
  user_id: string;
  user_email: string | null;
  plan_code: string;
  plan_name: string;
  cycle_start: string;
  cycle_end: string;
  usage_count: number;
  used_seconds: number;
  monthly_usage_limit: number;
  monthly_minutes: number;
}

export interface SubscriptionListResponse {
  total: number;
  page: number;
  page_size: number;
  subscriptions: SubscriptionListItem[];
}

export interface PlanStats {
  total_plans: number;
  active_plans: number;
  inactive_plans: number;
  total_subscriptions: number;
  subscriptions_by_plan: Record<string, number>;
}

export interface MigrateSubscriptionsRequest {
  from_plan_code: string;
  to_plan_code: string;
  reset_usage?: boolean;
}

export interface SubscriptionListParams {
  page?: number;
  page_size?: number;
  plan_code?: string;
  user_email?: string;
}

export const adminSubscriptionApi = {
  // Plans management
  getAllPlans: async (includeInactive = false): Promise<Plan[]> => {
    return api.get<Plan[]>('/api/v1/admin/plans', {
      params: { include_inactive: includeInactive },
    });
  },

  createPlan: async (data: PlanCreateData): Promise<Plan> => {
    return api.post<Plan>('/api/v1/admin/plans', data);
  },

  updatePlan: async (planId: string, data: PlanUpdateData): Promise<Plan> => {
    return api.patch<Plan>(`/api/v1/admin/plans/${planId}`, data);
  },

  deactivatePlan: async (planId: string): Promise<{ message: string }> => {
    return api.post<{ message: string }>(`/api/v1/admin/plans/${planId}/deactivate`);
  },

  // Subscriptions management
  getSubscriptions: async (params?: SubscriptionListParams): Promise<SubscriptionListResponse> => {
    return api.get<SubscriptionListResponse>('/api/v1/admin/subscriptions', { params });
  },

  getUserSubscription: async (userId: string): Promise<SubscriptionDetail> => {
    return api.get<SubscriptionDetail>(`/api/v1/admin/subscriptions/${userId}`);
  },

  changeUserPlan: async (
    userId: string,
    planCode: string,
    prorate = false
  ): Promise<{ message: string; subscription: any }> => {
    return api.post<{ message: string; subscription: any }>(
      `/api/v1/admin/subscriptions/${userId}/change-plan`,
      null,
      {
        params: { plan_code: planCode, prorate },
      }
    );
  },

  migrateSubscriptions: async (data: MigrateSubscriptionsRequest): Promise<{ message: string; migrated_count: number }> => {
    return api.post<{ message: string; migrated_count: number }>(
      '/api/v1/admin/subscriptions/migrate',
      data
    );
  },

  // Statistics
  getStats: async (): Promise<PlanStats> => {
    return api.get<PlanStats>('/api/v1/admin/subscription-stats');
  },
};

