import { useAudioRecorder } from '../hooks/useAudioRecorder'

interface MessageInputProps {
  onSendAudio?: (audioBlob: Blob) => void
  disabled?: boolean
}

export default function MessageInput({
  onSendAudio,
  disabled = false
}: MessageInputProps) {
  // Audio recording hook
  const {
    isRecording,
    error: audioError,
    startRecording,
    stopRecording
  } = useAudioRecorder()

  const handleMicClick = async () => {
    if (isRecording) {
      // Stop recording and send audio
      const audioBlob = await stopRecording()
      if (audioBlob && onSendAudio) {
        onSendAudio(audioBlob)
      }
    } else {
      // Start recording
      await startRecording()
    }
  }

  return (
    <div className='relative'>
      {/* Error message banner */}
      {audioError && (
        <div className='absolute bottom-full left-0 right-0 mb-2 px-4'>
          <div className='bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded-lg text-sm'>
            {audioError}
          </div>
        </div>
      )}

      <div className='flex items-center justify-center p-4 border-t border-gray-800'>
        {/* Microphone button */}
        <button
          onClick={handleMicClick}
          disabled={disabled}
          className={`relative w-20 h-20 rounded-full transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center ${
            isRecording
              ? 'bg-red-600 hover:bg-red-500 shadow-lg shadow-red-500/50 animate-pulse'
              : 'bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50'
          }`}
          title={isRecording ? '停止並送出' : '開始錄音'}
        >
          {/* Microphone Icon */}
          {isRecording ? (
            // Stop/Square icon when recording
            <svg
              className="w-10 h-10 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          ) : (
            // Microphone icon when not recording
            <svg
              className="w-10 h-10 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          )}

          {/* Recording indicator ring */}
          {isRecording && (
            <span className="absolute inset-0 rounded-full border-4 border-red-400 animate-ping opacity-75" />
          )}
        </button>
      </div>
    </div>
  )
}
