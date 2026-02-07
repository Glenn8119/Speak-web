import { useState } from 'react'
import { useChat } from '../context/ChatContext'
import ConfirmModal from './ConfirmModal'

export default function NewConversationButton() {
  const { messages, clearThread } = useChat()
  const [showConfirm, setShowConfirm] = useState(false)

  const handleClick = () => {
    if (messages.length === 0) return
    setShowConfirm(true)
  }

  const handleConfirm = () => {
    clearThread()
    setShowConfirm(false)
  }

  const handleCancel = () => {
    setShowConfirm(false)
  }

  return (
    <>
      <button
        onClick={handleClick}
        disabled={messages.length === 0}
        className="text-xs text-gray-300 hover:text-gray-100 transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
      >
        + New Conversation
      </button>

      {showConfirm && (
        <ConfirmModal
          title="New Conversation"
          message="Start a new conversation? The current one will be cleared."
          confirmText="Start New"
          cancelText="Cancel"
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </>
  )
}
