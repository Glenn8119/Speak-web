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
  ErrorEventData,
  AudioChunkEventData
} from '../types'

/** Configuration for the useSSE hook */
interface UseSSEConfig {
  /** Base URL for the chat API (defaults to http://localhost:8000) */
  baseUrl?: string
  /** Maximum number of reconnection attempts */
  maxReconnectAttempts?: number
  /** Base delay in ms between reconnection attempts (exponential backoff) */
  reconnectBaseDelay?: number
  /** Callback when audio chunk is received (for TTS playback) */
  onAudioChunk?: (data: AudioChunkEventData) => void
}

/** Return type for the useSSE hook */
interface UseSSEReturn {
  /** Send audio to the chat API via SSE */
  sendAudio: (audioBlob: Blob) => void
  /** Whether an SSE connection is currently active */
  isConnected: boolean
  /** Close the current SSE connection */
  disconnect: () => void
  /** Number of reconnection attempts made */
  reconnectAttempts: number
}

/** Default configuration values */
const DEFAULT_CONFIG = {
  baseUrl: 'http://localhost:8000',
  maxReconnectAttempts: 3,
  reconnectBaseDelay: 1000
} as const

/**
 * Custom hook for managing SSE connections to the chat API.
 */
export function useSSE(config: UseSSEConfig = {}): UseSSEReturn {
  const { baseUrl, onAudioChunk } = {
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
   * Get file extension from MIME type for Whisper API
   */
  const getFileExtension = (mimeType: string): string => {
    if (mimeType.includes('webm')) return 'webm'
    if (mimeType.includes('mp4')) return 'mp4'
    if (mimeType.includes('wav')) return 'wav'
    if (mimeType.includes('m4a')) return 'm4a'
    if (mimeType.includes('ogg')) return 'ogg'
    // Default fallback
    return 'webm'
  }

  /**
   * Execute an audio request (upload audio and stream SSE response)
   */
  const executeAudioRequest = useCallback(
    (audioBlob: Blob) => {
      isCompleteHandledRef.current = false
      cleanup()
      setError(null)
      currentMessageIdRef.current = null

      setLoading('chat', true)
      setLoading('correction', true)

      const url = `${baseUrl}/chat`
      const formData = new FormData()
      // Include file extension based on actual MIME type for Whisper API
      const extension = getFileExtension(audioBlob.type)
      formData.append('audio', audioBlob, `audio.${extension}`)
      if (threadIdRef.current) {
        formData.append('thread_id', threadIdRef.current)
      }

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

      const onTranscription = (data: { text: string; timestamp?: number }) => {
        // Replace placeholder message with transcribed text
        if (lastUserMessageIdRef.current) {
          updateMessageContent(lastUserMessageIdRef.current, data.text)
        }
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
          Accept: 'text/event-stream'
        },
        body: formData
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
                      case 'transcription':
                        onTranscription(
                          parsedData as { text: string; timestamp?: number }
                        )
                        break
                      case 'chat_response':
                        onChatResponse(parsedData as ChatResponseEventData)
                        break
                      case 'correction':
                        onCorrection(parsedData as Correction)
                        break
                      case 'audio_chunk':
                        // Handle audio chunk event - play audio without blocking text
                        if (onAudioChunk) {
                          onAudioChunk(parsedData as AudioChunkEventData)
                        }
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
          onError({
            node: 'unknown',
            message: 'Failed to upload audio. Please try again.'
          })
          reconnectAttemptsRef.current = 0
          setReconnectAttempts(0)
        })
    },
    [
      baseUrl,
      cleanup,
      setError,
      setLoading,
      setThreadId,
      addMessage,
      updateMessageContent,
      attachCorrection,
      onAudioChunk
    ]
  )

  /**
   * Send audio to the chat API via SSE
   */
  const sendAudio = useCallback(
    (audioBlob: Blob) => {
      // Create placeholder message with "🎤 Transcribing..."
      const userMessageId = addMessage({
        role: 'user',
        content: '🎤 Transcribing...'
      })
      lastUserMessageIdRef.current = userMessageId
      executeAudioRequest(audioBlob)
    },
    [addMessage, executeAudioRequest]
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
    sendAudio,
    isConnected,
    disconnect,
    reconnectAttempts
  }
}

export default useSSE
