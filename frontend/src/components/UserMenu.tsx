import { Menu, UnstyledButton, Group, Avatar, Text, rem, Badge } from '@mantine/core';
import { IconChevronDown, IconSettings, IconShieldCheck, IconLogout, IconCreditCard } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { useSubscription } from '@/hooks/useSubscription';

export function UserMenu() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { subscription, hasQuota } = useSubscription();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Get current plan name
  const currentPlan = subscription.data?.plan?.name || 'Free';
  const planCode = subscription.data?.plan?.code || 'free';

  // Determine badge color based on plan
  const getPlanBadgeColor = () => {
    if (!hasQuota) return 'red';
    if (planCode === 'premium') return 'yellow';
    if (planCode === 'basic') return 'blue';
    return 'gray';
  };

  return (
    <Menu
      width={260}
      position="bottom-end"
      transitionProps={{ transition: 'pop-top-right' }}
      withinPortal
    >
      <Menu.Target>
        <UnstyledButton>
          <Group gap={7}>
            <Avatar
              src={user?.profile?.avatar_url}
              alt={user?.profile?.name || user?.user_name}
              radius="xl"
              size={32}
            />
            <Text fw={500} size="sm" lh={1} mr={3}>
              {user?.profile?.name || user?.user_name}
            </Text>
            <IconChevronDown style={{ width: rem(12), height: rem(12) }} stroke={1.5} />
          </Group>
        </UnstyledButton>
      </Menu.Target>

      <Menu.Dropdown>
        {/* User Info Section */}
        <Menu.Item
          leftSection={
            <Avatar
              src={user?.profile?.avatar_url}
              alt={user?.profile?.name || user?.user_name}
              radius="xl"
              size={32}
            />
          }
        >
          <div>
            <Text fw={500}>{user?.profile?.name || user?.user_name}</Text>
            <Text size="xs" c="dimmed">
              {user?.email}
            </Text>
          </div>
        </Menu.Item>

        <Menu.Divider />

        {/* Subscription Info */}
        <Menu.Item
          leftSection={<IconCreditCard style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
          onClick={() => navigate('/subscription')}
          rightSection={
            <Badge size="sm" color={getPlanBadgeColor()} variant="light">
              {currentPlan}
            </Badge>
          }
        >
          Subscription
        </Menu.Item>

        <Menu.Item
          leftSection={<IconSettings style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
          onClick={() => navigate('/settings')}
        >
          Settings
        </Menu.Item>

        {/* Admin Section */}
        {user?.role === 'admin' && (
          <>
            <Menu.Divider />
            <Menu.Item
              leftSection={<IconShieldCheck style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
              onClick={() => navigate('/admin')}
            >
              Admin Dashboard
            </Menu.Item>
          </>
        )}

        <Menu.Divider />

        {/* Logout */}
        <Menu.Item
          color="red"
          leftSection={<IconLogout style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
          onClick={handleLogout}
        >
          Logout
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
}

