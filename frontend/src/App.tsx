import { useState } from 'react'
import { ChatProvider, useChat } from './context/ChatContext'
import { useSSE } from './hooks/useSSE'
import { useAudioPlayback } from './hooks/useAudioPlayback'
import ChatContainer from './components/ChatContainer'
import MessageInput from './components/MessageInput'
import NewConversationButton from './components/NewConversationButton'
import SummaryModal from './components/SummaryModal'
import type { Summary } from './types'

function ChatApp() {
  const { loading, threadId, setLoading, clearThread } = useChat()
  const { playAudio } = useAudioPlayback()
  const { sendMessage, reconnectAttempts } = useSSE({
    onAudioChunk: (data) => {
      playAudio(data.audio)
    }
  })
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
    <div className='flex flex-col h-screen bg-gray-950 text-gray-100'>
      {/* Header */}
      <header className='flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0'>
        <h1 className='text-lg font-semibold text-indigo-300'>Speak</h1>
        <div className='flex items-center gap-4'>
          <button
            onClick={handleOpenSummary}
            disabled={!threadId || loading.summary}
            className='text-xs text-gray-300 hover:text-gray-100 transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed'
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
        <SummaryModal
          summary={summary}
          onNewConversation={() => {
            clearThread()
            setTimeout(() => {
              setSummary(null)
            }, 100)
          }}
        />
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
