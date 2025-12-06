import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChatMessage, UserId } from '../types'
import { api } from '../lib/api'
import { Send, Loader2, X, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface ChatModalProps {
  isOpen: boolean
  onClose: () => void
  userId: UserId
  onOpenTripPlanner: () => void
}

export function ChatModal({ isOpen, onClose, userId, onOpenTripPlanner }: ChatModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      let currentAssistantMessage: ChatMessage | null = null
      let messageContent = ''

      await api.streamChat(input.trim(), userId, (event) => {
        const data = JSON.parse(event.data)

        if (event.event === 'message_chunk') {
          messageContent += data.text_chunk || ''
          if (!currentAssistantMessage) {
            currentAssistantMessage = {
              id: data.message_id || Date.now().toString(),
              role: 'assistant',
              content: messageContent,
              timestamp: new Date(),
            }
            setMessages((prev) => [...prev, currentAssistantMessage!])
          } else {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === currentAssistantMessage!.id
                  ? { ...msg, content: messageContent }
                  : msg
              )
            )
          }
        } else if (event.event === 'message_complete') {
          messageContent = data.message_content || messageContent
          if (currentAssistantMessage) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === currentAssistantMessage!.id
                  ? { ...msg, content: messageContent }
                  : msg
              )
            )
          }
        }
      })
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 h-[85vh] max-h-[700px] bg-slate-900 rounded-t-3xl shadow-2xl z-50 flex flex-col border-t border-white/10"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-white/10">
              <div>
                <h2 className="text-2xl font-display font-bold text-white">Quick Chat</h2>
                <p className="text-sm text-gray-400">Ask quick questions about gear</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={onOpenTripPlanner}
                  className="flex items-center gap-2 px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-lg transition-all text-sm font-medium border border-primary/30"
                >
                  <ExternalLink className="w-4 h-4" />
                  Open Trip Planner
                </button>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-center">
                  <div>
                    <h3 className="text-xl font-semibold mb-2 text-white">Start a Conversation</h3>
                    <p className="text-gray-400">
                      Ask quick questions about gear or your trip
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      For detailed trip planning, use the Trip Planner
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                        message.role === 'user'
                          ? 'bg-primary text-white'
                          : 'bg-slate-800 text-gray-100'
                      }`}
                    >
                      {message.role === 'assistant' ? (
                        <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="text-sm">{message.content}</p>
                      )}
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-800 rounded-2xl px-4 py-2 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-gray-300">Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="border-t border-white/10 p-4 bg-slate-900/50">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a quick question..."
                  className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Send
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

