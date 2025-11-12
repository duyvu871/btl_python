import { useState, useRef, useEffect } from 'react';
import { ScrollArea, Textarea, Button, Stack, Text, Group, Loader, Box, Paper, Center } from '@mantine/core';
import { IconSend, IconDownload } from '@tabler/icons-react';
import { useRecording, useTranscript } from '@/hooks/useRecord';

interface ChatAreaProps {
  sessionId: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function ChatArea({ sessionId }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: recording, isLoading: isRecordingLoading } = useRecording(sessionId);
  const { data: transcript, isLoading: isTranscriptLoading } = useTranscript(sessionId, 'text');

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  useEffect(() => {
    setMessages([]);
    if (transcript && recording) {
      setMessages([
        {
          id: '1',
          role: 'assistant',
          content: `Hello! I've analyzed the transcript from your recording. Feel free to ask me any questions about the content.`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [sessionId, transcript, recording]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `This is a simulated response. In production, this would call your RAG API with the question: "${userMessage.content}" and context from the transcript.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isRecordingLoading || isTranscriptLoading) {
    return (
      <Center h="100%">
        <Loader size="lg" />
      </Center>
    );
  }

  if (!recording) {
    return (
      <Center h="100%">
        <Text c="dimmed">Recording not found</Text>
      </Center>
    );
  }

  const formatDuration = (durationMs: number) => {
    const minutes = Math.floor(durationMs / 60000);
    return `${minutes} MINUTES`;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box h="100%" display="flex" style={{ flexDirection: 'column' }}>
      <Paper p="lg" withBorder radius={0}>
        <Group justify="space-between" align="center">
          <Box>
            <Text fw={600} size="xl" mb="xs">
              {recording.name}
            </Text>
            <Group gap="md">
              <Text size="sm" c="blue" fw={600}>
                {formatDuration(recording.duration_ms)}
              </Text>
              <Text size="sm" c="dimmed">
                Session ID: {sessionId.slice(0, 8)}
              </Text>
            </Group>
          </Box>
          <Button
            leftSection={<IconDownload size={16} />}
            variant="light"
            size="sm"
          >
            Export
          </Button>
        </Group>
      </Paper>

      <ScrollArea flex={1} p="xl" viewportRef={scrollRef}>
        <Stack gap="lg" maw={1024} mx="auto">
          {messages.map((message) => (
            <Box key={message.id}>
              {message.role === 'assistant' ? (
                <Paper p="md" withBorder>
                  <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </Text>
                  <Text size="xs" c="dimmed" mt="xs">
                    {formatTime(message.timestamp)}
                  </Text>
                </Paper>
              ) : (
                <Group justify="flex-end">
                  <Paper p="md" withBorder bg="blue" c="white" maw="80%">
                    <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </Text>
                    <Text size="xs" mt="xs" opacity={0.8}>
                      {formatTime(message.timestamp)}
                    </Text>
                  </Paper>
                </Group>
              )}
            </Box>
          ))}
          {isLoading && (
            <Paper p="md" withBorder>
              <Loader size="xs" />
            </Paper>
          )}
        </Stack>
      </ScrollArea>

      <Paper p="lg" withBorder radius={0}>
        <Box maw={1024} mx="auto">
          <Group gap="xs" align="flex-end">
            <Textarea
              flex={1}
              placeholder="Ask a question about the transcript..."
              value={inputValue}
              onChange={(e) => setInputValue(e.currentTarget.value)}
              onKeyDown={handleKeyPress}
              disabled={isLoading}
              autosize
              minRows={1}
              maxRows={4}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              rightSection={<IconSend size={16} />}
              size="md"
            >
              Send
            </Button>
          </Group>
        </Box>
      </Paper>
    </Box>
  );
}

