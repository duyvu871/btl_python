import { useState } from 'react';
import {Burger, Group, Box, Paper, Text, Center, Stack} from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import { Sidebar } from '@/components/completion/Sidebar';
import { cn } from "@/lib/utils.ts";

export default function CompletionPage({}) {
  const [opened, setOpened] = useState(false);
  const isMobile = useMediaQuery('(max-width: 768px)');

  return (
    <Stack h="100%">
      {isMobile && (
        <Paper p="md" withBorder radius={0} h={60}>
          <Group justify="space-between" w="100%">
            <Burger opened={opened} onClick={() => setOpened(!opened)} size="sm" />
          </Group>
        </Paper>
      )}

      <Box flex={1} className={"flex h-full overflow-hidden"}>
        <Box
          w={280}
          className={cn("relative left-0 bottom-0 z-20", {
            'absolute top-16  shadow-lg': isMobile,
            'relative': !isMobile,
            'hidden': isMobile && !opened
          })}
        >
          <Sidebar />
        </Box>

        <Box flex={1} style={{ overflow: 'hidden' }}>
          <Center h="100%">
            <Box ta="center">
              <Text size="lg" fw={500} mb="xs">
                Welcome to Chat
              </Text>
              <Text size="sm" c="dimmed">
                Select a chat session from the sidebar to start chatting
              </Text>
            </Box>
          </Center>
        </Box>
      </Box>
    </Stack>
  );
}
