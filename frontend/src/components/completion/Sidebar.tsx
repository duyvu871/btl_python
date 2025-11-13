import { useState } from 'react';
import { ScrollArea, Stack, Text, Badge, Group, Loader, Button, Box, Center } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';
import { useRecordings } from '@/hooks/useRecord';
import { useChatSessions } from '@/hooks/useChat';
import { CreateSessionModal } from './CreateSessionModal';
import { useNavigate } from 'react-router-dom';

interface SidebarProps {
  selectedSession?: string | null;
  onSelectSession?: (sessionId: string) => void;
}

export function Sidebar({ selectedSession, onSelectSession }: SidebarProps) {
  const [searchQuery] = useState('');
  const [modalOpened, setModalOpened] = useState(false);
  const { data: recordingsData, isLoading: isRecordingsLoading } = useRecordings({ status: 'COMPLETED' });
  const { data: sessionsData, isLoading: isSessionsLoading } = useChatSessions(1, 50);
  const navigate = useNavigate();

  const filteredRecordings = recordingsData?.recordings?.filter((recording) =>
    recording.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const sessions = sessionsData?.data || [];

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
          onClick={() => setModalOpened(true)}
        >
          New Chat
        </Button>
      </Box>

      <ScrollArea flex={1} className={"p-5"}>
        <Stack gap={10}>
          {isSessionsLoading ? (
            <Center py="xl">
              <Loader size="sm" />
            </Center>
          ) : sessions.length === 0 ? (
            <Text c="dimmed" size="sm" ta="center" py="xl">
              No chat sessions yet. Create one to get started!
            </Text>
          ) : (
            sessions.map((session) => (
              <Box
                key={session.id}
                p="md"
                className={"cursor-pointer bg-zinc-500/10 hover:bg-blue-300/10 rounded-md"}
                bd={selectedSession === session.id ? 'l' : undefined}
                bg={selectedSession === session.id ? 'blue.9' : undefined}
                onClick={() => navigate(`/search/${session.id}`)}
              >
                <Text fw={500} size="sm" truncate="end" mb="xs">
                  {session.title}
                </Text>

                <Group gap="xs" wrap="nowrap">
                  <Badge size="xs" variant="filled" fw={700}>
                    {session.messages?.length || 0} MESSAGES
                  </Badge>
                  <Text size="xs" c="dimmed" flex={1}>
                    {formatDate(session.updated_at)}
                  </Text>
                </Group>
              </Box>
            ))
          )}
        </Stack>
      </ScrollArea>

      <CreateSessionModal
        opened={modalOpened}
        onClose={() => setModalOpened(false)}
      />
    </Stack>
  );
}
