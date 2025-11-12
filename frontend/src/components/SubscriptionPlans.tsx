import { Grid, Stack, Title, Text, Loader, Center, Alert } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { useSubscription } from '@/hooks/useSubscription';
import { PlanCard } from './PlanCard';

export function SubscriptionPlans() {
  const { subscription, plans, changePlan, isLoading } = useSubscription();

  // Loading state
  if (isLoading) {
    return (
      <Center h={400}>
        <Loader size="lg" />
      </Center>
    );
  }

  // Error state
  if (subscription.isError || plans.isError) {
    return (
      <Alert
        icon={<IconAlertCircle size={16} />}
        title="Error"
        color="red"
        variant="light"
      >
        Failed to load subscription information. Please try again later.
      </Alert>
    );
  }

  const currentPlanCode = subscription.data?.plan?.code;
  const availablePlans = plans.data || [];

  const handleSelectPlan = async (planCode: string) => {
    try {
      await changePlan.mutateAsync({
        plan_code: planCode,
        prorate: true,
      });
    } catch (error) {
      // Error handling is done in the hook
      console.error('Failed to change plan:', error);
    }
  };

  return (
    <Stack gap="xl">
      {/* Header */}
      <Stack gap="xs">
        <Title order={2}>Available Plans</Title>
        <Text c="dimmed">
          Choose the plan that best fits your needs. You can upgrade or downgrade at any time.
        </Text>
      </Stack>

      {/* Plans Grid */}
      <Grid>
        {availablePlans.map((plan) => (
          <Grid.Col key={plan.id} span={{ base: 12, sm: 6, md: 4 }}>
            <PlanCard
              plan={plan}
              currentPlanCode={currentPlanCode}
              isLoading={changePlan.isPending}
              onSelectPlan={handleSelectPlan}
            />
          </Grid.Col>
        ))}
      </Grid>

      {availablePlans.length === 0 && (
        <Center h={200}>
          <Text c="dimmed">No plans available at the moment.</Text>
        </Center>
      )}
    </Stack>
  );
}

