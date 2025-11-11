import { api } from './base';

// ============================================================================
// Types - Recording
// ============================================================================

export interface Recording {
  id: string;
  user_id: string;
  source: 'upload' | 'realtime';
  language: 'vi' | 'en';
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  duration_ms: number;
  created_at: string;
  completed_at?: string;
  meta?: Record<string, any>;
}

export interface RecordingDetail extends Recording {
  segments: Segment[];
  audio_url?: string;
}

export interface SegmentWord {
  id: string;
  segment_id: string;
  text: string;
  start_ms: number;
  end_ms: number;
}

export interface Segment {
  id: string;
  recording_id: string;
  idx: number;
  start_ms: number;
  end_ms: number;
  text: string;
  words: SegmentWord[];
}

export interface RecordingStats {
  total_recordings: number;
  total_duration_ms: number;
  total_duration_minutes: number;
  completed_count: number;
  processing_count: number;
  failed_count: number;
}

// ============================================================================
// Types - Request/Response
// ============================================================================

export interface UploadRecordingResponse {
  recording_id: string;
  upload_url: string;
  upload_fields: Record<string, string>;
  expires_in: number;
}

export interface ListRecordingsRequest {
  page?: number;
  per_page?: number;
  status?: string;
  source?: string;
  language?: string;
}

export interface ListRecordingsResponse {
  recordings: Recording[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface UpdateRecordingRequest {
  language?: 'vi' | 'en';
}

export interface DeleteRecordingResponse {
  recording_id: string;
  message: string;
  deleted_segments_count: number;
}

export interface SearchSegmentsRequest {
  query: string;
  recording_id?: string;
  limit?: number;
}

export interface SearchSegmentsResponse {
  segments: Segment[];
  total_matches: number;
  query: string;
}

export interface GetTranscriptResponse {
  recording_id: string;
  transcript: string;
  format: string;
  segment_count: number;
}

export interface MarkUploadCompletedResponse {
  recording_id: string;
  status: string;
  message: string;
  job_id?: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Upload a recording file for transcription
 * @param language - Language code ('vi' or 'en')
 * @returns Upload URL and recording ID
 */
export async function uploadRecording(language: 'vi' | 'en' = 'vi'): Promise<UploadRecordingResponse> {
  return api.post<UploadRecordingResponse>('api/v1/record/upload', { language });
}

/**
 * Mark an upload as completed and queue it for transcription
 * @param recordingId - Recording UUID
 * @returns Completion status and job ID
 */
export async function markUploadCompleted(recordingId: string): Promise<MarkUploadCompletedResponse> {
  return api.post<MarkUploadCompletedResponse>('api/v1/record/upload/completed', {
    recording_id: recordingId
  });
}

/**
 * Get a specific recording with segments
 * @param recordingId - Recording UUID
 * @returns Recording details with segments
 */
export async function getRecording(recordingId: string): Promise<RecordingDetail> {
  return api.get<RecordingDetail>(`api/v1/record/${recordingId}`);
}

/**
 * List recordings with pagination and filters
 * @param params - Filter and pagination parameters
 * @returns Paginated list of recordings
 */
export async function listRecordings(params?: ListRecordingsRequest): Promise<ListRecordingsResponse> {
  const queryParams = new URLSearchParams();
  
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.per_page) queryParams.append('per_page', params.per_page.toString());
  if (params?.status) queryParams.append('status_filter', params.status);
  if (params?.source) queryParams.append('source', params.source);
  if (params?.language) queryParams.append('language', params.language);
  
  const url = queryParams.toString() ? `api/v1/record?${queryParams}` : 'api/v1/record';
  return api.get<ListRecordingsResponse>(url);
}

/**
 * Get recording statistics for the current user
 * @returns Statistics about user's recordings
 */
export async function getRecordingStats(): Promise<RecordingStats> {
  return api.get<RecordingStats>('api/v1/record/stats');
}

/**
 * Update recording metadata
 * @param recordingId - Recording UUID
 * @param data - Fields to update
 * @returns Updated recording
 */
export async function updateRecording(
  recordingId: string,
  data: UpdateRecordingRequest
): Promise<Recording> {
  return api.put<Recording>(`api/v1/record/${recordingId}`, data);
}

/**
 * Delete a recording and its segments
 * @param recordingId - Recording UUID
 * @returns Deletion confirmation
 */
export async function deleteRecording(recordingId: string): Promise<DeleteRecordingResponse> {
  return api.delete<DeleteRecordingResponse>(`api/v1/record/${recordingId}`);
}

/**
 * Get transcript in various formats
 * @param recordingId - Recording UUID
 * @param format - Output format ('text', 'json', 'srt', 'vtt')
 * @returns Transcript in requested format
 */
export async function getTranscript(
  recordingId: string,
  format: 'text' | 'json' | 'srt' | 'vtt' = 'text'
): Promise<GetTranscriptResponse> {
  return api.get<GetTranscriptResponse>(`api/v1/record/${recordingId}/transcript?format_response=${format}`);
}

/**
 * Search segments by text query
 * @param request - Search parameters
 * @returns Matching segments
 */
export async function searchSegments(request: SearchSegmentsRequest): Promise<SearchSegmentsResponse> {
  return api.post<SearchSegmentsResponse>('api/v1/record/search', request);
}

/**
 * Upload audio file to the presigned POST URL
 * @param uploadUrl - Presigned form POST URL
 * @param fields - Fields returned alongside the URL that must be included in the form
 * @param file - Audio file to upload
 * @param onProgress - Progress callback
 */
export async function uploadAudioFile(
  uploadUrl: string,
  fields: Record<string, string>,
  file: File,
  onProgress?: (progress: number) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const progress = (e.loaded / e.total) * 100;
        onProgress(progress);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed'));
    });

    const formData = new FormData();
    // Append all required fields first
    Object.entries(fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    // Append file as the last field, named 'file' per S3 form POST convention
    formData.append('file', file);

    xhr.open('POST', uploadUrl);
    // Let the browser set the multipart boundary; do not set Content-Type manually
    xhr.send(formData);
  });
}

/**
 * Helper function to format duration
 * @param ms - Duration in milliseconds
 * @returns Formatted duration string (e.g., "2h 45m", "6m 30s")
 */
export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  } else if (minutes > 0) {
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Helper function to get status color
 * @param status - Recording status
 * @returns Mantine color name
 */
export function getStatusColor(status: Recording['status']): string {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'green';
    case 'processing':
      return 'blue';
    case 'pending':
      return 'yellow';
    case 'failed':
      return 'red';
    default:
      return 'gray';
  }
}

/**
 * Helper function to get status label
 * @param status - Recording status
 * @returns Human-readable status
 */
export function getStatusLabel(status: Recording['status']): string {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'Completed';
    case 'processing':
      return 'Processing';
    case 'pending':
      return 'Pending';
    case 'failed':
      return 'Failed';
    default:
      return 'Unknown';
  }
}

// Export all as recordApi
export const recordApi = {
  uploadRecording,
  getRecording,
  listRecordings,
  getRecordingStats,
  updateRecording,
  deleteRecording,
  getTranscript,
  searchSegments,
  markUploadCompleted,
  uploadAudioFile,
  formatDuration,
  getStatusColor,
  getStatusLabel,
};
