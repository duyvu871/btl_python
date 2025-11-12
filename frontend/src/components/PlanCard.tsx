import { Card, Text, Group, Stack, Badge, Button, List, ThemeIcon } from '@mantine/core';
import { IconCheck, IconClock, IconCalendar } from '@tabler/icons-react';
import type { Plan } from '@/api/subscription';

interface PlanCardProps {
  plan: Plan;
  currentPlanCode?: string;
  isLoading?: boolean;
  onSelectPlan?: (planCode: string) => void;
}

export function PlanCard({ plan, currentPlanCode, isLoading, onSelectPlan }: PlanCardProps) {
  const isCurrentPlan = currentPlanCode === plan.code;
  const isPremium = plan.plan_type === 'premium';

  // Format price
  const formattedPrice = new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
  }).format(plan.plan_cost);

  // Calculate discounted price if applicable
  const discountedPrice = plan.plan_discount > 0
    ? new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND',
      }).format(plan.plan_cost * (1 - plan.plan_discount / 100))
    : null;

  return (
    <Card
      shadow="sm"
      padding="lg"
      radius="md"
      withBorder
      style={{
        position: 'relative',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderColor: isCurrentPlan ? 'var(--mantine-color-blue-6)' : undefined,
        borderWidth: isCurrentPlan ? 2 : 1,
      }}
    >
      {/* Header */}
      <Stack gap="xs" mb="md">
        <Group justify="space-between" align="flex-start">
          <Text size="xl" fw={700}>
            {plan.name}
          </Text>
          {isCurrentPlan && (
            <Badge color="blue" variant="filled">
              Current Plan
            </Badge>
          )}
          {isPremium && !isCurrentPlan && (
            <Badge color="yellow" variant="light">
              Premium
            </Badge>
          )}
        </Group>

        {plan.description && (
          <Text size="sm" c="dimmed">
            {plan.description}
          </Text>
        )}
      </Stack>

      {/* Pricing */}
      <Stack gap="xs" mb="md">
        <Group align="baseline" gap="xs">
          {discountedPrice ? (
            <>
              <Text size="sm" c="dimmed" td="line-through">
                {formattedPrice}
              </Text>
              <Text size="xl" fw={700} c="blue">
                {discountedPrice}
              </Text>
              <Badge color="red" variant="light" size="sm">
                -{plan.plan_discount}%
              </Badge>
            </>
          ) : (
            <Text size="xl" fw={700} c="blue">
              {formattedPrice}
            </Text>
          )}
        </Group>
        <Text size="xs" c="dimmed">
          per {plan.billing_cycle}
        </Text>
      </Stack>

      {/* Features */}
      <Stack gap="md" mb="md" style={{ flex: 1 }}>
        <List
          spacing="xs"
          size="sm"
          center
          icon={
            <ThemeIcon color="teal" size={20} radius="xl">
              <IconCheck style={{ width: 12, height: 12 }} />
            </ThemeIcon>
          }
        >
          <List.Item>
            <Group gap="xs">
              <IconClock size={16} />
              <Text size="sm">
                <strong>{plan.monthly_minutes}</strong> minutes per month
              </Text>
            </Group>
          </List.Item>
          <List.Item>
            <Group gap="xs">
              <IconCalendar size={16} />
              <Text size="sm">
                <strong>{plan.monthly_usage_limit}</strong> recordings per month
              </Text>
            </Group>
          </List.Item>
        </List>
      </Stack>

      {/* Action Button */}
      {!isCurrentPlan && onSelectPlan && (
        <Button
          variant={isPremium ? 'filled' : 'light'}
          color={isPremium ? 'blue' : 'gray'}
          fullWidth
          loading={isLoading}
          onClick={() => onSelectPlan(plan.code)}
        >
          {isPremium ? 'Upgrade to Premium' : 'Select Plan'}
        </Button>
      )}

      {isCurrentPlan && (
        <Button variant="outline" color="blue" fullWidth disabled>
          Current Plan
        </Button>
      )}
    </Card>
  );
}

