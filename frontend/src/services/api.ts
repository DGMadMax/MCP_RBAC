/**
 * API Service for Backend Communication
 * Handles all HTTP requests to the FastAPI backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  HealthStatus,
  FeedbackRequest,
  UsageStats
} from '../types/chat';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for RAG queries
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    // Token is set by AuthContext via defaults.headers.common
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.url}`, response.status);
    return response;
  },
  (error: AxiosError) => {
    console.error('❌ Response Error:', error.response?.status, error.message);
    if (error.response?.status === 401) {
      // Token expired or invalid - clear local storage and redirect
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * API Service Class
 */
class APIService {
  /**
   * Send a chat message (Sync)
   * Note: For streaming, use fetchSSE in ChatInterface
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await apiClient.post<ChatResponse>('/chat', request);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment and try again.');
        } else if (error.response?.status === 401) {
          throw new Error('Session expired. Please login again.');
        } else if (error.response?.status === 503) {
          throw new Error('Service temporarily unavailable. Please try again later.');
        } else if (error.response?.data?.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      throw new Error('Failed to send message. Please check your connection.');
    }
  }

  /**
   * Check system health
   */
  async checkHealth(): Promise<HealthStatus> {
    try {
      const response = await apiClient.get<HealthStatus>('/health');
      return response.data;
    } catch (error) {
      throw new Error('Failed to check system health');
    }
  }

  /**
   * Submit feedback for an answer
   */
  async submitFeedback(feedback: FeedbackRequest): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.post<{ success: boolean; message: string }>(
        '/feedback',
        feedback
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 429) {
        throw new Error('Rate limit exceeded. Please wait before submitting more feedback.');
      }
      throw new Error('Failed to submit feedback');
    }
  }

  /**
   * Get usage statistics
   */
  async getUsageStats(days: number = 7): Promise<UsageStats> {
    // Endpoint doesn't exist yet, return mock data or throw
    // For now, returning mock to prevent crash
    return {
      total_requests: 0,
      total_tokens: 0,
      total_cost_usd: 0,
      avg_latency_ms: 0,
      requests_by_date: {}
    };
  }

  /**
   * Get user-specific stats
   */
  async getUserStats(days: number = 30): Promise<any> {
    // Endpoint doesn't exist yet
    return {};
  }
}

// Export singleton instance
export const apiService = new APIService();

// Export for testing and AuthContext
export { apiClient, API_BASE_URL };
