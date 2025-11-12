import { useState } from 'react';
import { ScrollArea, Stack, Text, Badge, Group, Loader, Button, Box, Center } from '@mantine/core';
import { IconMicrophone, IconPlus } from '@tabler/icons-react';
import { useRecordings } from '@/hooks/useRecord';

interface SidebarProps {
  selectedSession: string | null;
  onSelectSession: (sessionId: string) => void;
}

export function Sidebar({ selectedSession, onSelectSession }: SidebarProps) {
  const [searchQuery,] = useState('');
  const { data, isLoading } = useRecordings({ status: 'COMPLETED' });

  const filteredRecordings = data?.recordings?.filter((recording) =>
    recording.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const formatDuration = (durationMs: number) => {
    const minutes = Math.floor(durationMs / 60000);
    return `${minutes} MIN`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return `Today ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    } else if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    }
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  return (
    <Stack h="100%" gap={0}>
      <Box p="md">
        <Button
          fullWidth
          leftSection={<IconPlus size={16} />}
          variant="light"
          size="md"
        >
          New Recording
        </Button>
      </Box>

      <ScrollArea flex={1} className={"p-5"}>
        <Stack gap={10}>
          {isLoading ? (
            <Center py="xl">
              <Loader size="sm" />
            </Center>
          ) : filteredRecordings.length === 0 ? (
            <Text c="dimmed" size="sm" ta="center" py="xl">
              {searchQuery ? 'No transcripts found' : 'No transcripts available'}
            </Text>
          ) : (
            filteredRecordings.map((recording) => (
              <Box
                key={recording.id}
                p="md"
                className={"cursor-pointer bg-zinc-500/10 hover:bg-blue-300/10 rounded-md"}
                bd={selectedSession === recording.id ? 'l' : undefined}
                bg={selectedSession === recording.id ? 'blue.9' : undefined}
                onClick={() => onSelectSession(recording.id)}
              >
                <Group gap="xs" mb="xs" wrap="nowrap">
                  <Box p={6}>
                    <IconMicrophone size={14} />
                  </Box>
                  <Text fw={500} size="sm" flex={1} truncate="end">
                    {recording.name}
                  </Text>
                </Group>

                <Group gap="xs" wrap="nowrap">
                  <Badge size="xs" variant="filled" fw={700}>
                    {formatDuration(recording.duration_ms)}
                  </Badge>
                  <Text size="xs" c="dimmed" flex={1}>
                    {formatDate(recording.created_at)}
                  </Text>
                </Group>

                {recording.meta?.description && (
                  <Text size="xs" c="dimmed" mt="xs" lineClamp={2}>
                    {recording.meta.description}
                  </Text>
                )}
              </Box>
            ))
          )}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}

