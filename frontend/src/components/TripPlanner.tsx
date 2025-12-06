import { useState, useRef, useEffect } from 'react'
import { ChatMessage, UserId, ThoughtTraceEvent } from '../types'
import { api } from '../lib/api'
import { ThoughtTrace } from './ThoughtTrace'
import { Send, Loader2, MapPin, Calendar, Mountain } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'

interface TripPlannerProps {
  userId: UserId
}

export function TripPlanner({ userId }: TripPlannerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [thoughtTrace, setThoughtTrace] = useState<ThoughtTraceEvent[]>([])
  const [tripContext, setTripContext] = useState({
    destination: '',
    dates: '',
    activity: '',
  })
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
    <div className="min-h-[calc(100vh-5rem)] bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-display font-bold text-white mb-2">
            Trip Planner
          </h1>
          <p className="text-gray-300">
            Plan your perfect adventure with AI-powered recommendations
          </p>
        </motion.div>

        {/* Trip Context Inputs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <div className="glass rounded-xl p-4">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <MapPin className="w-4 h-4 text-primary" />
              Destination
            </label>
            <input
              type="text"
              value={tripContext.destination}
              onChange={(e) => setTripContext({ ...tripContext, destination: e.target.value })}
              placeholder="e.g., Rocky Mountains"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="glass rounded-xl p-4">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <Calendar className="w-4 h-4 text-primary" />
              Dates
            </label>
            <input
              type="text"
              value={tripContext.dates}
              onChange={(e) => setTripContext({ ...tripContext, dates: e.target.value })}
              placeholder="e.g., This weekend"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="glass rounded-xl p-4">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <Mountain className="w-4 h-4 text-primary" />
              Activity
            </label>
            <input
              type="text"
              value={tripContext.activity}
              onChange={(e) => setTripContext({ ...tripContext, activity: e.target.value })}
              placeholder="e.g., Camping, Hiking"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </motion.div>

        {/* Main Chat Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Section */}
          <div className="lg:col-span-2 flex flex-col bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-[500px] max-h-[600px]">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-center">
                  <div>
                    <h3 className="text-2xl font-display font-bold text-slate-900 mb-2">
                      Start Planning Your Adventure
                    </h3>
                    <p className="text-slate-600 mb-4">
                      Tell me about your trip and I'll recommend the perfect gear
                    </p>
                    <div className="text-sm text-slate-500 space-y-1">
                      <p>Try: "I'm going camping in the Rockies this weekend"</p>
                      <p>Or: "Planning a 3-day backpacking trip in Yosemite"</p>
                    </div>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                        message.role === 'user'
                          ? 'bg-primary text-white'
                          : 'bg-slate-100 text-slate-900'
                      }`}
                    >
                      {message.role === 'assistant' ? (
                        <ReactMarkdown className="prose prose-sm max-w-none">
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="text-sm">{message.content}</p>
                      )}
                      <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/70' : 'text-slate-500'}`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </motion.div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-100 rounded-2xl px-5 py-3 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-slate-600">Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="border-t border-slate-200 p-4 bg-white">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about your trip..."
                  className="flex-1 bg-white border border-slate-300 rounded-xl px-4 py-3 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg shadow-primary/20 hover:shadow-primary/40"
                >
                  <Send className="w-4 h-4" />
                  Send
                </button>
              </div>
            </form>
          </div>

          {/* Thought Trace Panel */}
          <div className="lg:col-span-1">
            <ThoughtTrace events={thoughtTrace} />
          </div>
        </div>
      </div>
    </div>
  )
}

