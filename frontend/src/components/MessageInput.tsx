import {
  useState,
  useRef,
  useEffect,
  type KeyboardEvent,
  type ChangeEvent
} from 'react'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'

interface MessageInputProps {
  onSend: (text: string) => void
  disabled?: boolean
}

export default function MessageInput({
  onSend,
  disabled = false
}: MessageInputProps) {
  const [text, setText] = useState('')
  const [speechError, setSpeechError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Speech recognition hook
  const {
    isSupported,
    isRecording,
    startRecording,
    stopRecording,
    clearTranscript,
    error: recognitionError
  } = useSpeechRecognition({
    onFinalResult: (finalTranscript) => {
      // Update text field but don't auto-submit
      // Let user review and manually click Send
      setText(finalTranscript)
    },
    onInterimResult: (interimTranscript) => {
      // Update text field with interim results
      setText(interimTranscript)
    },
    onError: (error) => {
      setSpeechError(error)
      // Clear error after 5 seconds
      setTimeout(() => setSpeechError(null), 5000)
    }
  })

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [text])

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
    clearTranscript()
  }

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    // When user types, clear any interim transcript from voice input
    if (isRecording) {
      stopRecording()
      clearTranscript()
    }
    setText(e.target.value)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      // Clear text field when starting voice input
      setText('')
      clearTranscript()
      setSpeechError(null)
      startRecording()
    }
  }

  return (
    <div className='relative'>
      {/* Error message banner */}
      {(speechError || recognitionError) && (
        <div className='absolute bottom-full left-0 right-0 mb-2 px-4'>
          <div className='bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded-lg text-sm'>
            {speechError || recognitionError}
          </div>
        </div>
      )}

      {/* Unsupported browser message */}
      {!isSupported && (
        <div className='absolute bottom-full left-0 right-0 mb-2 px-4'>
          <div className='bg-yellow-900/50 border border-yellow-700 text-yellow-200 px-4 py-2 rounded-lg text-sm'>
            Voice input is not supported in your browser. Please use text input
            or try Chrome/Edge.
          </div>
        </div>
      )}

      <div className='flex items-end gap-2 p-4 border-t border-gray-800'>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled || isRecording}
          placeholder={
            isRecording ? 'Listening...' : 'Type a message... (Enter to send)'
          }
          rows={1}
          className='flex-1 resize-none bg-gray-800 text-gray-100 placeholder-gray-500 rounded-xl px-4 py-2.5 text-sm border border-gray-700 focus:border-indigo-500 focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden'
        />

        {/* Microphone button */}
        <button
          onClick={handleMicClick}
          disabled={disabled || !isSupported}
          className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0 ${
            isRecording
              ? 'bg-red-600 hover:bg-red-500 text-white animate-pulse'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-100'
          }`}
          title={
            !isSupported
              ? 'Voice input not supported'
              : isRecording
                ? 'Stop recording'
                : 'Start voice input'
          }
        >
          {isRecording ? (
            <svg className='w-5 h-5' fill='currentColor' viewBox='0 0 20 20'>
              <rect x='6' y='4' width='8' height='12' rx='1' />
            </svg>
          ) : (
            <svg className='w-5 h-5' fill='currentColor' viewBox='0 0 20 20'>
              <path d='M10 12a2 2 0 100-4 2 2 0 000 4z' />
              <path
                fillRule='evenodd'
                d='M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z'
                clipRule='evenodd'
              />
              <circle cx='10' cy='10' r='3' />
            </svg>
          )}
        </button>

        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className='bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0'
        >
          Send
        </button>
      </div>
    </div>
  )
}
