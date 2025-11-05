import { Container, Title, Text, Button, Stack, Paper, Group, Badge } from '@mantine/core';
import { IconShield } from '@tabler/icons-react';
import { useAuth } from '@/providers/AuthProvider';
import { useNavigate } from 'react-router-dom';

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'admin';

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <Container size="md" style={{ width: '100%', maxWidth: 768 }}>
      <Paper shadow="md" p="xl" radius="md" withBorder>
        <Stack gap="md">
          <Title order={1}>Dashboard</Title>

          <div>
            <Group gap="sm">
              <Text size="lg" fw={600}>Welcome, {user?.user_name || user?.email}!</Text>
              {isAdmin && (
                <Badge color="blue" leftSection={<IconShield size={14} />}>
                  Admin
                </Badge>
              )}
            </Group>
            <Text c="dimmed" size="sm">
              Account Status: {user?.verified ? '✅ Verified' : '⚠️ Not Verified'}
            </Text>
          </div>

          {!user?.verified && (
            <Text c="orange" size="sm">
              Please verify your email to unlock all features.
            </Text>
          )}

          <Group gap="sm">
            {isAdmin && (
              <Button
                variant="filled"
                color="blue"
                leftSection={<IconShield size={16} />}
                onClick={() => navigate('/admin')}
              >
                Admin Panel
              </Button>
            )}
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          </Group>
        </Stack>
      </Paper>
    </Container>
  );
}
