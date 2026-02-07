import { useRef, useEffect } from 'react'
import { useChat } from '../context/ChatContext'
import ChatMessage from './ChatMessage'
import LoadingIndicator from './LoadingIndicator'
import ErrorBanner from './ErrorBanner'

interface ChatContainerProps {
  /** Number of reconnection attempts for error display */
  reconnectAttempts?: number
}

export default function ChatContainer({
  reconnectAttempts = 0
}: ChatContainerProps) {
  const { messages, loading, error } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading.chat, error])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {/* Error banner */}
      <ErrorBanner reconnectAttempts={reconnectAttempts} />

      {messages.length === 0 && !error && (
        <p className="text-center text-gray-500 text-sm mt-16">
          Start a conversation to practice your English!
        </p>
      )}

      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}

      {loading.chat && <LoadingIndicator type="chat" />}

      <div ref={bottomRef} />
    </div>
  )
}
