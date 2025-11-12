import {Title, Text, Button, Stack, SimpleGrid, Paper, Group, Badge, LoadingOverlay} from '@mantine/core';
import {IconMicrophone, IconFileText, IconClock, IconTrendingUp} from '@tabler/icons-react';
import {useAuth} from '@/providers/AuthProvider';
import {useNavigate} from 'react-router-dom';
import {StatsCard} from '@/components/StatsCard';
import {useRecordingStats} from "@/hooks/useRecord.ts";
import {useDisclosure} from "@mantine/hooks";
import {useEffect} from "react";

export function DashboardPage() {
    const {user} = useAuth();
    const navigate = useNavigate();
    const isAdmin = user?.role === 'admin';
    const [loading, {open: openLoading, close: closeLoading}] = useDisclosure(true);

    const {data: stats} = useRecordingStats(!!user?.id);

    useEffect(() => {
        if (stats) {
            closeLoading();
        } else {
            openLoading();
        }
    }, [stats]);

    // Calculate usage percentage based on plan quota from API
    const quotaMinutes = stats?.quota_minutes || 0; // fallback to 1000 if no plan
    const usagePercent = quotaMinutes > 0 ? (stats?.usage_minutes
        ? Math.min(100, Math.round((stats.usage_minutes / quotaMinutes) * 100))
        : 0) : 0;

    // Format duration helper
    const formatDuration = (ms: number) => {
        const seconds = Math.floor(ms / 1000);
        if (seconds < 60) return `${seconds} secs`;
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes} mins`;
        const hours = Math.floor(minutes / 60);
        return `${hours} hrs`;
    }

    return (
        <Stack gap="lg" p={"xl"}>
            <LoadingOverlay visible={loading} zIndex={1000} overlayProps={{radius: "sm", blur: 2}}/>
            <Group justify="space-between" align="center">
                <div>
                    <Group gap="sm">
                        <Title order={1}>Dashboard</Title>
                        {isAdmin && (
                            <Badge color="blue" variant="filled">
                                Admin
                            </Badge>
                        )}
                    </Group>
                    <Text c="dimmed" size="sm">
                        Welcome back, {user?.profile?.name || user?.user_name}!
                    </Text>
                </div>
                <Button
                    variant="filled"
                    color="blue"
                    leftSection={<IconMicrophone size={18}/>}
                    onClick={() => navigate('/speech-to-text')}
                >
                    New Recording
                </Button>
            </Group>

            {!user?.verified && (
                <Paper p="md" withBorder bg="orange.0" style={{borderColor: 'var(--mantine-color-orange-5)'}}>
                    <Group gap="xs">
                        <Text size="sm" fw={500} c="orange.8">
                            ⚠️ Email not verified
                        </Text>
                        <Text size="sm" c="dimmed">
                            - Please verify your email to unlock all features
                        </Text>
                    </Group>
                </Paper>
            )}

            <SimpleGrid cols={{base: 1, sm: 2, lg: 4}} spacing="lg">
                <StatsCard
                    title="Total Recordings"
                    value={stats?.total_recordings || 0}
                    description="All time"
                    color="blue"
                    icon={<IconFileText size={32}/>}
                />
                <StatsCard
                    title="Total Duration"
                    value={formatDuration(stats?.total_duration_ms || 0)}
                    description="Total transcribed"
                    color="green"
                    icon={<IconClock size={32}/>}
                />
                <StatsCard
                    title={`${stats?.usage_cycle || 'Monthly'} Usage`}
                    value={`${usagePercent}%`}
                    description={`${stats?.usage_minutes || 0} / ${quotaMinutes} mins`}
                    color="orange"
                    progress={usagePercent}
                />
                <StatsCard
                    title="Avg. Length"
                    value={stats?.average_recording_duration_ms
                        ? formatDuration(Math.round(stats.average_recording_duration_ms))
                        : '0 secs'}
                    description={`${stats?.usage_count || 0} this cycle`}
                    color="violet"
                    icon={<IconTrendingUp size={32}/>}
                />
            </SimpleGrid>

            <Paper p="xl" withBorder>
                <Stack gap="md">
                    <Title order={2} size="h3">
                        Quick Actions
                    </Title>
                    <SimpleGrid cols={{base: 1, sm: 2, md: 3}} spacing="md">
                        <Button
                            variant="light"
                            color="blue"
                            leftSection={<IconMicrophone size={18}/>}
                            onClick={() => navigate('/speech-to-text')}
                            fullWidth
                        >
                            Start Recording
                        </Button>
                        <Button
                            variant="light"
                            color="green"
                            leftSection={<IconFileText size={18}/>}
                            onClick={() => navigate('/recordings')}
                            fullWidth
                        >
                            View Recordings
                        </Button>
                        <Button
                            variant="light"
                            color="violet"
                            leftSection={<IconTrendingUp size={18}/>}
                            onClick={() => navigate('/search')}
                            fullWidth
                        >
                            Search & RAG
                        </Button>
                    </SimpleGrid>
                </Stack>
            </Paper>

            <Paper p="xl" withBorder>
                <Stack gap="md">
                    <Title order={2} size="h3">
                        Recent Activity
                    </Title>
                    <Text c="dimmed" size="sm">
                        {stats?.total_recordings === 0
                            ? 'No recordings yet. Start your first recording to see activity here.'
                            : `You have ${stats?.total_recordings} total recordings with ${formatDuration(stats?.total_duration_ms || 0)} of audio. ${stats?.completed_count} completed, ${stats?.processing_count} processing.`}
                    </Text>
                </Stack>
            </Paper>
        </Stack>
    );
}
