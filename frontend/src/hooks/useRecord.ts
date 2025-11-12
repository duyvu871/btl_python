import {useMutation, useQuery, useQueryClient, type UseQueryOptions} from '@tanstack/react-query';
import {
    recordApi,
    type ListRecordingsRequest,
    type SearchSegmentsRequest,
    type UpdateRecordingRequest
} from '@/api/record';
import {notifications} from '@mantine/notifications';

// ============================================================================
// Query Keys
// ============================================================================

export const recordKeys = {
    all: ['recordings'] as const,
    lists: () => [...recordKeys.all, 'list'] as const,
    list: (params?: ListRecordingsRequest) => [...recordKeys.lists(), params] as const,
    details: () => [...recordKeys.all, 'detail'] as const,
    detail: (id: string) => [...recordKeys.details(), id] as const,
    stats: () => [...recordKeys.all, 'stats'] as const,
    transcript: (id: string, format: string) => [...recordKeys.all, 'transcript', id, format] as const,
    search: (query: string) => [...recordKeys.all, 'search', query] as const,
};

// ============================================================================
// Queries
// ============================================================================

/**
 * Hook to fetch a specific recording
 */
export function useRecording(recordingId: string, options?: Omit<UseQueryOptions, 'queryKey' | 'queryFn'>) {
    return useQuery({
        queryKey: recordKeys.detail(recordingId),
        queryFn: () => recordApi.getRecording(recordingId),
        enabled: !!recordingId,
        ...options,
    });
}

/**
 * Hook to fetch list of recordings with filters
 */
export function useRecordings(params?: ListRecordingsRequest) {
    return useQuery({
        queryKey: recordKeys.list(params),
        queryFn: () => recordApi.listRecordings(params),
    });
}

/**
 * Hook to fetch recording statistics
 */
export function useRecordingStats(enabled: boolean = true) {
    return useQuery({
        queryKey: recordKeys.stats(),
        queryFn: () => recordApi.getRecordingStats(),
        enabled,
    });
}

/**
 * Hook to fetch transcript
 */
export function useTranscript(recordingId: string, format: 'text' | 'json' | 'srt' | 'vtt' = 'text') {
    return useQuery({
        queryKey: recordKeys.transcript(recordingId, format),
        queryFn: () => recordApi.getTranscript(recordingId, format),
        enabled: !!recordingId,
    });
}

// ============================================================================
// Mutations
// ============================================================================

/**
 * Hook to upload a recording
 */
export function useUploadRecording() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({language, name}: { language: 'vi' | 'en'; name?: string }) =>
            recordApi.uploadRecording(language, name),
        onSuccess: () => {
            // Invalidate recordings list
            void queryClient.invalidateQueries({queryKey: recordKeys.lists()});
            void queryClient.invalidateQueries({queryKey: recordKeys.stats()});
        },
        onError: (error: Error) => {
            notifications.show({
                title: 'Upload Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Hook to upload audio file to presigned URL (POST form)
 */
export function useUploadAudioFile() {
    return useMutation({
        mutationFn: ({
                         uploadUrl,
                         uploadFields,
                         file,
                         onProgress,
                     }: {
            uploadUrl: string;
            uploadFields: Record<string, string>;
            file: File;
            onProgress?: (progress: number) => void;
        }) => recordApi.uploadAudioFile(uploadUrl, uploadFields, file, onProgress),
        onError: (error: Error) => {
            notifications.show({
                title: 'File Upload Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Hook to update a recording
 */
export function useUpdateRecording() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({recordingId, data}: { recordingId: string; data: UpdateRecordingRequest }) =>
            recordApi.updateRecording(recordingId, data),
        onSuccess: (_, variables) => {
            // Invalidate specific recording and list
            queryClient.invalidateQueries({queryKey: recordKeys.detail(variables.recordingId)});
            queryClient.invalidateQueries({queryKey: recordKeys.lists()});

            notifications.show({
                title: 'Success',
                message: 'Recording updated successfully',
                color: 'green',
            });
        },
        onError: (error: Error) => {
            notifications.show({
                title: 'Update Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Hook to delete a recording
 */
export function useDeleteRecording() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (recordingId: string) => recordApi.deleteRecording(recordingId),
        onSuccess: (data) => {
            // Invalidate recordings list and stats
            queryClient.invalidateQueries({queryKey: recordKeys.lists()});
            queryClient.invalidateQueries({queryKey: recordKeys.stats()});

            notifications.show({
                title: 'Success',
                message: data.message,
                color: 'green',
            });
        },
        onError: (error: Error) => {
            notifications.show({
                title: 'Delete Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Hook to search segments
 */
export function useSearchSegments() {
    return useMutation({
        mutationFn: (request: SearchSegmentsRequest) => recordApi.searchSegments(request),
        onError: (error: Error) => {
            notifications.show({
                title: 'Search Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Hook to regenerate upload URL for failed/expired uploads
 */
export function useRegenerateUploadUrl() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (recordingId: string) => recordApi.regenerateUploadUrl(recordingId),
        onSuccess: (data) => {
            // Invalidate recording detail
            queryClient.invalidateQueries({queryKey: recordKeys.detail(data.recording_id)});

            notifications.show({
                title: 'Success',
                message: data.message,
                color: 'green',
            });
        },
        onError: (error: Error) => {
            notifications.show({
                title: 'Regenerate URL Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Hook to get audio download/play URL
 */
export function useGetAudioUrl() {
    return useMutation({
        mutationFn: (recordingId: string) => recordApi.getAudioUrl(recordingId),
        onError: (error: Error) => {
            notifications.show({
                title: 'Get Audio URL Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Hook to mark upload as completed and queue transcription
 */
export function useMarkUploadCompleted() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (recordingId: string) => recordApi.markUploadCompleted(recordingId),
        onSuccess: (data) => {
            // Invalidate recordings list and stats
            queryClient.invalidateQueries({queryKey: recordKeys.lists()});
            queryClient.invalidateQueries({queryKey: recordKeys.stats()});
            queryClient.invalidateQueries({queryKey: recordKeys.detail(data.recording_id)});

            notifications.show({
                title: 'Success',
                message: data.message,
                color: 'green',
            });
        },
        onError: (error: Error) => {
            notifications.show({
                title: 'Upload Completion Failed',
                message: error.message,
                color: 'red',
            });
        },
    });
}

/**
 * Combined hook for full upload flow (create recording + upload file + mark completed)
 */
export function useCompleteUpload() {
    const uploadRecording = useUploadRecording();
    const uploadFile = useUploadAudioFile();
    const markCompleted = useMarkUploadCompleted();

    return {
        uploadRecording,
        uploadFile,
        markCompleted,
        isLoading: uploadRecording.isPending || uploadFile.isPending || markCompleted.isPending,

        /**
         * Complete upload flow: create recording, upload file, then mark as completed
         */
        async upload(
            file: File,
            language: 'vi' | 'en' = 'vi',
            onProgress?: (progress: number) => void,
            name?: string
        ) {
            try {
                // Step 1: Create recording and get presigned POST data
                const uploadData = await uploadRecording.mutateAsync({language, name});

                // Step 2: Upload file via form POST with required fields
                await uploadFile.mutateAsync({
                    uploadUrl: uploadData.upload_url,
                    uploadFields: uploadData.upload_fields  ,
                    file,
                    onProgress,
                });

                // Step 3: Mark upload as completed and queue transcription
                const completedData = await markCompleted.mutateAsync(uploadData.recording_id);

                return {
                    ...uploadData,
                    job_id: completedData.job_id,
                };
            } catch (error) {
                throw error;
            }
        },
    };
}
