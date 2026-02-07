import { useState } from 'react'
import { ChatProvider, useChat } from './context/ChatContext'
import { useSSE } from './hooks/useSSE'
import ChatContainer from './components/ChatContainer'
import MessageInput from './components/MessageInput'
import NewConversationButton from './components/NewConversationButton'
import SummaryModal from './components/SummaryModal'
import type { Summary } from './types'

function ChatApp() {
  const { loading, threadId, setLoading } = useChat()
  const { sendMessage, reconnectAttempts } = useSSE()
  const [summary, setSummary] = useState<Summary | null>(null)

  const handleOpenSummary = async () => {
    if (!threadId) return
    setLoading('summary', true)
    try {
      const response = await fetch('http://localhost:8000/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId })
      })
      if (!response.ok) throw new Error(`HTTP error: ${response.status}`)
      const data: Summary = await response.json()
      setSummary(data)
    } catch (error) {
      console.error('Failed to fetch summary:', error)
    } finally {
      setLoading('summary', false)
    }
  }

  const isInputDisabled = loading.chat || loading.correction

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
        <h1 className="text-lg font-semibold text-indigo-400">Speak</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={handleOpenSummary}
            disabled={!threadId || loading.summary}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {loading.summary ? 'Generating…' : 'Summary'}
          </button>
          <NewConversationButton />
        </div>
      </header>

      {/* Chat message list */}
      <ChatContainer reconnectAttempts={reconnectAttempts} />

      {/* Message input */}
      <MessageInput onSend={sendMessage} disabled={isInputDisabled} />

      {/* Summary modal (rendered when summary data is available) */}
      {summary && (
        <SummaryModal summary={summary} onClose={() => setSummary(null)} />
      )}
    </div>
  )
}

export default function App() {
  return (
    <ChatProvider>
      <ChatApp />
    </ChatProvider>
  )
}
