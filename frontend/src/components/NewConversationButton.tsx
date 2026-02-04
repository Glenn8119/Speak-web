import { useChat } from '../context/ChatContext'

export default function NewConversationButton() {
  const { messages, clearThread } = useChat()

  const handleClick = () => {
    if (messages.length === 0) return
    if (window.confirm('Start a new conversation? The current one will be cleared.')) {
      clearThread()
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={messages.length === 0}
      className="text-xs text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
    >
      + New Conversation
    </button>
  )
}
