import { useState } from 'react';
import {
  Container,
  Title,
  Text,
  Stack,
  Switch,
  Group,
  Divider,
  Box,
  Button,
  Select,
  Card,
  Badge,
} from '@mantine/core';
import { IconMoon, IconSun, IconPalette, IconBell, IconShield, IconUser } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [language, setLanguage] = useState('en');

  const handleThemeToggle = (checked: boolean) => {
    setDarkMode(checked);
    notifications.show({
      title: checked ? 'Dark Mode Enabled' : 'Light Mode Enabled',
      message: `Theme switched to ${checked ? 'dark' : 'light'} mode`,
      color: checked ? 'blue' : 'orange',
      icon: checked ? <IconMoon size={16} /> : <IconSun size={16} />,
    });
  };

  const handleNotificationToggle = (checked: boolean) => {
    setNotificationsEnabled(checked);
    notifications.show({
      title: checked ? 'Notifications Enabled' : 'Notifications Disabled',
      message: `Notifications are now ${checked ? 'enabled' : 'disabled'}`,
      color: checked ? 'green' : 'red',
      icon: <IconBell size={16} />,
    });
  };

  const handleLanguageChange = (value: string | null) => {
    if (!value) return;
    setLanguage(value);
    notifications.show({
      title: 'Language Changed',
      message: `Language switched to ${value === 'en' ? 'English' : 'Vietnamese'}`,
      color: 'blue',
      icon: <IconUser size={16} />,
    });
  };

  return (
    <Container size="md" py="xl">
      <Stack gap="xl">
        {/* Header */}
        <Box>
          <Title order={2} mb="xs">
            Settings
          </Title>
          <Text c="dimmed">
            Customize your experience and preferences
          </Text>
        </Box>

        {/* Appearance Settings */}
        <Card withBorder>
          <Group mb="md">
            <IconPalette size={20} />
            <Title order={4}>Appearance</Title>
          </Group>

          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Box>
                <Text fw={500}>Dark Mode</Text>
                <Text size="sm" c="dimmed">
                  Switch between light and dark themes
                </Text>
              </Box>
              <Switch
                checked={darkMode}
                onChange={(event) => handleThemeToggle(event.currentTarget.checked)}
                size="lg"
              />
            </Group>

            <Divider />

            <Group justify="space-between" align="center">
              <Box>
                <Text fw={500}>Theme Color</Text>
                <Text size="sm" c="dimmed">
                  Choose your preferred color scheme
                </Text>
              </Box>
              <Select
                placeholder="Select theme"
                data={[
                  { value: 'default', label: 'Default' },
                  { value: 'blue', label: 'Blue' },
                  { value: 'green', label: 'Green' },
                  { value: 'purple', label: 'Purple' },
                ]}
                defaultValue="default"
                style={{ width: 120 }}
                onChange={(value) => {
                  if (value) {
                    notifications.show({
                      title: 'Theme Changed',
                      message: `Color scheme switched to ${value}`,
                      color: 'blue',
                      icon: <IconPalette size={16} />,
                    });
                  }
                }}
              />
            </Group>
          </Stack>
        </Card>

        {/* Notifications Settings */}
        <Card withBorder>
          <Group mb="md">
            <IconBell size={20} />
            <Title order={4}>Notifications</Title>
          </Group>

          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Box>
                <Text fw={500}>Push Notifications</Text>
                <Text size="sm" c="dimmed">
                  Receive notifications about your activities
                </Text>
              </Box>
              <Switch
                checked={notificationsEnabled}
                onChange={(event) => handleNotificationToggle(event.currentTarget.checked)}
                size="lg"
              />
            </Group>

            <Divider />

            <Group justify="space-between" align="center">
              <Box>
                <Text fw={500}>Email Notifications</Text>
                <Text size="sm" c="dimmed">
                  Receive email updates about your account
                </Text>
              </Box>
              <Switch
                defaultChecked
                size="lg"
                onChange={(checked) => {
                  notifications.show({
                    title: checked ? 'Email Notifications Enabled' : 'Email Notifications Disabled',
                    message: `Email notifications are now ${checked ? 'enabled' : 'disabled'}`,
                    color: checked ? 'green' : 'red',
                    icon: <IconBell size={16} />,
                  });
                }}
              />
            </Group>
          </Stack>
        </Card>

        {/* Language Settings */}
        <Card withBorder>
          <Group mb="md">
            <IconUser size={20} />
            <Title order={4}>Language & Region</Title>
          </Group>

          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Box>
                <Text fw={500}>Language</Text>
                <Text size="sm" c="dimmed">
                  Choose your preferred language
                </Text>
              </Box>
              <Select
                value={language}
                onChange={handleLanguageChange}
                data={[
                  { value: 'en', label: 'English' },
                  { value: 'vi', label: 'Tiếng Việt' },
                ]}
                style={{ width: 120 }}
              />
            </Group>
          </Stack>
        </Card>

        {/* Privacy & Security */}
        <Card withBorder>
          <Group mb="md">
            <IconShield size={20} />
            <Title order={4}>Privacy & Security</Title>
          </Group>

          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Box>
                <Text fw={500}>Two-Factor Authentication</Text>
                <Text size="sm" c="dimmed">
                  Add an extra layer of security to your account
                </Text>
              </Box>
              <Badge color="orange" variant="light">
                Coming Soon
              </Badge>
            </Group>

            <Divider />

            <Group justify="space-between" align="center">
              <Box>
                <Text fw={500}>Data Export</Text>
                <Text size="sm" c="dimmed">
                  Download your data and chat history
                </Text>
              </Box>
              <Button
                variant="light"
                size="sm"
                onClick={() => {
                  notifications.show({
                    title: 'Data Export Started',
                    message: 'Your data export has been initiated. You will receive an email when ready.',
                    color: 'blue',
                    icon: <IconShield size={16} />,
                  });
                }}
              >
                Export Data
              </Button>
            </Group>
          </Stack>
        </Card>

        {/* Account Actions */}
        <Card withBorder>
          <Title order={4} mb="md">
            Account Actions
          </Title>

          <Stack gap="sm">
            <Button
              variant="light"
              color="red"
              onClick={() => {
                notifications.show({
                  title: 'Account Deletion',
                  message: 'Account deletion feature is not available in demo mode.',
                  color: 'red',
                  icon: <IconShield size={16} />,
                });
              }}
            >
              Delete Account
            </Button>
          </Stack>
        </Card>
      </Stack>
    </Container>
  );
}

