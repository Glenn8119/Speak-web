import type { Message } from '../types'
import CorrectionAccordion from './CorrectionAccordion'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in-up`}>
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div
          className={`px-4 py-2 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white rounded-br-sm'
              : 'bg-gray-800 text-gray-100 rounded-bl-sm'
          }`}
        >
          {message.content}
        </div>

        {isUser && message.correction && (message.correction.issues.length > 0 || message.correction.explanation?.includes('unavailable')) && (
          <CorrectionAccordion correction={message.correction} />
        )}

        {isUser && message.correction && message.correction.issues.length === 0 && !message.correction.explanation?.includes('unavailable') && (
          <div className="flex items-center gap-1 text-xs text-emerald-400 mt-0.5">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            <span>Perfect!</span>
          </div>
        )}
      </div>
    </div>
  )
}
