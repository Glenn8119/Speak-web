/**
 * Custom hook for audio recording using MediaRecorder API.
 * Supports click-to-toggle recording mode with automatic format detection.
 */

import { useState, useRef, useCallback } from 'react'

/**
 * Audio format detection preferences for cross-browser compatibility
 *
 * The formats are ordered by preference, balancing quality, file size, and browser support:
 * 1. audio/webm;codecs=opus - Chrome/Firefox preferred format
 *    - Opus codec: excellent voice quality at low bitrates (~20-40 Kbps)
 *    - Best compression, smallest upload size
 * 2. audio/webm - Chrome/Firefox fallback (uses default codec, typically Opus or Vorbis)
 * 3. audio/mp4 - Safari/iOS support (AAC codec)
 * 4. audio/wav - Universal fallback (uncompressed PCM)
 *    - Largest file size but guaranteed browser support
 *
 * Backend (Whisper API) accepts all these formats, so we prioritize
 * client-side efficiency (smaller uploads = faster transcription start).
 */
const MIME_TYPE_PREFERENCES = [
  'audio/webm;codecs=opus', // Chrome/Firefox - best compression
  'audio/webm', // Chrome/Firefox fallback
  'audio/mp4', // Safari
  'audio/wav' // Final fallback
] as const

/** Return type for the useAudioRecorder hook */
interface UseAudioRecorderReturn {
  /** Whether recording is currently in progress */
  isRecording: boolean
  /** The recorded audio blob (available after stopRecording) */
  audioBlob: Blob | null
  /** Error message if something went wrong */
  error: string | null
  /** Start recording audio */
  startRecording: () => Promise<void>
  /** Stop recording and return the audio blob */
  stopRecording: () => Promise<Blob | null>
  /** Clear the current audio blob and error */
  clear: () => void
}

/**
 * Detect and return the best supported audio format for this browser
 *
 * Uses MediaRecorder.isTypeSupported() to test each format in order of preference.
 * The detection happens at runtime because browser support varies:
 * - Chrome/Firefox: typically support WebM with Opus
 * - Safari/iOS: typically support MP4 with AAC
 * - Older browsers: may only support WAV
 *
 * @returns The first supported MIME type, or empty string to let the browser
 *          choose its default format (MediaRecorder constructor accepts empty string)
 */
function getSupportedMimeType(): string {
  for (const mimeType of MIME_TYPE_PREFERENCES) {
    if (MediaRecorder.isTypeSupported(mimeType)) {
      return mimeType
    }
  }
  // Fallback to empty string - let browser choose default format
  // This should rarely happen as modern browsers support at least one format
  return ''
}

/**
 * Custom hook for recording audio with toggle mode interaction
 */
export function useAudioRecorder(): UseAudioRecorderReturn {
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [error, setError] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  /**
   * Start recording audio from the user's microphone
   */
  const startRecording = useCallback(async () => {
    try {
      setError(null)
      setAudioBlob(null)
      audioChunksRef.current = []

      // Request microphone permission and get media stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1, // Mono audio
          sampleRate: 16000 // 16kHz for speech
        }
      })
      streamRef.current = stream

      // Get best supported MIME type
      const mimeType = getSupportedMimeType()

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType || undefined
      })
      mediaRecorderRef.current = mediaRecorder

      // Collect audio chunks
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      // Handle recording stop
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, {
          type: mimeType || 'audio/webm'
        })
        setAudioBlob(blob)
      }

      // Start recording
      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      const errorMessage =
        err instanceof Error && err.name === 'NotAllowedError'
          ? 'Microphone permission denied. Please allow microphone access to use voice input.'
          : err instanceof Error && err.name === 'NotFoundError'
            ? 'No microphone found. Please connect a microphone to use voice input.'
            : 'Failed to start recording. Please try again.'

      setError(errorMessage)
      setIsRecording(false)

      // Cleanup stream if it was created
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
    }
  }, [])

  /**
   * Stop recording and return the audio blob
   */
  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        resolve(null)
        return
      }

      // Wait for the stop event to fire and blob to be created
      const originalOnStop = mediaRecorder.onstop
      mediaRecorder.onstop = (event) => {
        // Call original handler
        if (originalOnStop) {
          originalOnStop.call(mediaRecorder, event)
        }

        // Cleanup stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop())
          streamRef.current = null
        }

        setIsRecording(false)

        // Resolve with the blob (will be set by ondataavailable handler)
        setTimeout(() => {
          const blob = new Blob(audioChunksRef.current, {
            type: mediaRecorder.mimeType || 'audio/webm'
          })
          resolve(blob)
        }, 0)
      }

      mediaRecorder.stop()
    })
  }, [])

  /**
   * Clear the current audio blob and error
   */
  const clear = useCallback(() => {
    setAudioBlob(null)
    setError(null)
    audioChunksRef.current = []
  }, [])

  return {
    isRecording,
    audioBlob,
    error,
    startRecording,
    stopRecording,
    clear
  }
}

export default useAudioRecorder
