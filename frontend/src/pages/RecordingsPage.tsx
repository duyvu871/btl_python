import { useState } from 'react';
import {
  Stack,
  Title,
  FileInput,
  Button,
  Group,
  Text,
  Progress,
  Paper,
  Table,
  Badge,
  ActionIcon,
  Menu,
  Select,
  TextInput,
  Modal,
} from '@mantine/core';
import { IconUpload, IconDownload, IconTrash, IconDots, IconSearch, IconFileText, IconFile } from '@tabler/icons-react';
import {
  useRecordings,
  useRecordingStats,
  useCompleteUpload,
  useDeleteRecording,
  useTranscript,
  useSearchSegments,
} from '@/hooks/useRecord';
import { recordApi } from '@/api/record';
import { notifications } from '@mantine/notifications';

export function RecordingsPage() {
  // Upload modal state
  const [uploadModalOpened, setUploadModalOpened] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLanguage, setUploadLanguage] = useState<'vi' | 'en'>('vi');
  const [uploadProgress, setUploadProgress] = useState(0);

  // Combined filter & pagination state (avoid multiple rerenders)
  const [queryParams, setQueryParams] = useState({
    page: 1,
    per_page: 10,
    language: null as string | null,
    status: null as string | null,
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [transcriptModal, setTranscriptModal] = useState<string | null>(null);

  // Queries
  const { data: recordings, isLoading: loadingRecordings } = useRecordings({
    page: queryParams.page,
    per_page: queryParams.per_page,
    language: queryParams.language || undefined,
    status: queryParams.status || undefined,
  });
  const { data: stats } = useRecordingStats();
  const { data: transcript } = useTranscript(transcriptModal || '', 'text');

  // Mutations
  const completeUpload = useCompleteUpload();
  const deleteRecording = useDeleteRecording();
  const searchSegments = useSearchSegments();

  // Handle file upload
  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploadProgress(0);

      await completeUpload.upload(selectedFile, uploadLanguage, (progress) => {
        setUploadProgress(progress);
      });

      notifications.show({
        title: 'Success',
        message: 'File uploaded successfully! Processing will begin shortly.',
        color: 'green',
      });

      // Reset and close modal
      setSelectedFile(null);
      setUploadProgress(0);
      setUploadModalOpened(false);
      setUploadLanguage('vi');
    } catch (error) {
      console.error('Upload error:', error);
      setUploadProgress(0);
    }
  };

  // Handle delete
  const handleDelete = (recordingId: string) => {
    if (confirm('Are you sure you want to delete this recording?')) {
      deleteRecording.mutate(recordingId);
    }
  };

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      const result = await searchSegments.mutateAsync({
        query: searchQuery,
        limit: 20,
      });

      notifications.show({
        title: 'Search Results',
        message: `Found ${result.total_matches} matches`,
        color: 'blue',
      });
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  return (
    <Stack gap="lg">
      <Title order={1}>Recordings</Title>

      {/* Statistics */}
      {stats && (
        <Paper p="md" withBorder>
          <Group justify="space-between">
            <div>
              <Text size="sm" c="dimmed">Total Recordings</Text>
              <Text size="xl" fw={700}>{stats.total_recordings}</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed">Total Duration</Text>
              <Text size="xl" fw={700}>{recordApi.formatDuration(stats.total_duration_ms)}</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed">Completed</Text>
              <Text size="xl" fw={700} c="green">{stats.completed_count}</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed">Processing</Text>
              <Text size="xl" fw={700} c="blue">{stats.processing_count}</Text>
            </div>
          </Group>
        </Paper>
      )}

      {/* Actions & Filters */}
      <Paper p="md" withBorder>
        <Group justify="space-between">
          <Group>
            <Select
              label="Language Filter"
              placeholder="All languages"
              value={queryParams.language}
              onChange={(value) => setQueryParams(prev => ({ ...prev, language: value, page: 1 }))}
              data={[
                { value: 'vi', label: 'Vietnamese' },
                { value: 'en', label: 'English' },
              ]}
              clearable
              style={{ width: 180 }}
            />
            <Select
              label="Status Filter"
              placeholder="All statuses"
              value={queryParams.status}
              onChange={(value) => setQueryParams(prev => ({ ...prev, status: value, page: 1 }))}
              data={[
                { value: 'pending', label: 'Pending' },
                { value: 'processing', label: 'Processing' },
                { value: 'completed', label: 'Completed' },
                { value: 'failed', label: 'Failed' },
              ]}
              clearable
              style={{ width: 180 }}
            />
          </Group>

          <Button
            leftSection={<IconUpload size={18} />}
            onClick={() => setUploadModalOpened(true)}
            size="md"
          >
            Upload Audio File
          </Button>
        </Group>
      </Paper>

      {/* Search Section */}
      <Paper p="md" withBorder>
        <Group>
          <TextInput
            placeholder="Search in transcripts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.currentTarget.value)}
            style={{ flex: 1 }}
            leftSection={<IconSearch size={16} />}
          />
          <Button
            onClick={handleSearch}
            loading={searchSegments.isPending}
            leftSection={<IconSearch size={16} />}
          >
            Search
          </Button>
        </Group>
      </Paper>

      {/* Recordings Table */}
      <Paper p="md" withBorder>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Status</Table.Th>
              <Table.Th>Language</Table.Th>
              <Table.Th>Source</Table.Th>
              <Table.Th>Duration</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {loadingRecordings ? (
              <Table.Tr>
                <Table.Td colSpan={6}>
                  <Text ta="center">Loading...</Text>
                </Table.Td>
              </Table.Tr>
            ) : recordings?.recordings.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={6}>
                  <Text ta="center" c="dimmed">No recordings yet</Text>
                </Table.Td>
              </Table.Tr>
            ) : (
              recordings?.recordings.map((recording) => (
                <Table.Tr key={recording.id}>
                  <Table.Td>
                    <Badge color={recordApi.getStatusColor(recording.status)}>
                      {recordApi.getStatusLabel(recording.status)}
                    </Badge>
                  </Table.Td>
                  <Table.Td>{recording.language.toUpperCase()}</Table.Td>
                  <Table.Td>{recording.source}</Table.Td>
                  <Table.Td>{recordApi.formatDuration(recording.duration_ms)}</Table.Td>
                  <Table.Td>{new Date(recording.created_at).toLocaleDateString()}</Table.Td>
                  <Table.Td>
                    <Menu position="bottom-end">
                      <Menu.Target>
                        <ActionIcon variant="subtle">
                          <IconDots size={16} />
                        </ActionIcon>
                      </Menu.Target>
                      <Menu.Dropdown>
                        <Menu.Item
                          leftSection={<IconFileText size={16} />}
                          onClick={() => setTranscriptModal(recording.id)}
                          disabled={recording.status !== 'completed'}
                        >
                          View Transcript
                        </Menu.Item>
                        <Menu.Item
                          leftSection={<IconDownload size={16} />}
                          disabled={recording.status !== 'completed'}
                        >
                          Download
                        </Menu.Item>
                        <Menu.Divider />
                        <Menu.Item
                          color="red"
                          leftSection={<IconTrash size={16} />}
                          onClick={() => handleDelete(recording.id)}
                        >
                          Delete
                        </Menu.Item>
                      </Menu.Dropdown>
                    </Menu>
                  </Table.Td>
                </Table.Tr>
              ))
            )}
          </Table.Tbody>
        </Table>

        {/* Pagination */}
        {recordings && recordings.total_pages > 1 && (
          <Group justify="center" mt="md">
            <Button
              onClick={() => setQueryParams(prev => ({ ...prev, page: prev.page - 1 }))}
              disabled={queryParams.page === 1}
            >
              Previous
            </Button>
            <Text>
              Page {queryParams.page} of {recordings.total_pages}
            </Text>
            <Button
              onClick={() => setQueryParams(prev => ({ ...prev, page: prev.page + 1 }))}
              disabled={queryParams.page >= recordings.total_pages}
            >
              Next
            </Button>
          </Group>
        )}
      </Paper>

      {/* Upload Modal */}
      <Modal
        opened={uploadModalOpened}
        onClose={() => {
          if (!completeUpload.isLoading) {
            setUploadModalOpened(false);
            setSelectedFile(null);
            setUploadProgress(0);
          }
        }}
        title="Upload Audio File"
        size="md"
        closeOnClickOutside={!completeUpload.isLoading}
        closeOnEscape={!completeUpload.isLoading}
        centered
      >
        <Stack gap="md">
          <Select
            label="Language"
            description="Select the language of the audio"
            value={uploadLanguage}
            onChange={(value) => setUploadLanguage(value as 'vi' | 'en')}
            data={[
              { value: 'vi', label: '🇻🇳 Vietnamese' },
              { value: 'en', label: '🇬🇧 English' },
            ]}
            required
          />

          <FileInput
            label="Audio File"
            description="Select an audio file to upload (WAV, MP3, etc.)"
            placeholder="Click to select file"
            value={selectedFile}
            onChange={setSelectedFile}
            accept="audio/*"
            leftSection={<IconFile size={16} />}
            required
          />

          {selectedFile && (
            <Paper p="sm" bg="blue.0" withBorder>
              <Group gap="xs">
                <IconFile size={16} />
                <div style={{ flex: 1 }}>
                  <Text size="sm" fw={500}>{selectedFile.name}</Text>
                  <Text size="xs" c="dimmed">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </Text>
                </div>
              </Group>
            </Paper>
          )}

          {uploadProgress > 0 && uploadProgress < 100 && (
            <div>
              <Text size="sm" mb="xs">Uploading: {uploadProgress.toFixed(0)}%</Text>
              <Progress value={uploadProgress} animated />
            </div>
          )}

          <Group justify="flex-end" mt="md">
            <Button
              variant="default"
              onClick={() => {
                setUploadModalOpened(false);
                setSelectedFile(null);
                setUploadProgress(0);
              }}
              disabled={completeUpload.isLoading}
            >
              Cancel
            </Button>
            <Button
              leftSection={<IconUpload size={16} />}
              onClick={handleFileUpload}
              loading={completeUpload.isLoading}
              disabled={!selectedFile}
            >
              Upload & Transcribe
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Transcript Modal */}
      <Modal
        opened={!!transcriptModal}
        onClose={() => setTranscriptModal(null)}
        title="Transcript"
        size="lg"
      >
        {transcript && (
          <Paper p="md" bg="gray.0">
            <Text style={{ whiteSpace: 'pre-wrap' }}>{transcript.transcript}</Text>
          </Paper>
        )}
      </Modal>
    </Stack>
  );
}

