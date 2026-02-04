/**
 * Custom hook for Server-Sent Events (SSE) management.
 * Handles EventSource connection, event parsing, and automatic reconnection.
 */

import { useRef, useCallback, useState, useEffect } from 'react'
import { useChat } from '../context/ChatContext'
import type {
  Correction,
  ThreadIdEventData,
  ChatResponseEventData,
  ErrorEventData
} from '../types'

/** Configuration for the useSSE hook */
interface UseSSEConfig {
  /** Base URL for the chat API (defaults to http://localhost:8000) */
  baseUrl?: string
  /** Maximum number of reconnection attempts */
  maxReconnectAttempts?: number
  /** Base delay in ms between reconnection attempts (exponential backoff) */
  reconnectBaseDelay?: number
}

/** Return type for the useSSE hook */
interface UseSSEReturn {
  /** Send a message to the chat API via SSE */
  sendMessage: (message: string) => void
  /** Whether an SSE connection is currently active */
  isConnected: boolean
  /** Close the current SSE connection */
  disconnect: () => void
  /** Number of reconnection attempts made */
  reconnectAttempts: number
}

/** Default configuration values */
const DEFAULT_CONFIG: Required<UseSSEConfig> = {
  baseUrl: 'http://localhost:8000',
  maxReconnectAttempts: 3,
  reconnectBaseDelay: 1000
}

/**
 * Custom hook for managing SSE connections to the chat API.
 *
 * Handles:
 * - EventSource connection lifecycle
 * - Parsing SSE events (thread_id, chat_response, correction, error, complete)
 * - Automatic reconnection with exponential backoff
 * - Integration with ChatContext for state updates
 */
export function useSSE(config: UseSSEConfig = {}): UseSSEReturn {
  const {
    baseUrl,
    maxReconnectAttempts,
    reconnectBaseDelay
  } = { ...DEFAULT_CONFIG, ...config }

  const {
    threadId,
    setThreadId,
    addMessage,
    updateMessageContent,
    attachCorrection,
    setLoading,
    setError
  } = useChat()

  // Refs for managing connection state
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const currentMessageIdRef = useRef<string | null>(null)
  const lastUserMessageIdRef = useRef<string | null>(null)
  const executeRequestRef = useRef<((message: string) => void) | null>(null)
  const isCompleteHandledRef = useRef<boolean>(false)

  // State
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  /**
   * Clean up EventSource and timeout refs
   */
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    setIsConnected(false)
  }, [])

  /**
   * Handle thread_id event - store in state and localStorage
   */
  const handleThreadIdEvent = useCallback((data: ThreadIdEventData) => {
    setThreadId(data.thread_id)
  }, [setThreadId])

  /**
   * Handle chat_response event - update messages
   */
  const handleChatResponseEvent = useCallback((data: ChatResponseEventData) => {
    // If we don't have an assistant message yet, create one
    if (!currentMessageIdRef.current) {
      const messageId = addMessage({
        role: 'assistant',
        content: data.content
      })
      currentMessageIdRef.current = messageId
    } else {
      // Update existing message content (for potential future streaming support)
      updateMessageContent(currentMessageIdRef.current, data.content)
    }
    setLoading('chat', false)
  }, [addMessage, updateMessageContent, setLoading])

  /**
   * Handle correction event - attach to user message
   */
  const handleCorrectionEvent = useCallback((correction: Correction) => {
    if (lastUserMessageIdRef.current) {
      attachCorrection(lastUserMessageIdRef.current, correction)
    }
    setLoading('correction', false)
  }, [attachCorrection, setLoading])

  /**
   * Handle error event - display error and stop loading
   */
  const handleErrorEvent = useCallback((data: ErrorEventData) => {
    const errorMessage = data.message || `Error in ${data.node || 'unknown'} node`
    setError(errorMessage)

    // Stop relevant loading states based on error node
    if (data.node === 'chat') {
      setLoading('chat', false)
    } else if (data.node === 'correction') {
      setLoading('correction', false)
    } else {
      // Unknown error - stop both
      setLoading('chat', false)
      setLoading('correction', false)
    }
  }, [setError, setLoading])

  /**
   * Handle complete event - cleanup and reset state
   */
  const handleCompleteEvent = useCallback(() => {
    // Prevent duplicate handling
    if (isCompleteHandledRef.current) return
    isCompleteHandledRef.current = true

    // Ensure all loading states are cleared
    setLoading('chat', false)
    setLoading('correction', false)

    // Reset message refs for next interaction
    currentMessageIdRef.current = null

    // Reset reconnect attempts on successful completion
    setReconnectAttempts(0)

    // Close connection
    cleanup()
  }, [setLoading, cleanup])

  /**
   * Execute the SSE request (internal function for retry support)
   */
  const executeRequest = useCallback((message: string) => {
    // Reset complete handled flag for new request
    isCompleteHandledRef.current = false

    // Clean up any existing connection
    cleanup()
    setError(null)

    // Reset assistant message ref
    currentMessageIdRef.current = null

    // Set loading states
    setLoading('chat', true)
    setLoading('correction', true)

    // Build the SSE request URL with query params
    // Note: EventSource only supports GET, so we need to use fetch for POST
    // We'll use fetch with ReadableStream to handle SSE from POST request
    const url = `${baseUrl}/chat`

    const requestBody = JSON.stringify({
      message,
      thread_id: threadId || undefined
    })

    // Use fetch for POST SSE (EventSource only supports GET)
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: requestBody
    })
      .then(async response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        setIsConnected(true)
        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('No response body')
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()

          if (done) {
            handleCompleteEvent()
            break
          }

          buffer += decoder.decode(value, { stream: true })

          // Parse SSE events from buffer
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer

          let currentEventType = ''
          let currentData = ''

          for (const line of lines) {
            if (line.startsWith('event:')) {
              currentEventType = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              currentData = line.slice(5).trim()

              // Process the event
              if (currentEventType && currentData) {
                try {
                  const parsedData = JSON.parse(currentData)

                  switch (currentEventType) {
                    case 'thread_id':
                      handleThreadIdEvent(parsedData as ThreadIdEventData)
                      break
                    case 'chat_response':
                      handleChatResponseEvent(parsedData as ChatResponseEventData)
                      break
                    case 'correction':
                      handleCorrectionEvent(parsedData as Correction)
                      break
                    case 'error':
                      handleErrorEvent(parsedData as ErrorEventData)
                      break
                    case 'complete':
                      handleCompleteEvent()
                      break
                  }
                } catch (parseError) {
                  console.error('Failed to parse SSE data:', parseError)
                }

                // Reset for next event
                currentEventType = ''
                currentData = ''
              }
            } else if (line === '') {
              // Empty line indicates end of event - reset
              currentEventType = ''
              currentData = ''
            }
          }
        }
      })
      .catch(error => {
        console.error('SSE connection error:', error)
        setIsConnected(false)

        // Attempt reconnection
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = reconnectBaseDelay * Math.pow(2, reconnectAttempts)
          setError(`Connection lost. Reconnecting in ${delay / 1000}s...`)

          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1)
            // Retry the request without adding user message again
            executeRequestRef.current?.(message)
          }, delay)
        } else {
          handleErrorEvent({
            node: 'unknown',
            message: `Connection failed after ${maxReconnectAttempts} attempts. Please try again.`
          })
          setReconnectAttempts(0)
        }
      })
  }, [
    cleanup,
    setError,
    setLoading,
    baseUrl,
    threadId,
    handleThreadIdEvent,
    handleChatResponseEvent,
    handleCorrectionEvent,
    handleErrorEvent,
    handleCompleteEvent,
    reconnectAttempts,
    maxReconnectAttempts,
    reconnectBaseDelay
  ])

  useEffect(() => {
    executeRequestRef.current = executeRequest
  }, [executeRequest])

  /**
   * Send a message to the chat API via SSE
   */
  const sendMessage = useCallback((message: string) => {
    // Add user message to state and store the ID for correction attachment
    const userMessageId = addMessage({
      role: 'user',
      content: message
    })
    lastUserMessageIdRef.current = userMessageId

    // Execute the request
    executeRequest(message)
  }, [addMessage, executeRequest])

  /**
   * Disconnect the current SSE connection
   */
  const disconnect = useCallback(() => {
    cleanup()
    setLoading('chat', false)
    setLoading('correction', false)
  }, [cleanup, setLoading])

  return {
    sendMessage,
    isConnected,
    disconnect,
    reconnectAttempts
  }
}

export default useSSE
