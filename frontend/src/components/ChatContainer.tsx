import { useRef, useEffect } from 'react'
import { useChat } from '../context/ChatContext'
import ChatMessage from './ChatMessage'
import LoadingIndicator from './LoadingIndicator'

export default function ChatContainer() {
  const { messages, loading } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading.chat, loading.correction])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.length === 0 && (
        <p className="text-center text-gray-500 text-sm mt-16">
          Start a conversation to practice your English!
        </p>
      )}

      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}

      <div className="flex flex-col gap-2">
        {loading.chat && <LoadingIndicator type="chat" />}
        {loading.correction && <LoadingIndicator type="correction" />}
      </div>

      <div ref={bottomRef} />
    </div>
  )
}
