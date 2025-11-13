import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Paper, Text, Group, Button, Loader, Center, Stack } from '@mantine/core';
import { IconArrowLeft, IconEdit, IconTrash } from '@tabler/icons-react';
import { useChatSessionDetail, useChatMessages, useDeleteChatSession } from '@/hooks/useChat';
import { ChatArea } from '@/components/completion/ChatArea';

export default function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const { data: session, isLoading: isSessionLoading, error: sessionError } = useChatSessionDetail(sessionId);
  const { data: messages, isLoading: isMessagesLoading } = useChatMessages(sessionId);
  const { mutate: deleteSession, isPending: isDeleting } = useDeleteChatSession();

  if (isSessionLoading || isMessagesLoading) {
    return (
      <Center h="100%">
        <Loader size="lg" />
      </Center>
    );
  }

  if (sessionError || !session) {
    return (
      <Center h="100%">
        <Box ta="center">
          <Text size="lg" fw={500} mb="xs" c="red">
            Session not found
          </Text>
          <Text size="sm" c="dimmed" mb="lg">
            The chat session you're looking for doesn't exist or you don't have access to it.
          </Text>
          <Button onClick={() => navigate('/search')} variant="light">
            Back to Chat
          </Button>
        </Box>
      </Center>
    );
  }

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this chat session? This action cannot be undone.')) {
      deleteSession(sessionId!, {
        onSuccess: () => {
          navigate('/search');
        },
      });
    }
  };

  return (
    <Stack h="100%" gap={0}>
      {/* Header */}
      <Paper p="lg" withBorder radius={0}>
        <Group justify="space-between" align="center">
          <Group gap="md">
            <Button
              variant="subtle"
              leftSection={<IconArrowLeft size={16} />}
              onClick={() => navigate('/search')}
            >
              Back
            </Button>
            <Box>
              <Text fw={600} size="xl" mb="xs">
                {session.title}
              </Text>
              <Group gap="md">
                <Text size="sm" c="dimmed">
                  Session ID: {sessionId?.slice(0, 8)}
                </Text>
                <Text size="sm" c="dimmed">
                  {messages?.length || 0} messages
                </Text>
              </Group>
            </Box>
          </Group>

          <Group gap="sm">
            <Button
              variant="light"
              leftSection={<IconEdit size={16} />}
              onClick={() => {
                // TODO: Implement edit title modal
                console.log('Edit title');
              }}
            >
              Edit Title
            </Button>
            <Button
              variant="light"
              color="red"
              leftSection={<IconTrash size={16} />}
              onClick={handleDelete}
              loading={isDeleting}
            >
              Delete
            </Button>
          </Group>
        </Group>
      </Paper>

      {/* Chat Area */}
      <Box flex={1} style={{ overflow: 'hidden' }}>
        {sessionId && <ChatArea sessionId={sessionId} />}
      </Box>
    </Stack>
  );
}
