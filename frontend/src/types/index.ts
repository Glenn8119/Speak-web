/**
 * Types and interfaces for the Speak Chat App
 */

/**
 * Represents a grammar correction for a user message
 */
export interface Correction {
  /** The original text that was analyzed */
  original: string
  /** The corrected version of the text */
  corrected: string
  /** Array of specific issues found (e.g., "Past tense: go → went") */
  issues: string[]
  /** Friendly explanation of the corrections */
  explanation: string
}

/**
 * Role of the message sender
 */
export type MessageRole = 'user' | 'assistant'

/**
 * Represents a single message in the conversation
 */
export interface Message {
  /** Unique identifier for the message */
  id: string
  /** Who sent the message */
  role: MessageRole
  /** The message content */
  content: string
  /** Timestamp when the message was created */
  timestamp: number
  /** Grammar correction attached to user messages (optional) */
  correction?: Correction
}

/**
 * Loading states for different async operations
 */
export interface LoadingState {
  /** Whether a chat response is being generated */
  chat: boolean
  /** Whether grammar correction is being processed */
  correction: boolean
  /** Whether summary is being generated */
  summary: boolean
}

/**
 * SSE event types received from the backend
 */
export type SSEEventType =
  | 'thread_id'
  | 'chat_response'
  | 'correction'
  | 'error'
  | 'done'

/**
 * Base SSE event structure
 */
export interface SSEEvent<T = unknown> {
  type: SSEEventType
  data: T
}

/**
 * Thread ID event data
 */
export interface ThreadIdEventData {
  thread_id: string
}

/**
 * Chat response event data
 */
export interface ChatResponseEventData {
  content: string
}

/**
 * Correction event data
 */
export interface CorrectionEventData {
  correction: Correction
  message_id?: string
}

/**
 * Error event data
 */
export interface ErrorEventData {
  node: 'chat' | 'correction' | 'unknown'
  message: string
}

/**
 * Audio chunk event data (TTS audio)
 */
export interface AudioChunkEventData {
  /** Base64-encoded audio data */
  audio: string
  /** Audio format (e.g., 'opus') */
  format: string
}

/**
 * Common pattern identified in corrections
 */
export interface PatternInfo {
  /** Name of the error pattern */
  pattern: string
  /** Number of times this pattern occurred */
  frequency: number
  /** Suggested practice exercise */
  suggestion: string
}

/**
 * Summary data structure returned from /summary endpoint
 */
export interface Summary {
  /** Part 1: List of all corrections from the thread */
  corrections: Correction[]
  /** Part 2: AI-generated tips and common patterns */
  tips: string
  /** Common error patterns with frequency and suggestions */
  common_patterns: PatternInfo[]
}

/**
 * Chat context state
 */
export interface ChatState {
  /** All messages in the current conversation */
  messages: Message[]
  /** Current thread ID (null if no active conversation) */
  threadId: string | null
  /** Loading states for async operations */
  loading: LoadingState
  /** Current error message (if any) */
  error: string | null
}

/**
 * Chat context actions
 */
export interface ChatActions {
  /** Add a new message to the conversation */
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => string
  /** Attach a correction to a specific user message */
  attachCorrection: (messageId: string, correction: Correction) => void
  /** Set the thread ID (also syncs to localStorage) */
  setThreadId: (threadId: string) => void
  /** Clear the current thread (start new conversation) */
  clearThread: () => void
  /** Update loading state for a specific operation */
  setLoading: (key: keyof LoadingState, value: boolean) => void
  /** Set an error message */
  setError: (error: string | null) => void
  /** Update the content of an existing message (for streaming) */
  updateMessageContent: (messageId: string, content: string) => void
}
