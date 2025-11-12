import {
    Stack,
    Title,
    Text,
    Group,
    Badge,
    Progress,
    SimpleGrid,
    Card,
    LoadingOverlay,
    Alert,
    Button,
    Divider
} from '@mantine/core';
import {
    IconClock,
    IconFileText,
    IconCalendar,
    IconTrendingUp,
    IconAlertCircle,
    IconCheck
} from '@tabler/icons-react';
import {useSubscription} from '@/hooks/useSubscription';
import {SubscriptionPlans} from '@/components/SubscriptionPlans';
import {StatsCard} from '@/components/StatsCard';

export function SubscriptionPage() {
    const {subscription, isLoading, hasQuota, quotaMessage} = useSubscription();

    const subscriptionData = subscription.data;
    const usageData = subscriptionData?.usage;

    // Calculate usage percentages
    const minutesPercent = usageData
        ? Math.min(100, Math.round((usageData.used_minutes / usageData.monthly_minutes) * 100))
        : 0;

    const recordingsPercent = usageData
        ? Math.min(100, Math.round((usageData.usage_count / usageData.monthly_usage_limit) * 100))
        : 0;

    // Format date
    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    };

    return (
        <Stack gap="xl" p={"xl"}>
            <LoadingOverlay visible={isLoading} zIndex={1000} overlayProps={{radius: 'sm', blur: 2}}/>

            {/* Quota Warning */}
            {!hasQuota && (
                <Alert
                    icon={<IconAlertCircle size={16}/>}
                    title="Quota Exceeded"
                    color="red"
                    variant="light"
                >
                    {quotaMessage || 'You have reached your monthly quota limit. Please upgrade your plan or wait for the next billing cycle.'}
                </Alert>
            )}

            {/* Current Subscription Info */}
            {subscriptionData && (
                <Stack gap="lg">
                    <Group justify="space-between" align="flex-start">
                        <div>
                            <Group gap="sm" mb="xs">
                                <Title order={2}>Current Plan</Title>
                                <Badge size="lg" variant="filled" color="blue">
                                    {subscriptionData.plan.name}
                                </Badge>
                            </Group>
                            <Text c="dimmed" size="sm">
                                Billing
                                cycle: {formatDate(subscriptionData.cycle_start)} - {formatDate(subscriptionData.cycle_end)}
                            </Text>
                        </div>
                        <Badge
                            size="lg"
                            variant="light"
                            color={hasQuota ? 'green' : 'red'}
                            leftSection={hasQuota ? <IconCheck size={14}/> : <IconAlertCircle size={14}/>}
                        >
                            {hasQuota ? 'Active' : 'Quota Exceeded'}
                        </Badge>
                    </Group>

                    <Divider/>

                    {/* Usage Stats */}
                    <SimpleGrid cols={{base: 1, sm: 2, lg: 4}} spacing="lg">
                        <StatsCard
                            title="Minutes Used"
                            value={`${usageData?.used_minutes || 0} / ${usageData?.monthly_minutes || 0}`}
                            description="minutes this month"
                            color="blue"
                            progress={minutesPercent}
                            icon={<IconClock size={24}/>}
                        />

                        <StatsCard
                            title="Recordings Used"
                            value={`${usageData?.usage_count || 0} / ${usageData?.monthly_usage_limit || 0}`}
                            description="recordings this month"
                            color="green"
                            progress={recordingsPercent}
                            icon={<IconFileText size={24}/>}
                        />

                        <StatsCard
                            title="Remaining Minutes"
                            value={usageData?.remaining_minutes || 0}
                            description="minutes left"
                            color="orange"
                            icon={<IconTrendingUp size={24}/>}
                        />

                        <StatsCard
                            title="Remaining Recordings"
                            value={usageData?.remaining_count || 0}
                            description="recordings left"
                            color="violet"
                            icon={<IconCalendar size={24}/>}
                        />
                    </SimpleGrid>

                    {/* Usage Progress Bars */}
                    <Stack gap="md">
                        <div>
                            <Group justify="space-between" mb="xs">
                                <Text size="sm" fw={500}>
                                    Minutes Usage
                                </Text>
                                <Text size="sm" c="dimmed">
                                    {minutesPercent}%
                                </Text>
                            </Group>
                            <Progress
                                value={minutesPercent}
                                color={minutesPercent > 90 ? 'red' : minutesPercent > 70 ? 'orange' : 'blue'}
                                size="lg"
                                radius="xl"
                            />
                        </div>

                        <div>
                            <Group justify="space-between" mb="xs">
                                <Text size="sm" fw={500}>
                                    Recordings Usage
                                </Text>
                                <Text size="sm" c="dimmed">
                                    {recordingsPercent}%
                                </Text>
                            </Group>
                            <Progress
                                value={recordingsPercent}
                                color={recordingsPercent > 90 ? 'red' : recordingsPercent > 70 ? 'orange' : 'green'}
                                size="lg"
                                radius="xl"
                            />
                        </div>
                    </Stack>
                </Stack>
            )}

            <div className={"my-10"}></div>
            {/* Plan Selection */}
            <SubscriptionPlans/>
            <div className={"my-10"}></div>

            {/* Help Section */}
            <Card withBorder p="lg">
                <Stack gap="sm">
                    <Group>
                        <IconAlertCircle size={20} color="var(--mantine-color-blue-6)"/>
                        <Title order={4}>Need help?</Title>
                    </Group>
                    <Text size="sm" c="dimmed">
                        If you have any questions about our plans or need assistance, please contact our support team.
                    </Text>
                    <div>
                        <Button variant="light" color="blue" size="sm">
                            Contact Support
                        </Button>
                    </div>
                </Stack>
            </Card>
        </Stack>
    );
}

