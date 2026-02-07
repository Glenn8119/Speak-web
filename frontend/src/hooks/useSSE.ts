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
 */
export function useSSE(config: UseSSEConfig = {}): UseSSEReturn {
  const { baseUrl, maxReconnectAttempts, reconnectBaseDelay } = {
    ...DEFAULT_CONFIG,
    ...config
  }

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
  const isCompleteHandledRef = useRef<boolean>(false)
  const reconnectAttemptsRef = useRef(0)
  const executeRequestRef = useRef<((message: string) => void) | null>(null)
  const threadIdRef = useRef(threadId)

  // State
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  // Keep threadId ref in sync
  useEffect(() => {
    threadIdRef.current = threadId
  }, [threadId])

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
   * Execute the SSE request
   */
  const executeRequest = useCallback(
    (message: string) => {
      isCompleteHandledRef.current = false
      cleanup()
      setError(null)
      currentMessageIdRef.current = null

      setLoading('chat', true)
      setLoading('correction', true)

      const url = `${baseUrl}/chat`
      const requestBody = JSON.stringify({
        message,
        thread_id: threadIdRef.current || undefined
      })

      // Inline handlers to avoid dependency issues
      const onComplete = () => {
        if (isCompleteHandledRef.current) return
        isCompleteHandledRef.current = true

        setLoading('chat', false)
        setLoading('correction', false)
        currentMessageIdRef.current = null
        reconnectAttemptsRef.current = 0
        setReconnectAttempts(0)
        cleanup()
      }

      const onThreadId = (data: ThreadIdEventData) => {
        setThreadId(data.thread_id)
      }

      const onChatResponse = (data: ChatResponseEventData) => {
        if (!currentMessageIdRef.current) {
          currentMessageIdRef.current = addMessage({
            role: 'assistant',
            content: data.content
          })
        } else {
          // Reserved for future streaming support (stream by token)
          updateMessageContent(currentMessageIdRef.current, data.content)
        }
        setLoading('chat', false)
      }

      const onCorrection = (correction: Correction) => {
        if (lastUserMessageIdRef.current) {
          attachCorrection(lastUserMessageIdRef.current, correction)
        }
        setLoading('correction', false)
      }

      const onError = (data: ErrorEventData) => {
        const errorMessage =
          data.message || `Error in ${data.node || 'unknown'} node`

        if (data.node === 'chat') {
          // Chat failed - show error, stop chat loading
          setError(errorMessage)
          setLoading('chat', false)
        } else if (data.node === 'correction') {
          // Correction failed - attach a fallback correction instead of showing error
          // This allows the conversation to continue smoothly
          if (lastUserMessageIdRef.current) {
            attachCorrection(lastUserMessageIdRef.current, {
              original: '',
              corrected: '',
              issues: [],
              explanation: 'Grammar check unavailable for this message.'
            })
          }
          setLoading('correction', false)
          // Don't set global error for correction failures - it's non-critical
        } else {
          // Unknown/general error - show error and stop all loading
          setError(errorMessage)
          setLoading('chat', false)
          setLoading('correction', false)
        }
      }

      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream'
        },
        body: requestBody
      })
        .then(async (response) => {
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
          let currentEventType = ''
          let currentData = ''

          while (true) {
            const { done, value } = await reader.read()

            if (done) {
              onComplete()
              break
            }

            buffer += decoder.decode(value, { stream: true })

            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (line.startsWith('event:')) {
                currentEventType = line.slice(6).trim()
              } else if (line.startsWith('data:')) {
                currentData = line.slice(5).trim()

                if (currentEventType && currentData) {
                  try {
                    const parsedData = JSON.parse(currentData)

                    switch (currentEventType) {
                      case 'thread_id':
                        onThreadId(parsedData as ThreadIdEventData)
                        break
                      case 'chat_response':
                        onChatResponse(parsedData as ChatResponseEventData)
                        break
                      case 'correction':
                        onCorrection(parsedData as Correction)
                        break
                      case 'error':
                        onError(parsedData as ErrorEventData)
                        break
                      case 'complete':
                        onComplete()
                        break
                    }
                  } catch (parseError) {
                    console.error('Failed to parse SSE data:', parseError)
                  }

                  currentEventType = ''
                  currentData = ''
                }
              } else if (line === '') {
                currentEventType = ''
                currentData = ''
              }
            }
          }
        })
        .catch((error) => {
          console.error('SSE connection error:', error)
          setIsConnected(false)

          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            const delay =
              reconnectBaseDelay * Math.pow(2, reconnectAttemptsRef.current)
            setError(`Connection lost. Reconnecting in ${delay / 1000}s...`)

            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectAttemptsRef.current += 1
              setReconnectAttempts(reconnectAttemptsRef.current)
              executeRequestRef.current?.(message)
            }, delay)
          } else {
            onError({
              node: 'unknown',
              message: `Connection failed after ${maxReconnectAttempts} attempts. Please try sending your message again.`
            })
            reconnectAttemptsRef.current = 0
            setReconnectAttempts(0)
          }
        })
    },
    [
      baseUrl,
      maxReconnectAttempts,
      reconnectBaseDelay,
      cleanup,
      setError,
      setLoading,
      setThreadId,
      addMessage,
      updateMessageContent,
      attachCorrection
    ]
  )

  // Keep ref in sync for recursive calls
  useEffect(() => {
    executeRequestRef.current = executeRequest
  }, [executeRequest])

  /**
   * Send a message to the chat API via SSE
   */
  const sendMessage = useCallback(
    (message: string) => {
      const userMessageId = addMessage({
        role: 'user',
        content: message
      })
      lastUserMessageIdRef.current = userMessageId
      executeRequest(message)
    },
    [addMessage, executeRequest]
  )

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
