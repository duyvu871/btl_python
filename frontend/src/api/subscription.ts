import { api } from '@/api/base';

export interface PlanSnapshot {
  code: string;
  name: string;
  monthly_minutes: number;
  monthly_usage_limit: number;
}

export interface Plan {
  id: string;
  code: string;
  name: string;
  description: string | null;
  plan_type: string;
  plan_cost: number;
  plan_discount: number;
  monthly_minutes: number;
  monthly_usage_limit: number;
  billing_cycle: string;
  created_at: string;
}

export interface UsageStats {
  usage_count: number;
  monthly_usage_limit: number;
  remaining_count: number;
  used_seconds: number;
  monthly_seconds: number;
  remaining_seconds: number;
  used_minutes: number;
  monthly_minutes: number;
  remaining_minutes: number;
}

export interface SubscriptionDetail {
  plan: PlanSnapshot;
  cycle_start: string;
  cycle_end: string;
  usage: UsageStats;
}

export interface QuotaCheck {
  has_quota: boolean;
  error_message: string;
}

export interface ChangePlanRequest {
  plan_code: string;
  prorate?: boolean;
}

export interface ChangePlanResponse {
  message: string;
  new_plan: PlanSnapshot;
  subscription: {
    id: string;
    user_id: string;
    plan: PlanSnapshot;
    cycle_start: string;
    cycle_end: string;
    usage: UsageStats;
  };
}

export const subscriptionApi = {
  // Get current user's subscription
  getMySubscription: async (): Promise<SubscriptionDetail> => {
    return api.get<SubscriptionDetail>('/api/v1/subscriptions/me');
  },

  // Check quota
  checkQuota: async (): Promise<QuotaCheck> => {
    return api.get<QuotaCheck>('/api/v1/subscriptions/check-quota');
  },

  // Change plan
  changePlan: async (data: ChangePlanRequest): Promise<ChangePlanResponse> => {
    return api.post<ChangePlanResponse>('/api/v1/subscriptions/change-plan', data);
  },

  // Get available plans
  getPlans: async (): Promise<Plan[]> => {
    return api.get<Plan[]>('/api/v1/subscriptions/plans');
  },
};

