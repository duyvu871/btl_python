import { useState } from 'react';
import {
  Dialog,
  Stack,
  TextInput,
  Select,
  Button,
  Group,
  Loader,
  Text,
  Center,
} from '@mantine/core';
import { useRecordings } from '@/hooks/useRecord';
import { useCreateChatSession } from '@/hooks/useChat';
import { useNavigate } from 'react-router-dom';

interface CreateSessionModalProps {
  opened: boolean;
  onClose: () => void;
}

export function CreateSessionModal({
  opened,
  onClose,
}: CreateSessionModalProps) {
  const [title, setTitle] = useState('');
  const [selectedRecordingId, setSelectedRecordingId] = useState<string | null>(null);
  const { data, isLoading: isRecordingsLoading } = useRecordings({ status: 'COMPLETED' });
  const { mutate: createSession, isPending } = useCreateChatSession();
  const navigate = useNavigate();

  const recordingOptions = data?.recordings?.map((recording) => ({
    value: recording.id,
    label: `${recording.name} (${(recording.duration_ms / 60000).toFixed(2)} min)`,
  })) || [];

  const handleCreate = async () => {
    if (!selectedRecordingId || !title.trim()) {
      return;
    }

    createSession(
      {
        recording_id: selectedRecordingId,
        title: title.trim(),
      },
      {
        onSuccess: (session) => {
          setTitle('');
          setSelectedRecordingId(null);
          onClose();
          navigate(`/search/${session.id}`); // Navigate to the new session page
        },
      }
    );
  };

  const handleClose = () => {
    setTitle('');
    setSelectedRecordingId(null);
    onClose();
  };

  return (
    <Dialog
      opened={opened}
      onClose={handleClose}
      size="md"
      radius="lg"
      withCloseButton
      title="Create New Chat Session"
    >
      <Stack gap="lg">
        <Stack gap="xs">
          <Text size="sm" fw={500}>
            Select Transcript
          </Text>
          {isRecordingsLoading ? (
            <Center py="lg">
              <Loader size="sm" />
            </Center>
          ) : recordingOptions.length === 0 ? (
            <Text c="dimmed" size="sm" ta="center" py="lg">
              No completed recordings available
            </Text>
          ) : (
            <Select
              placeholder="Choose a recording..."
              data={recordingOptions}
              value={selectedRecordingId}
              onChange={setSelectedRecordingId}
              searchable
              clearable
              disabled={isPending}
            />
          )}
        </Stack>

        <Stack gap="xs">
          <Text size="sm" fw={500}>
            Chat Title
          </Text>
          <TextInput
            placeholder="Enter a title for this chat session..."
            value={title}
            onChange={(e) => setTitle(e.currentTarget.value)}
            disabled={isPending}
          />
        </Stack>

        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!selectedRecordingId || !title.trim()}
            loading={isPending}
          >
            Create Session
          </Button>
        </Group>
      </Stack>
    </Dialog>
  );
}
