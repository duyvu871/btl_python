import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Container,
  Title,
  Paper,
  Table,
  Badge,
  Button,
  Group,
  TextInput,
  Select,
  Pagination,
  Modal,
  Stack,
  Text,
  Grid,
  Card,
  ActionIcon,
  Tooltip,
  LoadingOverlay,
  Switch,
  Checkbox, PasswordInput
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconEdit,
  IconTrash,
  IconSearch,
  IconUserCheck,
  IconUserX,
  IconUsers,
  IconUserShield,
} from '@tabler/icons-react';
import { adminApi, type User, type UserUpdateData, type UserCreateData } from '@/api/admin';
import { notifications } from '@mantine/notifications';
import { ApiError } from '@/api/base';

export function AdminDashboardPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string | null>(null);
  const [verifiedFilter, setVerifiedFilter] = useState<string | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());

  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [editModalOpened, { open: openEditModal, close: closeEditModal }] = useDisclosure(false);
  const [deleteModalOpened, { open: openDeleteModal, close: closeDeleteModal }] = useDisclosure(false);
  const [createModalOpened, { open: openCreateModal, close: closeCreateModal }] = useDisclosure(false);

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: adminApi.getStats,
  });

  // Fetch users
  const { data: usersData, isLoading } = useQuery({
    queryKey: ['admin', 'users', page, pageSize, search, roleFilter, verifiedFilter],
    queryFn: () => adminApi.getUsers({
      page,
      page_size: pageSize,
      search: search || undefined,
      role: roleFilter || undefined,
      verified: verifiedFilter === 'true' ? true : verifiedFilter === 'false' ? false : undefined,
    }),
  });

  // Update user mutation
  const updateUserMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UserUpdateData }) =>
      adminApi.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      notifications.show({
        title: 'Success',
        message: 'User updated successfully',
        color: 'green',
      });
      closeEditModal();
    },
    onError: (error) => {
      notifications.show({
        title: 'Error',
        message: error instanceof ApiError ? error.message : 'Failed to update user',
        color: 'red',
      });
    },
  });

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      notifications.show({
        title: 'Success',
        message: 'User deleted successfully',
        color: 'green',
      });
      closeDeleteModal();
      setSelectedUser(null);
    },
    onError: (error) => {
      notifications.show({
        title: 'Error',
        message: error instanceof ApiError ? error.message : 'Failed to delete user',
        color: 'red',
      });
    },
  });

  // Create user mutation
  const createUserMutation = useMutation({
    mutationFn: adminApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      notifications.show({
        title: 'Success',
        message: 'User created successfully',
        color: 'green',
      });
      closeCreateModal();
    },
    onError: (error) => {
      notifications.show({
        title: 'Error',
        message: error instanceof ApiError ? error.message : 'Failed to create user',
        color: 'red',
      });
    },
  });

  // Bulk action mutation
  const bulkActionMutation = useMutation({
    mutationFn: ({ userIds, action }: { userIds: string[]; action: string }) =>
      adminApi.bulkAction(userIds, action),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      notifications.show({
        title: 'Success',
        message: `Bulk action completed: ${data.updated_count} users updated`,
        color: 'green',
      });
      setSelectedUsers(new Set());
    },
    onError: (error) => {
      notifications.show({
        title: 'Error',
        message: error instanceof ApiError ? error.message : 'Failed to perform bulk action',
        color: 'red',
      });
    },
  });

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    openEditModal();
  };

  const handleDeleteUser = (user: User) => {
    setSelectedUser(user);
    openDeleteModal();
  };

  const handleCreateUser = () => {
    openCreateModal();
  };

  const handleUpdateUser = (data: UserUpdateData) => {
    if (selectedUser) {
      updateUserMutation.mutate({ userId: selectedUser.id, data });
    }
  };

  const handleConfirmDelete = () => {
    if (selectedUser) {
      deleteUserMutation.mutate(selectedUser.id);
    }
  };

  const handleBulkAction = (action: string) => {
    if (selectedUsers.size === 0) {
      notifications.show({
        title: 'No users selected',
        message: 'Please select at least one user',
        color: 'orange',
      });
      return;
    }
    bulkActionMutation.mutate({ userIds: Array.from(selectedUsers), action });
  };

  const toggleSelectUser = (userId: string) => {
    const newSelected = new Set(selectedUsers);
    if (newSelected.has(userId)) {
      newSelected.delete(userId);
    } else {
      newSelected.add(userId);
    }
    setSelectedUsers(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedUsers.size === usersData?.users.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(usersData?.users.map(u => u.id) || []));
    }
  };

  const totalPages = usersData ? Math.ceil(usersData.total / pageSize) : 0;

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="xl">Admin Dashboard</Title>

      {/* Statistics Cards */}
      <Grid mb="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
                  Total Users
                </Text>
                <Text size="xl" fw={700}>
                  {stats?.total_users || 0}
                </Text>
              </div>
              <IconUsers size={40} stroke={1.5} />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
                  Verified
                </Text>
                <Text size="xl" fw={700}>
                  {stats?.verified_users || 0}
                </Text>
              </div>
              <IconUserCheck size={40} stroke={1.5} color="green" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
                  Unverified
                </Text>
                <Text size="xl" fw={700}>
                  {stats?.unverified_users || 0}
                </Text>
              </div>
              <IconUserX size={40} stroke={1.5} color="orange" />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
                  Admins
                </Text>
                <Text size="xl" fw={700}>
                  {stats?.admin_users || 0}
                </Text>
              </div>
              <IconUserShield size={40} stroke={1.5} color="blue" />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Filters and Search */}
      <Paper shadow="sm" p="md" mb="md">
        <Group justify="space-between" mb="md">
          <Button leftSection={<IconUsers size={16} />} onClick={handleCreateUser}>
            Create User
          </Button>
        </Group>
        <Group>
          <TextInput
            placeholder="Search by email or username"
            leftSection={<IconSearch size={16} />}
            value={search}
            onChange={(e) => setSearch(e.currentTarget.value)}
            style={{ flex: 1 }}
          />
          <Select
            placeholder="Filter by role"
            data={[
              { value: '', label: 'All Roles' },
              { value: 'user', label: 'User' },
              { value: 'admin', label: 'Admin' },
            ]}
            value={roleFilter}
            onChange={setRoleFilter}
            clearable
            style={{ width: 150 }}
          />
          <Select
            placeholder="Filter by status"
            data={[
              { value: '', label: 'All Status' },
              { value: 'true', label: 'Verified' },
              { value: 'false', label: 'Unverified' },
            ]}
            value={verifiedFilter}
            onChange={setVerifiedFilter}
            clearable
            style={{ width: 150 }}
          />
        </Group>
      </Paper>

      {/* Bulk Actions */}
      {selectedUsers.size > 0 && (
        <Paper shadow="sm" p="md" mb="md" bg="blue.0">
          <Group justify="space-between">
            <Text size="sm" fw={500}>
              {selectedUsers.size} user(s) selected
            </Text>
            <Group gap="xs">
              <Button
                size="xs"
                variant="light"
                onClick={() => handleBulkAction('verify')}
                loading={bulkActionMutation.isPending}
              >
                Verify
              </Button>
              <Button
                size="xs"
                variant="light"
                color="orange"
                onClick={() => handleBulkAction('unverify')}
                loading={bulkActionMutation.isPending}
              >
                Unverify
              </Button>
              <Button
                size="xs"
                variant="light"
                color="blue"
                onClick={() => handleBulkAction('promote')}
                loading={bulkActionMutation.isPending}
              >
                Promote to Admin
              </Button>
              <Button
                size="xs"
                variant="light"
                color="gray"
                onClick={() => handleBulkAction('demote')}
                loading={bulkActionMutation.isPending}
              >
                Demote to User
              </Button>
              <Button
                size="xs"
                variant="light"
                color="red"
                onClick={() => handleBulkAction('delete')}
                loading={bulkActionMutation.isPending}
              >
                Delete
              </Button>
            </Group>
          </Group>
        </Paper>
      )}

      {/* Users Table */}
      <Paper shadow="sm" p="md" pos="relative">
        <LoadingOverlay visible={isLoading} />
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>
                <Checkbox
                  checked={selectedUsers.size === usersData?.users.length && usersData?.users.length > 0}
                  indeterminate={selectedUsers.size > 0 && selectedUsers.size < (usersData?.users.length || 0)}
                  onChange={toggleSelectAll}
                />
              </Table.Th>
              <Table.Th>Username</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Role</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Created At</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {usersData?.users.map((user) => (
              <Table.Tr key={user.id}>
                <Table.Td>
                  <Checkbox
                    checked={selectedUsers.has(user.id)}
                    onChange={() => toggleSelectUser(user.id)}
                  />
                </Table.Td>
                <Table.Td>{user.user_name}</Table.Td>
                <Table.Td>{user.email}</Table.Td>
                <Table.Td>
                  <Badge color={user.role === 'admin' ? 'blue' : 'gray'}>
                    {user.role.toUpperCase()}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Badge color={user.verified ? 'green' : 'orange'}>
                    {user.verified ? 'Verified' : 'Unverified'}
                  </Badge>
                </Table.Td>
                <Table.Td>{new Date(user.created_at).toLocaleDateString()}</Table.Td>
                <Table.Td>
                  <Group gap="xs">
                    <Tooltip label="Edit user">
                      <ActionIcon
                        variant="light"
                        color="blue"
                        onClick={() => handleEditUser(user)}
                      >
                        <IconEdit size={16} />
                      </ActionIcon>
                    </Tooltip>
                    <Tooltip label="Delete user">
                      <ActionIcon
                        variant="light"
                        color="red"
                        onClick={() => handleDeleteUser(user)}
                      >
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {usersData && usersData.total > 0 && (
          <Group justify="center" mt="xl">
            <Pagination
              value={page}
              onChange={setPage}
              total={totalPages}
            />
          </Group>
        )}

        {usersData && usersData.total === 0 && (
          <Text ta="center" c="dimmed" py="xl">
            No users found
          </Text>
        )}
      </Paper>

      {/* Edit User Modal */}
      <EditUserModal
        opened={editModalOpened}
        onClose={closeEditModal}
        user={selectedUser}
        onSubmit={handleUpdateUser}
        isLoading={updateUserMutation.isPending}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpened}
        onClose={closeDeleteModal}
        title="Confirm Delete"
        centered
      >
        <Stack>
          <Text>
            Are you sure you want to delete user <strong>{selectedUser?.email}</strong>?
            This action cannot be undone.
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={closeDeleteModal}>
              Cancel
            </Button>
            <Button
              color="red"
              onClick={handleConfirmDelete}
              loading={deleteUserMutation.isPending}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Create User Modal */}
      <CreateUserModal
        opened={createModalOpened}
        onClose={closeCreateModal}
        onSubmit={(data) => createUserMutation.mutate(data)}
        isLoading={createUserMutation.isPending}
      />
    </Container>
  );
}

// Edit User Modal Component
function EditUserModal({
  opened,
  onClose,
  user,
  onSubmit,
  isLoading,
}: {
  opened: boolean;
  onClose: () => void;
  user: User | null;
  onSubmit: (data: UserUpdateData) => void;
  isLoading: boolean;
}) {
  const [formData, setFormData] = useState<UserUpdateData>({});

  // Update form data when user changes
  useEffect(() => {
    if (user) {
      setFormData({
        user_name: user.user_name,
        email: user.email,
        verified: user.verified,
        role: user.role,
      });
    }
  }, [user]);

  const handleSubmit = () => {
    onSubmit(formData);
  };

  if (!user) return null;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Edit User"
      size="md"
      centered
    >
      <Stack>
        <TextInput
          label="Username"
          value={formData.user_name || ''}
          onChange={(e) => setFormData({ ...formData, user_name: e.currentTarget.value })}
        />
        <TextInput
          label="Email"
          type="email"
          value={formData.email || ''}
          onChange={(e) => setFormData({ ...formData, email: e.currentTarget.value })}
        />
        <Select
          label="Role"
          data={[
            { value: 'user', label: 'User' },
            { value: 'admin', label: 'Admin' },
          ]}
          value={formData.role || user.role}
          onChange={(value) => setFormData({ ...formData, role: value || 'user' })}
        />
        <Switch
          label="Email Verified"
          checked={formData.verified ?? user.verified}
          onChange={(e) => setFormData({ ...formData, verified: e.currentTarget.checked })}
        />
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} loading={isLoading}>
            Save Changes
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

// Create User Modal Component
function CreateUserModal({
  opened,
  onClose,
  onSubmit,
  isLoading,
}: {
  opened: boolean;
  onClose: () => void;
  onSubmit: (data: UserCreateData) => void;
  isLoading: boolean;
}) {
  const [formData, setFormData] = useState<UserCreateData>({
    email: '',
    password: '',
    user_name: '',
    role: 'user',
    verified: false,
  });

  const handleSubmit = () => {
    onSubmit(formData);
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Create User"
      size="md"
      centered
    >
      <Stack>
        <TextInput
          label="Username"
          value={formData.user_name}
          onChange={(e) => setFormData({ ...formData, user_name: e.currentTarget.value })}
        />
        <TextInput
          label="Email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.currentTarget.value })}
          required
        />
        <PasswordInput
          label="Password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.currentTarget.value })}
          required
        />
        <Select
          label="Role"
          data={[
            { value: 'user', label: 'User' },
            { value: 'admin', label: 'Admin' },
          ]}
          value={formData.role}
          onChange={(value) => setFormData({ ...formData, role: value || 'user' })}
        />
        <Switch
          label="Email Verified"
          checked={formData.verified}
          onChange={(e) => setFormData({ ...formData, verified: e.currentTarget.checked })}
        />
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} loading={isLoading}>
            Create User
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
