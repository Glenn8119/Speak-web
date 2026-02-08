/**
 * Custom hook for audio playback using Web Audio API.
 * Handles base64-encoded Opus audio decoding and playback.
 */

import { useRef, useCallback, useState, useEffect } from 'react'

/** Configuration for the useAudioPlayback hook */
interface UseAudioPlaybackConfig {
  /** Callback when playback starts */
  onPlaybackStart?: () => void
  /** Callback when playback ends */
  onPlaybackEnd?: () => void
  /** Callback when an error occurs */
  onError?: (error: string) => void
}

/** Return type for the useAudioPlayback hook */
interface UseAudioPlaybackReturn {
  /** Play audio from base64-encoded data */
  playAudio: (base64Audio: string) => Promise<void>
  /** Stop any currently playing audio */
  stopAudio: () => void
  /** Whether audio is currently playing */
  isPlaying: boolean
  /** Current error message (if any) */
  error: string | null
  /** Resume AudioContext after user interaction (call if suspended) */
  resumeContext: () => Promise<void>
  /** Whether AudioContext is suspended */
  isSuspended: boolean
}

/**
 * Convert base64 string to ArrayBuffer
 */
function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binaryString = atob(base64)
  const bytes = new Uint8Array(binaryString.length)
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }
  return bytes.buffer
}

/**
 * Custom hook for managing audio playback via Web Audio API.
 */
export function useAudioPlayback(config: UseAudioPlaybackConfig = {}): UseAudioPlaybackReturn {
  const { onPlaybackStart, onPlaybackEnd, onError } = config

  // State
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSuspended, setIsSuspended] = useState(false)

  // Refs
  const audioContextRef = useRef<AudioContext | null>(null)
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null)

  /**
   * Initialize AudioContext lazily on first use
   */
  const getAudioContext = useCallback((): AudioContext | null => {
    if (audioContextRef.current) {
      return audioContextRef.current
    }

    try {
      const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      if (!AudioContextClass) {
        throw new Error('Web Audio API not supported')
      }
      audioContextRef.current = new AudioContextClass()
      setIsSuspended(audioContextRef.current.state === 'suspended')
      return audioContextRef.current
    } catch {
      const errorMsg = 'Failed to initialize audio context'
      setError(errorMsg)
      onError?.(errorMsg)
      return null
    }
  }, [onError])

  /**
   * Resume AudioContext after user interaction
   */
  const resumeContext = useCallback(async (): Promise<void> => {
    const context = getAudioContext()
    if (context && context.state === 'suspended') {
      try {
        await context.resume()
        setIsSuspended(false)
      } catch (err) {
        console.error('Failed to resume AudioContext:', err)
      }
    }
  }, [getAudioContext])

  /**
   * Stop any currently playing audio
   */
  const stopAudio = useCallback(() => {
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop()
        sourceNodeRef.current.disconnect()
      } catch {
        // Ignore errors if already stopped
      }
      sourceNodeRef.current = null
    }
    setIsPlaying(false)
  }, [])

  /**
   * Play audio from base64-encoded data
   */
  const playAudio = useCallback(async (base64Audio: string): Promise<void> => {
    // Stop any currently playing audio
    stopAudio()
    setError(null)

    const context = getAudioContext()
    if (!context) {
      return
    }

    // Resume context if suspended (browser autoplay policy)
    if (context.state === 'suspended') {
      try {
        await context.resume()
        setIsSuspended(false)
      } catch (resumeError) {
        console.error('Failed to resume AudioContext:', resumeError)
        setIsSuspended(true)
        // Don't block, continue attempting playback
      }
    }

    try {
      // Convert base64 to ArrayBuffer
      const arrayBuffer = base64ToArrayBuffer(base64Audio)

      // Decode audio data
      const audioBuffer = await context.decodeAudioData(arrayBuffer)

      // Create and configure source node
      const sourceNode = context.createBufferSource()
      sourceNode.buffer = audioBuffer
      sourceNode.connect(context.destination)
      sourceNodeRef.current = sourceNode

      // Handle playback end
      sourceNode.onended = () => {
        setIsPlaying(false)
        sourceNodeRef.current = null
        onPlaybackEnd?.()
      }

      // Start playback
      sourceNode.start()
      setIsPlaying(true)
      onPlaybackStart?.()
    } catch (err) {
      // Log error but don't block text display
      const errorMsg = err instanceof Error ? err.message : 'Failed to decode audio'
      console.error('Audio playback error:', errorMsg)
      setError(errorMsg)
      onError?.(errorMsg)
      setIsPlaying(false)
    }
  }, [getAudioContext, stopAudio, onPlaybackStart, onPlaybackEnd, onError])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudio()
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {
          // Ignore close errors
        })
        audioContextRef.current = null
      }
    }
  }, [stopAudio])

  return {
    playAudio,
    stopAudio,
    isPlaying,
    error,
    resumeContext,
    isSuspended
  }
}

export default useAudioPlayback
