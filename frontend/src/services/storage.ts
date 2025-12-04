/**
 * Local Storage Service
 * Manages chat history and session persistence
 */

import type { ChatHistory, Message } from '../types/chat';

const STORAGE_KEYS = {
  CHAT_HISTORY: 'rag_chatbot_history',
  CURRENT_SESSION: 'rag_chatbot_session',
  API_KEY: 'rag_chatbot_api_key',
  SETTINGS: 'rag_chatbot_settings',
} as const;

class StorageService {
  /**
   * Generate a unique session ID
   */
  generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current session ID or create new one
   */
  getCurrentSessionId(): string {
    let sessionId = localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION);
    if (!sessionId) {
      sessionId = this.generateSessionId();
      localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION, sessionId);
    }
    return sessionId;
  }

  /**
   * Create a new session
   */
  createNewSession(): string {
    const sessionId = this.generateSessionId();
    localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION, sessionId);
    return sessionId;
  }

  /**
   * Save chat history
   */
  saveChatHistory(sessionId: string, messages: Message[]) {
    const allHistory = this.getAllChatHistory();
    
    if (messages.length === 0) {
      // Remove session if no messages
      delete allHistory[sessionId];
    } else {
      // Get first user message as title
      const firstUserMessage = messages.find(m => m.role === 'user');
      const title = firstUserMessage 
        ? firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '')
        : 'New Chat';

      allHistory[sessionId] = {
        id: sessionId,
        title,
        timestamp: new Date().toISOString(),
        messages: messages.map(m => ({
          ...m,
          timestamp: m.timestamp.toISOString(),
        })),
        lastMessage: messages[messages.length - 1]?.content,
      };
    }
    
    localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(allHistory));
  }

  /**
   * Get all chat history
   */
  getAllChatHistory(): Record<string, any> {
    const stored = localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);
    return stored ? JSON.parse(stored) : {};
  }

  /**
   * Get chat history list for sidebar
   */
  getChatHistoryList(): ChatHistory[] {
    const allHistory = this.getAllChatHistory();
    return Object.values(allHistory)
      .map((chat: any) => ({
        id: chat.id,
        title: chat.title,
        timestamp: this.formatTimestamp(chat.timestamp),
        lastMessage: chat.lastMessage,
      }))
      .sort((a: any, b: any) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
  }

  /**
   * Load messages for a session
   */
  loadSession(sessionId: string): Message[] | null {
    const allHistory = this.getAllChatHistory();
    const session = allHistory[sessionId];
    
    if (!session) return null;
    
    return session.messages.map((m: any) => ({
      ...m,
      timestamp: new Date(m.timestamp),
    }));
  }

  /**
   * Delete a chat session
   */
  deleteSession(sessionId: string) {
    const allHistory = this.getAllChatHistory();
    delete allHistory[sessionId];
    localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(allHistory));
  }

  /**
   * Save API key
   */
  saveApiKey(apiKey: string) {
    localStorage.setItem(STORAGE_KEYS.API_KEY, apiKey);
  }

  /**
   * Get API key
   */
  getApiKey(): string | null {
    return localStorage.getItem(STORAGE_KEYS.API_KEY);
  }

  /**
   * Format timestamp to relative time
   */
  private formatTimestamp(timestamp: string): string {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString();
  }

  /**
   * Clear all data
   */
  clearAll() {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  }
}

// Export singleton instance
export const storageService = new StorageService();
