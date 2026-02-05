import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  type ReactNode
} from 'react'
import type {
  ChatState,
  ChatActions,
  Message,
  Correction,
  LoadingState
} from '../types'

// Initial state
const initialState: ChatState = {
  messages: [],
  threadId: null,
  loading: {
    chat: false,
    correction: false,
    summary: false
  },
  error: null
}

// Action types
type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: Message }
  | {
      type: 'UPDATE_MESSAGE_CONTENT'
      payload: { messageId: string; content: string }
    }
  | {
      type: 'ATTACH_CORRECTION'
      payload: { messageId: string; correction: Correction }
    }
  | { type: 'SET_THREAD_ID'; payload: string }
  | { type: 'CLEAR_THREAD' }
  | {
      type: 'SET_LOADING'
      payload: { key: keyof LoadingState; value: boolean }
    }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'LOAD_HISTORY'; payload: Message[] }

// Reducer
function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload]
      }

    case 'UPDATE_MESSAGE_CONTENT':
      return {
        ...state,
        messages: state.messages.map((msg) =>
          msg.id === action.payload.messageId
            ? { ...msg, content: action.payload.content }
            : msg
        )
      }

    case 'ATTACH_CORRECTION':
      return {
        ...state,
        messages: state.messages.map((msg) =>
          msg.id === action.payload.messageId
            ? { ...msg, correction: action.payload.correction }
            : msg
        )
      }

    case 'SET_THREAD_ID':
      return {
        ...state,
        threadId: action.payload
      }

    case 'CLEAR_THREAD':
      return {
        ...initialState
      }

    case 'SET_LOADING':
      return {
        ...state,
        loading: {
          ...state.loading,
          [action.payload.key]: action.payload.value
        }
      }

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload
      }

    case 'LOAD_HISTORY':
      return {
        ...state,
        messages: action.payload
      }

    default:
      return state
  }
}

// Generate unique message ID
function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

// LocalStorage key for thread ID
const THREAD_ID_STORAGE_KEY = 'speak_chat_thread_id'

// Context type
type ChatContextType = ChatState & ChatActions

// Create context
const ChatContext = createContext<ChatContextType | null>(null)

// Provider props
interface ChatProviderProps {
  children: ReactNode
}

// Provider component
export function ChatProvider({ children }: ChatProviderProps) {
  const [state, dispatch] = useReducer(chatReducer, initialState)

  // Load thread ID and history from localStorage on mount
  useEffect(() => {
    const savedThreadId = localStorage.getItem(THREAD_ID_STORAGE_KEY)
    if (savedThreadId) {
      dispatch({ type: 'SET_THREAD_ID', payload: savedThreadId })

      // Fetch conversation history from backend
      fetch(`http://localhost:8000/history/${savedThreadId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.messages && data.messages.length > 0) {
            // Transform backend messages to frontend format
            const messages: Message[] = data.messages.map(
              (msg: {
                id: string
                role: string
                content: string
                timestamp: number
                correction?: Correction
              }) => ({
                id: msg.id,
                role: msg.role as 'user' | 'assistant',
                content: msg.content,
                timestamp: msg.timestamp || Date.now(),
                correction: msg.correction
              })
            )
            dispatch({ type: 'LOAD_HISTORY', payload: messages })
          }
        })
        .catch((err) => {
          console.error('Failed to load conversation history:', err)
        })
    }
  }, [])

  // Actions
  const addMessage = useCallback(
    (message: Omit<Message, 'id' | 'timestamp'>): string => {
      const id = generateMessageId()
      const fullMessage: Message = {
        ...message,
        id,
        timestamp: Date.now()
      }
      dispatch({ type: 'ADD_MESSAGE', payload: fullMessage })
      return id
    },
    []
  )

  const updateMessageContent = useCallback(
    (messageId: string, content: string) => {
      dispatch({
        type: 'UPDATE_MESSAGE_CONTENT',
        payload: { messageId, content }
      })
    },
    []
  )

  const attachCorrection = useCallback(
    (messageId: string, correction: Correction) => {
      dispatch({
        type: 'ATTACH_CORRECTION',
        payload: { messageId, correction }
      })
    },
    []
  )

  const setThreadId = useCallback((threadId: string) => {
    localStorage.setItem(THREAD_ID_STORAGE_KEY, threadId)
    dispatch({ type: 'SET_THREAD_ID', payload: threadId })
  }, [])

  const clearThread = useCallback(() => {
    localStorage.removeItem(THREAD_ID_STORAGE_KEY)
    dispatch({ type: 'CLEAR_THREAD' })
  }, [])

  const setLoading = useCallback((key: keyof LoadingState, value: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: { key, value } })
  }, [])

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error })
  }, [])

  const value: ChatContextType = {
    ...state,
    addMessage,
    updateMessageContent,
    attachCorrection,
    setThreadId,
    clearThread,
    setLoading,
    setError
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

// Custom hook to use chat context
export function useChat(): ChatContextType {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}

// Export default for convenience
export default ChatContext
