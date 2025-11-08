import { Title, Text, Button, Stack, SimpleGrid, Paper, Group, Badge } from '@mantine/core';
import { IconMicrophone, IconFileText, IconClock, IconTrendingUp } from '@tabler/icons-react';
import { useAuth } from '@/providers/AuthProvider';
import { useNavigate } from 'react-router-dom';
import { StatsCard } from '@/components/StatsCard';

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'admin';

  // Mock data - replace with real API calls
  const stats = {
    totalRecordings: 24,
    totalDuration: '2h 45m',
    monthlyUsage: 65, // percentage
    averageLength: '6m 52s',
  };

  return (
    <Stack gap="lg">
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
          leftSection={<IconMicrophone size={18} />}
          onClick={() => navigate('/speech-to-text')}
        >
          New Recording
        </Button>
      </Group>

      {!user?.verified && (
        <Paper p="md" withBorder bg="orange.0" style={{ borderColor: 'var(--mantine-color-orange-5)' }}>
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

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="lg">
        <StatsCard
          title="Total Recordings"
          value={stats.totalRecordings}
          description="All time"
          color="blue"
          icon={<IconFileText size={32} />}
        />
        <StatsCard
          title="Total Duration"
          value={stats.totalDuration}
          description="Total transcribed"
          color="green"
          icon={<IconClock size={32} />}
        />
        <StatsCard
          title="Monthly Usage"
          value={`${stats.monthlyUsage}%`}
          description="of your quota"
          color="orange"
          progress={stats.monthlyUsage}
        />
        <StatsCard
          title="Avg. Length"
          value={stats.averageLength}
          description="per recording"
          color="violet"
          icon={<IconTrendingUp size={32} />}
        />
      </SimpleGrid>

      <Paper p="xl" withBorder>
        <Stack gap="md">
          <Title order={2} size="h3">
            Quick Actions
          </Title>
          <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
            <Button
              variant="light"
              color="blue"
              leftSection={<IconMicrophone size={18} />}
              onClick={() => navigate('/speech-to-text')}
              fullWidth
            >
              Start Recording
            </Button>
            <Button
              variant="light"
              color="green"
              leftSection={<IconFileText size={18} />}
              onClick={() => navigate('/recordings')}
              fullWidth
            >
              View Recordings
            </Button>
            <Button
              variant="light"
              color="violet"
              leftSection={<IconTrendingUp size={18} />}
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
            No recent recordings. Start your first recording to see activity here.
          </Text>
        </Stack>
      </Paper>
    </Stack>
  );
}
