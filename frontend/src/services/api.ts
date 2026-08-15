import { HealthStatus, AgentInfo, ChatResponse, ChatMessage } from '../types';

const API_BASE = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    let errorMsg = 'Request failed';
    try {
      const error = await response.json();
      errorMsg = error.detail || error.error || errorMsg;
    } catch {
      errorMsg = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

export const api = {
  // Health
  health: (): Promise<HealthStatus> => request<HealthStatus>('/health'),

  // Agents
  agents: (): Promise<AgentInfo[]> => request<AgentInfo[]>('/agents'),
  agent: (agentId: string): Promise<AgentInfo> => request<AgentInfo>(`/agents/${agentId}`),
  createAgent: (data: Partial<AgentInfo>): Promise<AgentInfo> =>
    request<AgentInfo>('/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Chat
  chat: (message: string, provider: string = 'openai'): Promise<ChatResponse> =>
    request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, provider }),
    }),

  // Voices
  voices: (): Promise<{ voices: { name: string; description: string }[] }> =>
    request<{ voices: { name: string; description: string }[] }>('/voice/voices'),

  // TTS
  tts: (text: string, voice?: string): Promise<any> =>
    request<any>('/voice/tts', {
      method: 'POST',
      body: JSON.stringify({ text, voice }),
    }),

  // Providers
  providers: (): Promise<{ providers: any[] }> =>
    request<{ providers: any[] }>('/chat/providers'),

  // Director AI
  directorScene: (data?: any): Promise<any> =>
    request<any>('/agents/director/scene', {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),

  directorCharacters: (): Promise<any[]> =>
    request<any[]>('/agents/director/characters/linhfeng'),

  directorWorlds: (): Promise<any> =>
    request<any>('/agents/director/worlds/ancient-world'),

  directorEpisodes: (): Promise<any> =>
    request<any>('/agents/director/episodes/ep001'),

  // Pipeline
  pipelineStatus: (): Promise<any> => request<any>('/pipeline/status'),
  runPipeline: (data: any): Promise<any> =>
    request<any>('/pipeline/run', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  lipSync: (data: any): Promise<any> =>
    request<any>('/pipeline/lip-sync', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

export default api;
