import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  Text,
  TextInput,
  PasswordInput,
  Button,
  Stack,
  Anchor,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconX } from '@tabler/icons-react';
import { useAuth } from '@/providers/AuthProvider';
import { ApiError } from '@/api/base';

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, isRegisterLoading, registerError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    if (registerError) {
      notifications.show({
        title: 'Registration Failed',
        message: registerError instanceof ApiError ? registerError.message : 'Failed to create account',
        color: 'red',
        icon: <IconX size={16} />,
      });
    }
  }, [registerError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      return;
    }

    try {
      await register({ email, password });

      notifications.show({
        title: 'Registration Successful!',
        message: "We've sent a verification code to your email. Redirecting...",
        color: 'green',
        icon: <IconCheck size={16} />,
      });

      // Redirect to verify email page after 2 seconds
      setTimeout(() => {
        navigate(`/verify-email?email=${encodeURIComponent(email)}`);
      }, 2000);
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  return (
    <Container size="xs" style={{ width: '100%', minHeight: "100vh", maxWidth: 420, display: 'flex', alignItems: 'center' }}>
      <Paper shadow="md" p="xl" radius="md" withBorder w={"100%"}>
        <Stack gap="lg">
          <div>
            <Title order={2}>Register</Title>
            <Text c="dimmed" size="sm" mt="xs">
              Create your account to get started
            </Text>
          </div>


          <form onSubmit={handleSubmit}>
            <Stack gap="md">
              <TextInput
                label="Email"
                placeholder="your@email.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <PasswordInput
                label="Password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <PasswordInput
                label="Confirm Password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                error={
                  confirmPassword && password !== confirmPassword
                    ? 'Passwords do not match'
                    : undefined
                }
                required
              />

              <Button
                type="submit"
                fullWidth
                loading={isRegisterLoading}
                disabled={password !== confirmPassword}
              >
                Register
              </Button>
            </Stack>
          </form>

          <Text size="sm" ta="center">
            Already have an account?{' '}
            <Anchor component={Link} to="/login">
              Login
            </Anchor>
          </Text>
        </Stack>
      </Paper>
    </Container>
  );
}
