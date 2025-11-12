import {AppShell, Burger, Group, Text, NavLink, Box} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconHome,
  IconMicrophone,
  IconFileText,
  IconSearch,
  IconSettings,
  IconLogout,
  IconShieldCheck,
  IconCreditCard,
} from '@tabler/icons-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { UserMenu } from './UserMenu';

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
    { icon: IconCreditCard, label: 'Subscription', path: '/subscription' },
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
      // padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Text size="xl" fw={700} c="blue">
              Speech Hub
            </Text>
          </Group>

          <UserMenu />
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

      <AppShell.Main style={{ overflow: 'hidden', height: '100dvh' }}>
          <Box h="100%" style={{ overflowY: 'auto' }}>
              {children}
          </Box>
          </AppShell.Main>
    </AppShell>
  );
}


































