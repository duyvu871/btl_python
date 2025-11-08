import { Card, Text, Group, RingProgress, Stack } from '@mantine/core';

interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  color?: string;
  icon?: React.ReactNode;
  progress?: number;
}

export function StatsCard({ title, value, description, color = 'blue', icon, progress }: StatsCardProps) {
  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Group justify="space-between" align="flex-start">
        <Stack gap="xs" style={{ flex: 1 }}>
          <Text size="sm" c="dimmed" fw={500}>
            {title}
          </Text>
          <Text size="xl" fw={700}>
            {value}
          </Text>
          {description && (
            <Text size="xs" c="dimmed">
              {description}
            </Text>
          )}
        </Stack>

        {progress !== undefined ? (
          <RingProgress
            size={80}
            roundCaps
            thickness={8}
            sections={[{ value: progress, color }]}
            label={
              <Text c={color} fw={700} ta="center" size="xs">
                {progress}%
              </Text>
            }
          />
        ) : (
          icon && (
            <div style={{ color: `var(--mantine-color-${color}-6)` }}>
              {icon}
            </div>
          )
        )}
      </Group>
    </Card>
  );
}

