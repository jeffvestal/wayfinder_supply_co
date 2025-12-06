import { useState, useRef, useEffect } from 'react'
import { ChatMessage, UserId, ThoughtTraceEvent } from '../types'
import { api } from '../lib/api'
import { ThoughtTrace } from './ThoughtTrace'
import { Send, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface ChatInterfaceProps {
  userId: UserId
}

export function ChatInterface({ userId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [thoughtTrace, setThoughtTrace] = useState<ThoughtTraceEvent[]>([])
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
    setThoughtTrace([])

    try {
      let currentAssistantMessage: ChatMessage | null = null
      let messageContent = ''

      await api.streamChat(input.trim(), userId, (event) => {
        const data = JSON.parse(event.data)

        // Handle different event types
        if (event.event === 'reasoning') {
          setThoughtTrace((prev) => [
            ...prev,
            {
              event: 'reasoning',
              data: data.reasoning || data,
              timestamp: new Date(),
            },
          ])
        } else if (event.event === 'tool_call') {
          setThoughtTrace((prev) => [
            ...prev,
            {
              event: 'tool_call',
              data: {
                tool_id: data.tool_id,
                params: data.params,
                tool_call_id: data.tool_call_id,
              },
              timestamp: new Date(),
            },
          ])
        } else if (event.event === 'tool_result') {
          setThoughtTrace((prev) => [
            ...prev,
            {
              event: 'tool_result',
              data: {
                tool_call_id: data.tool_call_id,
                results: data.results,
              },
              timestamp: new Date(),
            },
          ])
        } else if (event.event === 'message_chunk') {
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
    <div className="flex gap-4 h-[calc(100vh-12rem)]">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-gray-800 rounded-lg border border-gray-700">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-center">
              <div>
                <h3 className="text-xl font-semibold mb-2">Start a Conversation</h3>
                <p className="text-gray-400">
                  Ask about your upcoming trip and get personalized gear recommendations!
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Try: "I'm going camping in the Rockies this weekend"
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
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-gray-700 text-gray-100'
                  }`}
                >
                  {message.role === 'assistant' ? (
                    <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <p>{message.content}</p>
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
              <div className="bg-gray-700 rounded-lg px-4 py-2 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="border-t border-gray-700 p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your trip..."
              className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </div>
        </form>
      </div>

      {/* Thought Trace Panel */}
      <div className="w-80">
        <ThoughtTrace events={thoughtTrace} />
      </div>
    </div>
  )
}


