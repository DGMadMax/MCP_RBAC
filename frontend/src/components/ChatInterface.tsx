import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, User, Menu, MessageSquare, Plus, Mic, ThumbsUp, ThumbsDown, Copy, Check, LogOut } from 'lucide-react';
import { apiService, API_BASE_URL } from '../services/api';
import { storageService } from '../services/storage';
import { useAuth } from '../context/AuthContext';
import type { Message, ChatHistory, Source } from '../types/chat';

const ThinkingIndicator = ({ status }: { status?: string }) => {
  return (
    <div className="flex gap-3 justify-start">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="rounded-2xl px-4 py-3 bg-gray-100 dark:bg-gray-800">
        <div className="flex flex-col gap-2">
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-pink-500 via-orange-500 to-blue-500 animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
          {status && (
            <span className="text-xs text-gray-500 dark:text-gray-400 animate-pulse">
              {status}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

const SourceCard = ({ source }: { source: string }) => {
  // Parse source string if it's JSON or formatted
  let displaySource = source;
  try {
    if (typeof source === 'string' && (source.startsWith('{') || source.startsWith('['))) {
      const parsed = JSON.parse(source);
      displaySource = parsed.filename || parsed.url || source;
    }
  } catch (e) { }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-xs">
      <div className="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500 flex-shrink-0">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
        <span className="font-medium text-gray-700 dark:text-gray-300 truncate max-w-[200px]" title={displaySource}>
          {displaySource}
        </span>
      </div>
    </div>
  );
};

const ChatMessage = ({ message, onFeedback }: { message: Message; onFeedback?: (messageId: string, helpful: boolean) => void }) => {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<boolean | null>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = (helpful: boolean) => {
    setFeedback(helpful);
    onFeedback?.(message.id, helpful);
  };

  return (
    <div className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      {message.role === 'assistant' && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}
      <div className="flex flex-col max-w-[80%] md:max-w-[70%]">
        <div
          className={`rounded-2xl px-4 py-3 ${message.role === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 dark:bg-gray-800'
            }`}
        >
          <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>

          {/* Show metadata for assistant messages */}
          {message.role === 'assistant' && (message.confidence !== undefined || message.iterations !== undefined) && (
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
              {message.confidence !== undefined && (
                <span className="mr-3">Confidence: {message.confidence}</span>
              )}
            </div>
          )}
        </div>

        {/* Sources */}
        {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-2">
            <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
              Sources ({message.sources.length}):
            </p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source: any, idx) => (
                <SourceCard key={idx} source={source.filename || source} />
              ))}
            </div>
          </div>
        )}

        {/* Action buttons for assistant messages */}
        {message.role === 'assistant' && (
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="Copy response"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-green-500" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-gray-500" />
              )}
            </button>
            <button
              onClick={() => handleFeedback(true)}
              className={`p-1.5 rounded-lg transition-colors ${feedback === true
                ? 'bg-green-100 dark:bg-green-900'
                : 'hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              title="Helpful"
            >
              <ThumbsUp className={`w-3.5 h-3.5 ${feedback === true ? 'text-green-600' : 'text-gray-500'}`} />
            </button>
            <button
              onClick={() => handleFeedback(false)}
              className={`p-1.5 rounded-lg transition-colors ${feedback === false
                ? 'bg-red-100 dark:bg-red-900'
                : 'hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              title="Not helpful"
            >
              <ThumbsDown className={`w-3.5 h-3.5 ${feedback === false ? 'text-red-600' : 'text-gray-500'}`} />
            </button>
          </div>
        )}
      </div>
      {message.role === 'user' && (
        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  );
};

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingStatus, setThinkingStatus] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { user, logout } = useAuth();

  // Initialize session and load history
  useEffect(() => {
    const currentSession = storageService.getCurrentSessionId();
    setSessionId(currentSession);

    // Try to load messages from current session
    const savedMessages = storageService.loadSession(currentSession);
    if (savedMessages) {
      setMessages(savedMessages);
    }

    // Load chat history list
    loadChatHistory();
  }, []);

  // Save messages whenever they change
  useEffect(() => {
    if (sessionId) {
      storageService.saveChatHistory(sessionId, messages);
      loadChatHistory();
    }
  }, [messages, sessionId]);

  const loadChatHistory = () => {
    const history = storageService.getChatHistoryList();
    setChatHistory(history);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking, thinkingStatus]);

  const handleSend = async () => {
    if (!input.trim() || isThinking) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsThinking(true);
    setThinkingStatus('Initializing...');
    setError(null);

    // Create message ID for the assistant response
    const assistantMessageId = (Date.now() + 1).toString();
    let messageAdded = false;

    try {
      // Use fetch for SSE streaming
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: userMessage.content,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader available');

      let accumulatedContent = '';
      let sources: any[] = [];
      let confidence: any = undefined;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'status') {
                setThinkingStatus(data.message);
              } else if (data.type === 'chunk') {
                accumulatedContent += data.content;

                // Add message on first chunk, then update
                if (!messageAdded) {
                  const assistantMessage: Message = {
                    id: assistantMessageId,
                    role: 'assistant',
                    content: accumulatedContent,
                    timestamp: new Date(),
                  };
                  setMessages((prev) => [...prev, assistantMessage]);
                  messageAdded = true;
                } else {
                  // Update the message
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  ));
                }
              } else if (data.type === 'sources') {
                sources = data.sources;
                if (messageAdded) {
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, sources: sources }
                      : msg
                  ));
                }
              } else if (data.type === 'done') {
                setIsThinking(false);
                setThinkingStatus('');
              } else if (data.type === 'error') {
                throw new Error(data.message);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }

    } catch (err) {
      console.error('Chat error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');

      // Add error message if no response was received yet
      if (!messageAdded) {
        const errorMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'An error occurred'}. Please try again.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else {
        // Update existing message with error
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: `${msg.content}\n\nError: ${err instanceof Error ? err.message : 'An error occurred'}` }
            : msg
        ));
      }
    } finally {
      setIsThinking(false);
      setThinkingStatus('');
    }
  };

  const handleFeedback = async (messageId: string, helpful: boolean) => {
    const message = messages.find(m => m.id === messageId);
    if (!message) return;

    const userMessage = messages.find(m =>
      m.role === 'user' &&
      messages.indexOf(m) < messages.indexOf(message)
    );

    if (!userMessage) return;

    try {
      await apiService.submitFeedback({
        query: userMessage.content,
        answer: message.content,
        rating: helpful ? 5 : 1,
        helpful,
        sources_count: message.sources?.length || 0,
        confidence: message.confidence,
      });

      console.log('✅ Feedback submitted successfully');
    } catch (err) {
      console.error('❌ Failed to submit feedback:', err);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startNewChat = () => {
    const newSessionId = storageService.createNewSession();
    setSessionId(newSessionId);
    setMessages([]);
    setError(null);
  };

  const loadChatSession = (historySessionId: string) => {
    const savedMessages = storageService.loadSession(historySessionId);
    if (savedMessages) {
      setMessages(savedMessages);
      setSessionId(historySessionId);
      localStorage.setItem('rag_chatbot_session', historySessionId);
      setSidebarOpen(false);
    }
  };

  const deleteChat = (historySessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    storageService.deleteSession(historySessionId);
    loadChatHistory();

    // If deleted current session, start new chat
    if (historySessionId === sessionId) {
      startNewChat();
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      {/* Sidebar */}
      <div
        className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0`}
      >
        <div className="flex flex-col h-full">
          <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-gray-900 dark:text-white">Chats</span>
            </div>
            <button
              onClick={startNewChat}
              className="h-9 w-9 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 relative group flex items-center justify-center focus:outline-none"
              title="New chat"
            >
              <Plus className="w-5 h-5 text-gray-700 dark:text-gray-300" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {chatHistory.length === 0 ? (
              <div className="text-center text-gray-500 dark:text-gray-400 text-sm mt-4">
                No chat history yet
              </div>
            ) : (
              chatHistory.map((chat) => (
                <div
                  key={chat.id}
                  className={`group relative w-full text-left p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors mb-1 ${chat.id === sessionId ? 'bg-gray-100 dark:bg-gray-800' : ''
                    }`}
                >
                  <button
                    onClick={() => loadChatSession(chat.id)}
                    className="w-full text-left"
                  >
                    <div className="font-medium text-sm truncate text-gray-900 dark:text-white pr-8">
                      {chat.title}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {chat.timestamp}
                    </div>
                  </button>
                  <button
                    onClick={(e) => deleteChat(chat.id, e)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 dark:hover:bg-red-900 transition-all"
                    title="Delete chat"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500">
                      <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="p-4 border-t border-gray-200 dark:border-gray-800">
            <div className="w-full flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user?.full_name || 'User'}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user?.role}
                </div>
              </div>
              <button
                onClick={logout}
                className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 p-4 flex items-center justify-between">
          <button
            className="lg:hidden h-9 w-9 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center justify-center"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Menu className="h-5 w-5" />
          </button>
          <h1 className="text-lg font-semibold absolute left-1/2 transform -translate-x-1/2 text-gray-900 dark:text-white">
            {messages.length === 0 ? 'New chat' : 'Chat'}
          </h1>
          <button
            onClick={startNewChat}
            className="ml-auto h-9 w-9 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 relative group flex items-center justify-center focus:outline-none"
            title="New chat"
          >
            <Plus className="w-5 h-5 text-gray-700 dark:text-gray-300" />
          </button>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 p-3">
            <p className="text-sm text-red-600 dark:text-red-400 text-center">
              ⚠️ {error}
            </p>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="w-24 h-24 mb-6 rounded-full bg-gradient-to-br from-blue-500 via-blue-600 to-purple-600 flex items-center justify-center shadow-lg">
                <Bot className="w-12 h-12 text-white" />
              </div>
              <h1 className="text-3xl md:text-4xl font-normal mb-3 bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
                Hi, I am HR AI Assistant
              </h1>
              <p className="text-lg md:text-xl text-gray-500 dark:text-gray-400 font-light">
                How can I help you today?
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} onFeedback={handleFeedback} />
            ))
          )}
          {isThinking && <ThinkingIndicator status={thinkingStatus} />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white dark:bg-gray-950 p-4 relative">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-center bg-gray-100 dark:bg-gray-800 rounded-full px-4 py-3 relative shadow-sm hover:shadow-md transition-all duration-200" style={{
              border: '1.5px solid rgba(59, 130, 246, 0.4)',
              boxShadow: '0 0 10px rgba(59, 130, 246, 0.2), 0 0 20px rgba(59, 130, 246, 0.1)'
            }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Message HR AI Assistant..."
                disabled={isThinking}
                className="flex-1 bg-transparent border-none outline-none text-sm placeholder:text-gray-500 dark:placeholder:text-gray-400 text-gray-900 dark:text-white disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isThinking}
                className="h-9 w-9 rounded-full flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl relative group overflow-hidden flex items-center justify-center"
                style={{
                  backgroundColor: input.trim() && !isThinking ? '#3B82F6' : '#94A3B8',
                  transition: 'all 0.2s ease-in-out'
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
                <Send className="w-4 h-4 text-white relative z-10" />
              </button>
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-2">
              Powered by RAG • Session: {sessionId.slice(-8)}
            </p>
          </div>
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
