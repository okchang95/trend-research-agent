export interface User {
  user_id: string;
  name: string;
}

export interface Thread {
  thread_id: string;
  user_id: string;
  title: string;
  status: 'idle' | 'generating' | 'completed' | 'error';
  created_at: string;
  updated_at: string;
}

export interface Message {
  message_id?: string;
  thread_id: string;
  role: 'user' | 'assistant';
  message: string;
  ended_node?: string;
  findings?: Finding[];
  timestamp: string;
}

export interface SSEEvent {
  type: string;
  [key: string]: any;
}

export interface ThreadEvent extends SSEEvent {
  type: 'thread';
  thread_id: string;
  title?: string;
}

export interface SessionEvent extends SSEEvent {
  type: 'session';
  session_id: string;
}

export interface NodeStartEvent extends SSEEvent {
  type: 'node_start';
  node: string;
}

export interface NodeCompleteEvent extends SSEEvent {
  type: 'node_complete';
  node: string;
  state: any;
}

export interface ResearchStatusEvent extends SSEEvent {
  type: 'research_status';
  message: string;
  results?: SearchResult[];
}

export interface ResearchFindingsEvent extends SSEEvent {
  type: 'research_findings';
  findings: Finding[];
}

export interface TextChunkEvent extends SSEEvent {
  type: 'text_chunk';
  char: string;
}

export interface FinalEvent extends SSEEvent {
  type: 'final';
  state: {
    answer: string;
    current_node?: string;
    is_clarified?: boolean;
    subject?: string;
    scope?: string;
    findings?: Finding[];
  };
}

export interface ScopingCompleteEvent extends SSEEvent {
  type: 'scoping_complete';
}

export interface ErrorEvent extends SSEEvent {
  type: 'error';
  error: string;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet?: string;
  content?: string;
}

export interface Finding {
  type?: string;
  query?: string;
  tool_type?: string;
  results?: SearchResult[];
  summary?: string;
  iteration?: number;
}

export interface StreamingState {
  currentText: string;
  sessionId: string | null;
  scopingComplete: boolean;
  nodeStatus: {
    name: string;
    status: 'pending' | 'in_progress' | 'completed';
  } | null;
  researchStatus: {
    message: string;
    results: SearchResult[];
  } | null;
  findings: Finding[];
}
