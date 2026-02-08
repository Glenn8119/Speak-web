/**
 * Custom hook for browser-native speech recognition using Web Speech API.
 * Handles voice-to-text transcription with real-time interim results.
 */

import { useRef, useCallback, useState, useEffect } from 'react'

/** Browser Speech Recognition API types */
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message?: string
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  isFinal: boolean
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  start(): void
  stop(): void
  abort(): void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
  onstart: (() => void) | null
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition
    webkitSpeechRecognition: new () => SpeechRecognition
  }
}

/** Configuration for the useSpeechRecognition hook */
interface UseSpeechRecognitionConfig {
  /** Language for speech recognition (defaults to 'en-US') */
  language?: string
  /** Timeout in ms to stop recording if no speech detected (defaults to 10000) */
  timeout?: number
  /** Callback when final transcript is ready */
  onFinalResult?: (transcript: string) => void
  /** Callback for interim results (real-time updates) */
  onInterimResult?: (transcript: string) => void
  /** Callback when an error occurs */
  onError?: (error: string) => void
}

/** Return type for the useSpeechRecognition hook */
interface UseSpeechRecognitionReturn {
  /** Whether speech recognition is supported in this browser */
  isSupported: boolean
  /** Whether recording is currently active */
  isRecording: boolean
  /** Current transcript (interim or final) */
  transcript: string
  /** Start voice recording */
  startRecording: () => void
  /** Stop voice recording */
  stopRecording: () => void
  /** Clear the current transcript */
  clearTranscript: () => void
  /** Current error message (if any) */
  error: string | null
}

/** Default configuration values */
const DEFAULT_CONFIG: Required<
  Omit<
    UseSpeechRecognitionConfig,
    'onFinalResult' | 'onInterimResult' | 'onError'
  >
> = {
  language: 'en-US',
  timeout: 10000
}

/**
 * Check if Web Speech API is supported in the current browser
 */
function getSpeechRecognition(): (new () => SpeechRecognition) | null {
  if (typeof window === 'undefined') return null
  return window.SpeechRecognition || window.webkitSpeechRecognition || null
}

/**
 * Custom hook for managing speech recognition via Web Speech API.
 */
export function useSpeechRecognition(
  config: UseSpeechRecognitionConfig = {}
): UseSpeechRecognitionReturn {
  const { language, timeout } = { ...DEFAULT_CONFIG, ...config }
  const { onFinalResult, onInterimResult, onError } = config

  // State
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Refs
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Check browser support (computed once, no effect needed)
  const isSupported = getSpeechRecognition() !== null

  /**
   * Clear the timeout
   */
  const clearTimeoutRef = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  /**
   * Stop recording and clean up
   */
  const stopRecording = useCallback(() => {
    clearTimeoutRef()
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    setIsRecording(false)
  }, [clearTimeoutRef])

  /**
   * Start voice recording
   */
  const startRecording = useCallback(() => {
    const SpeechRecognitionClass = getSpeechRecognition()
    if (!SpeechRecognitionClass) {
      const errorMsg = 'Speech recognition is not supported in this browser'
      setError(errorMsg)
      onError?.(errorMsg)
      return
    }

    // If already recording, stop first
    if (isRecording) {
      stopRecording()
      return
    }

    // Clear previous state
    setError(null)
    setTranscript('')

    // Create new recognition instance
    const recognition = new SpeechRecognitionClass()
    recognition.lang = language
    recognition.continuous = true
    recognition.interimResults = true
    recognitionRef.current = recognition

    // Handle results
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      clearTimeoutRef() // Reset timeout on speech detection
      console.log(event.results)
      let interimTranscript = ''
      let finalTranscript = ''

      // Accumulate all results (both interim and final)
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscript += result[0].transcript
        } else {
          interimTranscript += result[0].transcript
        }
      }

      // Combine final and interim transcripts
      const combinedTranscript = finalTranscript + interimTranscript

      if (combinedTranscript) {
        setTranscript(combinedTranscript)

        // Call appropriate callback based on whether we have final results
        if (finalTranscript) {
          onFinalResult?.(combinedTranscript)
        } else {
          onInterimResult?.(combinedTranscript)
        }

        // Reset timeout - don't auto-stop, let user control
        timeoutRef.current = setTimeout(() => {
          stopRecording()
        }, timeout)
      }
    }

    // Handle errors
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      let errorMsg: string

      switch (event.error) {
        case 'network':
          errorMsg = 'Network error occurred. Please check your connection.'
          break
        case 'no-speech':
          errorMsg = 'No speech detected. Please try again.'
          break
        case 'aborted':
          errorMsg = 'Recording was aborted.'
          break
        case 'audio-capture':
          errorMsg = 'No microphone found. Please check your microphone.'
          break
        case 'not-allowed':
          errorMsg = 'Microphone access denied. Please allow microphone access.'
          break
        default:
          errorMsg = `Speech recognition error: ${event.error}`
      }

      setError(errorMsg)
      onError?.(errorMsg)
      stopRecording()
    }

    // Handle recognition end
    recognition.onend = () => {
      console.log('on end')
      clearTimeoutRef()
      setIsRecording(false)
    }

    // Handle recognition start
    recognition.onstart = () => {
      console.log('on start')
      setIsRecording(true)
      // Set timeout for no speech detection
      timeoutRef.current = setTimeout(() => {
        const timeoutMsg = 'No speech detected. Recording stopped.'
        setError(timeoutMsg)
        onError?.(timeoutMsg)
        stopRecording()
      }, timeout)
    }

    // Start recognition
    try {
      recognition.start()
    } catch {
      const errorMsg = 'Failed to start speech recognition'
      setError(errorMsg)
      onError?.(errorMsg)
    }
  }, [
    isRecording,
    language,
    timeout,
    onFinalResult,
    onInterimResult,
    onError,
    stopRecording,
    clearTimeoutRef
  ])

  /**
   * Clear the current transcript
   */
  const clearTranscript = useCallback(() => {
    setTranscript('')
    setError(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeoutRef()
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    }
  }, [clearTimeoutRef])

  return {
    isSupported,
    isRecording,
    transcript,
    startRecording,
    stopRecording,
    clearTranscript,
    error
  }
}

export default useSpeechRecognition
