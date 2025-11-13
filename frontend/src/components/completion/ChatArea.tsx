import { useState, useRef, useEffect } from 'react';
import { ScrollArea, Textarea, Button, Stack, Text, Group, Loader, Box, Paper, Center } from '@mantine/core';
import { IconSend } from '@tabler/icons-react';
import { useChatSessionDetail, useChatMessages, useAskQuestion } from '@/hooks/useChat';

interface ChatAreaProps {
  sessionId: string;
}

export function ChatArea({ sessionId }: ChatAreaProps) {
  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: session, isLoading: isSessionLoading } = useChatSessionDetail(sessionId);
  const { data: messages = [], isLoading: isMessagesLoading } = useChatMessages(sessionId);
  const { mutate: askQuestion, isPending: isAsking } = useAskQuestion();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isAsking) return;

    const content = inputValue;
    setInputValue('');

    askQuestion({
      session_id: sessionId,
      data: {
        query: content,
        top_k: 10,
        score_threshold: 0.1,
        rerank_top_k: 3,
      },
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isSessionLoading || isMessagesLoading) {
    return (
      <Center h="100%">
        <Loader size="lg" />
      </Center>
    );
  }

  if (!session) {
    return (
      <Center h="100%">
        <Text c="dimmed">Session not found</Text>
      </Center>
    );
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box h="100%" display="flex" style={{ flexDirection: 'column' }}>
      {/*<Paper p="lg" withBorder radius={0}>*/}
      {/*  <Group justify="space-between" align="center">*/}
      {/*    <Box>*/}
      {/*      <Text fw={600} size="xl" mb="xs">*/}
      {/*        {session.title}*/}
      {/*      </Text>*/}
      {/*      <Text size="sm" c="dimmed">*/}
      {/*        Session ID: {sessionId.slice(0, 8)}*/}
      {/*      </Text>*/}
      {/*    </Box>*/}
      {/*  </Group>*/}
      {/*</Paper>*/}

      <ScrollArea flex={1} p="xl" viewportRef={scrollRef}>
        <Stack gap="lg" maw={1024} mx="auto">
          {messages.length === 0 ? (
            <Center py="xl">
              <Text c="dimmed" ta="center">
                Start the conversation by asking a question about the transcript
              </Text>
            </Center>
          ) : (
            messages.map((message) => (
              <Box key={message.id}>
                {message.role === 'assistant' ? (
                  <Paper p="md" withBorder>
                    <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </Text>
                    {message.sources && message.sources.length > 0 && (
                      <Box mt="md">
                        <Text size="xs" fw={500} mb="xs">
                          Sources:
                        </Text>
                        <Stack gap="xs">
                          {message.sources.map((source: any, idx: number) => (
                            <Text key={idx} size="xs" c="dimmed" style={{ whiteSpace: 'pre-wrap' }}>
                              "{source.text}"
                            </Text>
                          ))}
                        </Stack>
                      </Box>
                    )}
                    <Text size="xs" c="dimmed" mt="xs">
                      {formatTime(message.created_at)}
                    </Text>
                  </Paper>
                ) : (
                  <Group justify="flex-end">
                    <Paper p="md" withBorder maw="70%" bg="blue.9">
                      <Text size="md" style={{ whiteSpace: 'pre-wrap' }} color={"white"}>
                        {message.content}
                      </Text>
                      <Text size="xs" c="dimmed" mt="xs" ta="right">
                        {formatTime(message.created_at)}
                      </Text>
                    </Paper>
                  </Group>
                )}
              </Box>
            ))
          )}

          {/* Loading indicator for AI response */}
          {isAsking && (
            <Box>
              <Paper p="md" withBorder bg="gray.5">
                <Group gap="sm">
                  <Loader size="sm" />
                  <Text size="sm" c="dimmed">
                    AI is thinking...
                  </Text>
                </Group>
              </Paper>
            </Box>
          )}
        </Stack>
      </ScrollArea>

      <Paper p="lg" withBorder radius={0}>
        <Group gap="md">
          <Textarea
            placeholder="Ask a question about the transcript..."
            value={inputValue}
            onChange={(e) => setInputValue(e.currentTarget.value)}
            onKeyPress={handleKeyPress}
            disabled={isAsking}
            minRows={2}
            maxRows={4}
            flex={1}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isAsking}
            loading={isAsking}
            leftSection={<IconSend size={16} />}
          >
            Send
          </Button>
        </Group>
      </Paper>
    </Box>
  );
}
