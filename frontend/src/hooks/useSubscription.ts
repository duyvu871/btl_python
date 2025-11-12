import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { subscriptionApi, type ChangePlanRequest } from '@/api/subscription';
import {notifications} from '@mantine/notifications';
/**
 * Hook to get current user's subscription
 */
export const useMySubscription = () => {
  return useQuery({
    queryKey: ['subscription', 'me'],
    queryFn: () => subscriptionApi.getMySubscription(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

/**
 * Hook to check quota
 */
export const useCheckQuota = () => {
  return useQuery({
    queryKey: ['subscription', 'quota'],
    queryFn: () => subscriptionApi.checkQuota(),
    staleTime: 1000 * 60, // 1 minute
  });
};

/**
 * Hook to get available plans
 */
export const usePlans = () => {
  return useQuery({
    queryKey: ['subscription', 'plans'],
    queryFn: () => subscriptionApi.getPlans(),
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
};

/**
 * Hook to change plan
 */
export const useChangePlan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ChangePlanRequest) => subscriptionApi.changePlan(data),
    onSuccess: () => {
      // Invalidate subscription queries
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
      notifications.show({
        title: 'Success',
        message: 'Plan changed successfully',
        color: 'green',
      });
    },
    onError: (error: any) => {
      notifications.show({
        title: 'Failed to change plan',
        message: error.message || 'An error occurred while changing plan',
        color: 'red',
      });
    },
  });
};

/**
 * Combined hook for subscription management
 */
export const useSubscription = () => {
  const subscription = useMySubscription();
  const quota = useCheckQuota();
  const plans = usePlans();
  const changePlan = useChangePlan();

  return {
    subscription,
    quota,
    plans,
    changePlan,
    
    // Helper properties
    hasQuota: quota.data?.has_quota ?? true,
    quotaMessage: quota.data?.error_message ?? '',
    isLoading: subscription.isLoading || quota.isLoading || plans.isLoading,
  };
};

