import { api } from '@/api/base';

export interface SourceItem {
  text: string;
  metadata: Record<string, any>;
}

export interface ChatMessageRead {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceItem[];
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  created_at: string;
}

export interface ChatSessionRead {
  id: string;
  user_id: string;
  recording_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessageRead[];
}

export interface CreateSessionRequest {
  recording_id: string;
  title?: string;
}

export interface UpdateSessionRequest {
  title: string;
}

export interface CreateMessageRequest {
  content: string;
  role?: 'user' | 'assistant' | 'system';
}

export interface ChatListResponse {
  data: ChatSessionRead[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ChatCompletionRequest {
  query: string;
  top_k?: number;
  score_threshold?: number;
  rerank_top_k?: number;
}

export interface ChatCompletionResponse {
  user_message: ChatMessageRead;
  assistant_message: ChatMessageRead;
}

export const chatApi = {
  // Session endpoints
  createSession: async (data: CreateSessionRequest): Promise<ChatSessionRead> => {
    return api.post<ChatSessionRead>('/api/v1/chats', data);
  },

  listSessions: async (
    page: number = 1,
    per_page: number = 20,
    recording_id?: string
  ): Promise<ChatListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: per_page.toString(),
    });
    if (recording_id) {
      params.append('recording_id', recording_id);
    }
    return api.get<ChatListResponse>(`/api/v1/chats?${params.toString()}`);
  },

  getSessionDetail: async (session_id: string): Promise<ChatSessionRead> => {
    return api.get<ChatSessionRead>(`/api/v1/chats/${session_id}`);
  },

  updateSessionTitle: async (
    session_id: string,
    data: UpdateSessionRequest
  ): Promise<ChatSessionRead> => {
    return api.patch<ChatSessionRead>(`/api/v1/chats/${session_id}`, data);
  },

  deleteSession: async (session_id: string): Promise<void> => {
    return api.delete<void>(`/api/v1/chats/${session_id}`);
  },

  // Message endpoints
  addMessage: async (
    session_id: string,
    data: CreateMessageRequest
  ): Promise<ChatMessageRead> => {
    return api.post<ChatMessageRead>(`/api/v1/chats/${session_id}/messages`, data);
  },

  getSessionMessages: async (session_id: string): Promise<ChatMessageRead[]> => {
    return api.get<ChatMessageRead[]>(`/api/v1/chats/${session_id}/messages`);
  },

  // Ask question and get AI response
  askQuestion: async (
    session_id: string,
    request: ChatCompletionRequest
  ): Promise<ChatCompletionResponse> => {
    return api.post<ChatCompletionResponse>(`/api/v1/chats/${session_id}/ask`, request);
  },
};
