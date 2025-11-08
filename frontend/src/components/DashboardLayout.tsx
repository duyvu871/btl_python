import { AppShell, Burger, Group, Text, NavLink, Avatar, Menu, UnstyledButton, rem } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconHome,
  IconMicrophone,
  IconFileText,
  IconSearch,
  IconSettings,
  IconLogout,
  IconChevronDown,
  IconShieldCheck,
} from '@tabler/icons-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItems = [
    { icon: IconHome, label: 'Dashboard', path: '/dashboard' },
    { icon: IconMicrophone, label: 'Speech to Text', path: '/speech-to-text' },
    { icon: IconFileText, label: 'Recordings', path: '/recordings' },
    { icon: IconSearch, label: 'Search & RAG', path: '/search' },
    { icon: IconSettings, label: 'Settings', path: '/settings' },
  ];

  // Add admin link if user is admin
  if (user?.role === 'admin') {
    navItems.push({
      icon: IconShieldCheck,
      label: 'Admin Dashboard',
      path: '/admin',
    });
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 300,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Text size="xl" fw={700} c="blue">
              Speech Hub
            </Text>
          </Group>

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

              <Menu.Item
                leftSection={<IconSettings style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
                onClick={() => navigate('/settings')}
              >
                Settings
              </Menu.Item>

              {user?.role === 'admin' && (
                <Menu.Item
                  leftSection={<IconShieldCheck style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
                  onClick={() => navigate('/admin')}
                >
                  Admin Dashboard
                </Menu.Item>
              )}

              <Menu.Divider />

              <Menu.Item
                color="red"
                leftSection={<IconLogout style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
                onClick={handleLogout}
              >
                Logout
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <AppShell.Section grow>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              active={location.pathname === item.path}
              label={item.label}
              leftSection={<item.icon size="1.2rem" stroke={1.5} />}
              onClick={() => {
                navigate(item.path);
                if (opened) toggle();
              }}
              variant="subtle"
            />
          ))}
        </AppShell.Section>

        <AppShell.Section>
          <NavLink
            label="Logout"
            leftSection={<IconLogout size="1.2rem" stroke={1.5} />}
            onClick={handleLogout}
            color="red"
            variant="subtle"
          />
        </AppShell.Section>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}

