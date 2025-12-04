/**
 * TypeScript types for the chatbot
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  confidence?: number;
  iterations?: number;
}

export interface Source {
  question: string;
  answer: string;
  metadata: {
    filename: string;
    chunk_index?: number;
    total_chunks?: number;
  };
  score: number;
}

export interface ChatHistory {
  id: string;
  title: string;
  timestamp: string;
  lastMessage?: string;
}

export interface ChatRequest {
  query: string;
  session_id: string;
  max_iterations?: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  confidence: number;
  iterations: number;
  session_id: string;
  query_rewritten?: string;
  retrieval_time_ms?: number;
  generation_time_ms?: number;
  total_time_ms?: number;
}

export interface HealthStatus {
  status: string;
  milvus_status: string;
  milvus_host: string;
  collection_name: string;
  document_count: number;
  system: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
  };
}

export interface FeedbackRequest {
  query: string;
  answer: string;
  rating: number;
  helpful: boolean;
  comment?: string;
  sources_count?: number;
  confidence?: number;
}

export interface UsageStats {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  requests_by_date: Record<string, number>;
}
