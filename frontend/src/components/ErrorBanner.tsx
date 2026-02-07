import { useChat } from '../context/ChatContext'

interface ErrorBannerProps {
  /** Number of reconnection attempts (optional) */
  reconnectAttempts?: number
  /** Called when user clicks dismiss button */
  onDismiss?: () => void
}

export default function ErrorBanner({
  reconnectAttempts = 0,
  onDismiss
}: ErrorBannerProps) {
  const { error, setError } = useChat()

  if (!error) return null

  const handleDismiss = () => {
    setError(null)
    onDismiss?.()
  }

  // Check if this is a reconnection message
  const isReconnecting = error.includes('Reconnecting')

  return (
    <div
      className={`flex items-center justify-between px-4 py-3 rounded-lg mb-4 ${
        isReconnecting
          ? 'bg-yellow-900/30 border border-yellow-700/50 text-yellow-200'
          : 'bg-red-900/30 border border-red-700/50 text-red-200'
      }`}
      role="alert"
    >
      <div className="flex items-center gap-3">
        {isReconnecting ? (
          <svg
            className="w-5 h-5 animate-spin text-yellow-400"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : (
          <svg
            className="w-5 h-5 text-red-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        )}
        <div>
          <p className="text-sm font-medium">{error}</p>
          {reconnectAttempts > 0 && (
            <p className="text-xs opacity-75 mt-0.5">
              Attempt {reconnectAttempts} of 3
            </p>
          )}
        </div>
      </div>

      {!isReconnecting && (
        <button
          onClick={handleDismiss}
          className="p-1 rounded hover:bg-red-800/50 transition-colors"
          aria-label="Dismiss error"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  )
}
