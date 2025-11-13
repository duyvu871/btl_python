import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { chatApi, type CreateSessionRequest, type UpdateSessionRequest, type CreateMessageRequest, type ChatCompletionRequest } from '@/api/chat';
import { notifications } from '@mantine/notifications';

/**
 * Hook to list chat sessions
 */
export const useChatSessions = (page: number = 1, per_page: number = 20, recording_id?: string) => {
  return useQuery({
    queryKey: ['chat', 'sessions', page, per_page, recording_id],
    queryFn: () => chatApi.listSessions(page, per_page, recording_id),
    staleTime: 1000 * 60, // 1 minute
  });
};

/**
 * Hook to get chat session detail
 */
export const useChatSessionDetail = (session_id?: string) => {
  return useQuery({
    queryKey: ['chat', 'session', session_id],
    queryFn: () => chatApi.getSessionDetail(session_id!),
    enabled: !!session_id,
    staleTime: 1000 * 60, // 1 minute
  });
};

/**
 * Hook to get session messages
 */
export const useChatMessages = (session_id?: string) => {
  return useQuery({
    queryKey: ['chat', 'messages', session_id],
    queryFn: () => chatApi.getSessionMessages(session_id!),
    enabled: !!session_id,
    staleTime: 1000 * 30, // 30 seconds
  });
};

/**
 * Hook to create chat session
 */
export const useCreateChatSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSessionRequest) => chatApi.createSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] });
      notifications.show({
        title: 'Success',
        message: 'Chat session created',
        color: 'green',
      });
    },
    onError: (error: any) => {
      notifications.show({
        title: 'Failed to create session',
        message: error.message || 'An error occurred',
        color: 'red',
      });
    },
  });
};

/**
 * Hook to update session title
 */
export const useUpdateChatSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ session_id, data }: { session_id: string; data: UpdateSessionRequest }) =>
      chatApi.updateSessionTitle(session_id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] });
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', variables.session_id] });
      notifications.show({
        title: 'Success',
        message: 'Session updated',
        color: 'green',
      });
    },
    onError: (error: any) => {
      notifications.show({
        title: 'Failed to update session',
        message: error.message || 'An error occurred',
        color: 'red',
      });
    },
  });
};

/**
 * Hook to delete chat session
 */
export const useDeleteChatSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (session_id: string) => chatApi.deleteSession(session_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] });
      notifications.show({
        title: 'Success',
        message: 'Session deleted',
        color: 'green',
      });
    },
    onError: (error: any) => {
      notifications.show({
        title: 'Failed to delete session',
        message: error.message || 'An error occurred',
        color: 'red',
      });
    },
  });
};

/**
 * Hook to add message to session
 */
export const useAddChatMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ session_id, data }: { session_id: string; data: CreateMessageRequest }) =>
      chatApi.addMessage(session_id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', variables.session_id] });
    },
    onError: (error: any) => {
      notifications.show({
        title: 'Failed to add message',
        message: error.message || 'An error occurred',
        color: 'red',
      });
    },
  });
};

/**
 * Hook to ask question and get AI response
 */
export const useAskQuestion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ session_id, data }: { session_id: string; data: ChatCompletionRequest }) =>
      chatApi.askQuestion(session_id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', variables.session_id] });
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', variables.session_id] });
    },
    onError: (error: any) => {
      notifications.show({
        title: 'Failed to get AI response',
        message: error.message || 'An error occurred',
        color: 'red',
      });
    },
  });
};

/**
 * Combined hook for chat management
 */
export const useChat = (session_id?: string) => {
  const sessions = useChatSessions();
  const sessionDetail = useChatSessionDetail(session_id);
  const messages = useChatMessages(session_id);
  const createSession = useCreateChatSession();
  const updateSession = useUpdateChatSession();
  const deleteSession = useDeleteChatSession();
  const addMessage = useAddChatMessage();
  const askQuestion = useAskQuestion();

  return {
    // Queries
    sessions,
    sessionDetail,
    messages,

    // Mutations
    createSession,
    updateSession,
    deleteSession,
    addMessage,
    askQuestion,

    // Helper properties
    isLoading: sessions.isLoading || sessionDetail.isLoading || messages.isLoading,
    currentMessages: messages.data || [],
    currentSession: sessionDetail.data,
  };
};
