import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Product, ChatMessage, UserId } from '../types'
import { api, StreamEvent } from '../lib/api'
import { Send, Loader2, X, ExternalLink, ChevronDown, ChevronRight, Settings, Database } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { ProductDetailModal } from './ProductDetailModal'

interface AgentStep {
  type: 'reasoning' | 'tool_call';
  reasoning?: string;
  tool_call_id?: string;
  tool_id?: string;
  params?: any;
  results?: any[];
}

interface ExtendedChatMessage extends ChatMessage {
  steps?: AgentStep[];
  status?: 'thinking' | 'working' | 'typing' | 'complete';
}

interface ChatModalProps {
  isOpen: boolean
  onClose: () => void
  userId: UserId
  onOpenTripPlanner: () => void
  initialMessage?: string
  onInitialMessageSent?: () => void
}

export function ChatModal({ isOpen, onClose, userId, onOpenTripPlanner, initialMessage, onInitialMessageSent }: ChatModalProps) {
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [stepsExpanded, setStepsExpanded] = useState<Record<string, boolean>>({})
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [isProductModalOpen, setIsProductModalOpen] = useState(false)
  const [modalHeight, setModalHeight] = useState(700)
  const [isDragging, setIsDragging] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialMessageSentRef = useRef(false)
  const dragStartY = useRef(0)
  const dragStartHeight = useRef(0)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle initial message when modal opens with context
  useEffect(() => {
    if (isOpen && initialMessage && !initialMessageSentRef.current && !isLoading) {
      initialMessageSentRef.current = true
      sendMessage(initialMessage)
      onInitialMessageSent?.()
    }
  }, [isOpen, initialMessage])

  // Reset the ref when modal closes
  useEffect(() => {
    if (!isOpen) {
      initialMessageSentRef.current = false
    }
  }, [isOpen])

  // Drag listeners effect
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleDragMove)
      window.addEventListener('mouseup', handleDragEnd)
      return () => {
        window.removeEventListener('mousemove', handleDragMove)
        window.removeEventListener('mouseup', handleDragEnd)
      }
    }
  }, [isDragging])

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepId)) {
        newSet.delete(stepId)
      } else {
        newSet.add(stepId)
      }
      return newSet
    })
  }

  // Drag handlers for resizable modal
  const handleDragStart = (e: React.MouseEvent) => {
    setIsDragging(true)
    dragStartY.current = e.clientY
    dragStartHeight.current = modalHeight
    document.body.style.cursor = 'ns-resize'
    document.body.style.userSelect = 'none'
  }

  const handleDragMove = (e: MouseEvent) => {
    if (!isDragging) return
    const deltaY = dragStartY.current - e.clientY
    const newHeight = Math.min(window.innerHeight * 0.95, Math.max(300, dragStartHeight.current + deltaY))
    setModalHeight(newHeight)
  }

  const handleDragEnd = () => {
    setIsDragging(false)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  // Product extraction helper
  const extractProductMentions = (content: string): Array<{name: string, price?: string}> => {
    const products: Array<{name: string, price?: string}> = []
    
    // Match patterns like "**ProductName** - $99.99" or "- ProductName ($99.99)"
    const patterns = [
      /\*\*([^*]+)\*\*\s*-?\s*\$(\d+\.?\d*)/g,
      /-\s*([^(\n]+)\s*\(\$(\d+\.?\d*)\)/g,
    ]
    
    patterns.forEach(pattern => {
      let match
      while ((match = pattern.exec(content)) !== null) {
        products.push({
          name: match[1].trim(),
          price: match[2]
        })
      }
    })
    
    return products
  }

  // Handle product click
  const handleProductClick = async (productName: string) => {
    try {
      const results = await api.searchProducts(productName, 1)
      if (results.products.length > 0) {
        setSelectedProduct(results.products[0])
        setIsProductModalOpen(true)
      }
    } catch (error) {
      console.error('Failed to fetch product:', error)
    }
  }

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || isLoading) return

    const userMessage: ExtendedChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Create placeholder assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: ExtendedChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      steps: [],
      status: 'thinking'
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      let currentSteps: AgentStep[] = []
      let currentContent = ''

      await api.streamChat(messageText.trim(), userId, (event: StreamEvent) => {
        const { type, data } = event

        switch (type) {
          case 'reasoning':
            currentSteps = [...currentSteps, {
              type: 'reasoning',
              reasoning: data.reasoning
            }]
            updateAssistantMessage(assistantMessageId, currentContent, currentSteps, 'thinking')
            break

          case 'tool_call':
            // Skip if no tool_id (progress updates)
            if (!data.tool_id) break
            
            // Check if this tool_call already exists
            const existingToolCall = currentSteps.find(s => s.tool_call_id === data.tool_call_id)
            if (!existingToolCall && data.params && Object.keys(data.params).length > 0) {
              currentSteps = [...currentSteps, {
                type: 'tool_call',
                tool_call_id: data.tool_call_id,
                tool_id: data.tool_id,
                params: data.params,
                results: []
              }]
              updateAssistantMessage(assistantMessageId, currentContent, currentSteps, 'working')
            }
            break

          case 'tool_result':
            // Update the matching tool_call step with results
            const toolCallId = data.tool_call_id
            currentSteps = currentSteps.map(step => 
              step.tool_call_id === toolCallId 
                ? { ...step, results: data.results }
                : step
            )
            updateAssistantMessage(assistantMessageId, currentContent, currentSteps, 'working')
            break

          case 'message_chunk':
            currentContent += data.text_chunk || ''
            updateAssistantMessage(assistantMessageId, currentContent, currentSteps, 'typing')
            break

          case 'message_complete':
            currentContent = data.message_content || currentContent
            updateAssistantMessage(assistantMessageId, currentContent, currentSteps, 'complete')
            break

          case 'completion':
            updateAssistantMessage(assistantMessageId, currentContent, currentSteps, 'complete')
            break

          case 'error':
            currentContent = `Error: ${data.error}`
            updateAssistantMessage(assistantMessageId, currentContent, currentSteps, 'complete')
            break
        }
      })
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ExtendedChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        timestamp: new Date(),
        status: 'complete'
      }
      setMessages((prev) => prev.map(msg => 
        msg.id === assistantMessageId ? errorMessage : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const updateAssistantMessage = (
    messageId: string, 
    content: string, 
    steps: AgentStep[], 
    status: 'thinking' | 'working' | 'typing' | 'complete'
  ) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, content, steps, status }
        : msg
    ))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await sendMessage(input)
  }

  const renderStep = (step: AgentStep, index: number, messageId: string) => {
    const stepId = `${messageId}-${index}`
    const isExpanded = expandedSteps.has(stepId)

    return (
      <div key={index} className="bg-primary/10 rounded-lg border border-primary/20 overflow-hidden">
        <button
          onClick={() => toggleStep(stepId)}
          className="w-full flex items-center justify-between p-2 hover:bg-primary/20 transition-colors"
        >
          <div className="flex items-center gap-2">
            {step.type === 'reasoning' ? (
              <>
                <Settings className="h-3 w-3 text-primary" />
                <span className="text-xs font-medium text-primary">Reasoning</span>
              </>
            ) : (
              <>
                <Database className="h-3 w-3 text-primary" />
                <span className="text-xs font-medium text-primary">{step.tool_id || 'Tool Call'}</span>
                {step.params && Object.keys(step.params).length > 0 && (
                  <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                    {Object.keys(step.params).length} param{Object.keys(step.params).length !== 1 ? 's' : ''}
                  </span>
                )}
              </>
            )}
          </div>
          {isExpanded ? (
            <ChevronDown className="h-3 w-3 text-primary" />
          ) : (
            <ChevronRight className="h-3 w-3 text-primary" />
          )}
        </button>

        {isExpanded && (
          <div className="border-t border-primary/20 p-3 space-y-3 bg-primary/5">
            {step.type === 'reasoning' && step.reasoning && (
              <div>
                <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">
                  Agent Thinking:
                </div>
                <div className="bg-slate-800 rounded-md p-3">
                  <div className="text-xs text-gray-300 leading-relaxed">
                    {step.reasoning}
                  </div>
                </div>
              </div>
            )}

            {step.type === 'tool_call' && step.params && Object.keys(step.params).length > 0 && (
              <div>
                <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">
                  Parameters:
                </div>
                <div className="bg-slate-800 rounded-md p-3">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                    {JSON.stringify(step.params, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {step.type === 'tool_call' && step.results && step.results.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">
                  Results:
                </div>
                {step.results.map((result: any, resultIdx: number) => (
                  <div key={resultIdx} className="bg-slate-800 rounded-md p-3 mb-2">
                    {result.type === 'query' && result.data?.esql ? (
                      <div>
                        <div className="text-xs text-primary/70 font-medium mb-2">ES|QL Query:</div>
                        <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">
                          {result.data.esql}
                        </pre>
                      </div>
                    ) : result.type === 'tabular_data' && result.data ? (
                      <div>
                        <div className="text-xs text-primary/70 font-medium mb-2">
                          Found {result.data.values?.length || 0} results
                        </div>
                        {result.data.values && result.data.values.length > 0 && (
                          <div className="max-h-32 overflow-y-auto text-xs text-gray-300 font-mono">
                            {result.data.values.slice(0, 5).map((row: any[], rowIdx: number) => (
                              <div key={rowIdx} className="py-1 border-b border-slate-700 last:border-b-0">
                                {Array.isArray(row) ? row.slice(0, 4).join(' | ') : JSON.stringify(row)}
                              </div>
                            ))}
                            {result.data.values.length > 5 && (
                              <div className="py-2 text-gray-500">
                                ... and {result.data.values.length - 5} more
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono max-h-32 overflow-y-auto">
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    )
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
            style={{ height: `${modalHeight}px` }}
            className="fixed bottom-0 left-0 right-0 bg-slate-900 rounded-t-3xl shadow-2xl z-50 flex flex-col border-t border-white/10"
          >
            {/* Drag Handle */}
            <div
              onMouseDown={handleDragStart}
              className="absolute top-0 left-0 right-0 h-2 cursor-ns-resize hover:bg-primary/20 transition-colors group z-10"
            >
              <div className="absolute top-1 left-1/2 -translate-x-1/2 w-12 h-1 bg-slate-700 rounded-full group-hover:bg-primary/50 transition-colors" />
            </div>

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
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-primary text-white'
                          : 'bg-slate-800 text-gray-100'
                      }`}
                    >
                      {/* Status indicator for assistant messages */}
                      {message.role === 'assistant' && message.status && message.status !== 'complete' && (
                        <div className="flex items-center gap-2 mb-2">
                          {message.status === 'thinking' && (
                            <>
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                              <span className="text-xs text-blue-400 font-medium">Thinking...</span>
                            </>
                          )}
                          {message.status === 'working' && (
                            <>
                              <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse" />
                              <span className="text-xs text-orange-400 font-medium">Working...</span>
                            </>
                          )}
                          {message.status === 'typing' && (
                            <>
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                              <span className="text-xs text-green-400 font-medium">Typing...</span>
                            </>
                          )}
                        </div>
                      )}

                      {/* Agent Steps - Collapsed by Default */}
                      {message.steps && message.steps.length > 0 && (
                        <div className="mb-3">
                          <button
                            onClick={() => {
                              setStepsExpanded(prev => ({
                                ...prev,
                                [message.id]: !prev[message.id]
                              }))
                            }}
                            className="w-full flex items-center justify-between text-xs font-medium text-gray-400 mb-2 hover:text-gray-300 transition-colors p-1.5 rounded hover:bg-slate-700/50"
                          >
                            <div className="flex items-center gap-1.5">
                              <Settings className="h-3 w-3" />
                              <span>Agent Thinking</span>
                              <span className="text-xs bg-slate-700 text-gray-300 px-1.5 py-0.5 rounded-full">
                                {message.steps.filter(step => 
                                  (step.type === 'reasoning' && step.reasoning) || 
                                  (step.type === 'tool_call' && step.tool_id)
                                ).length}
                              </span>
                            </div>
                            {stepsExpanded[message.id] ? (
                              <ChevronDown className="h-3 w-3" />
                            ) : (
                              <ChevronRight className="h-3 w-3" />
                            )}
                          </button>
                          
                          {stepsExpanded[message.id] && (
                            <div className="space-y-1">
                              {message.steps
                                .filter(step => 
                                  (step.type === 'reasoning' && step.reasoning) || 
                                  (step.type === 'tool_call' && step.tool_id && step.params && Object.keys(step.params).length > 0)
                                )
                                .map((step, idx) => renderStep(step, idx, message.id))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Message content */}
                      {message.role === 'assistant' ? (
                        <>
                          <ReactMarkdown className="prose prose-invert prose-sm max-w-none prose-headings:text-white prose-p:text-gray-200 prose-strong:text-white prose-code:text-primary prose-code:bg-slate-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-slate-800 prose-li:text-gray-200 prose-ul:text-gray-200 prose-ol:text-gray-200">
                            {message.content}
                          </ReactMarkdown>
                          
                          {/* Product Previews */}
                          {message.status === 'complete' && (() => {
                            const products = extractProductMentions(message.content)
                            return products.length > 0 && (
                              <div className="mt-3 space-y-2">
                                <div className="text-xs font-medium text-gray-400 mb-1.5">Recommended Products:</div>
                                <div className="grid grid-cols-2 gap-2">
                                  {products.slice(0, 4).map((prod, idx) => (
                                    <button
                                      key={idx}
                                      onClick={() => handleProductClick(prod.name)}
                                      className="bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 hover:border-primary/50 rounded-lg p-2.5 transition-all text-left group"
                                    >
                                      <div className="text-xs font-medium text-white line-clamp-2 mb-1.5 group-hover:text-primary transition-colors">
                                        {prod.name}
                                      </div>
                                      {prod.price && (
                                        <div className="text-sm font-bold text-primary">${prod.price}</div>
                                      )}
                                      <div className="text-xs text-gray-500 mt-1 group-hover:text-gray-400 transition-colors">
                                        Click to view & add to cart
                                      </div>
                                    </button>
                                  ))}
                                </div>
                              </div>
                            )
                          })()}
                        </>
                      ) : (
                        <p className="text-sm">{message.content}</p>
                      )}
                      
                      <p className="text-xs opacity-70 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
              {isLoading && messages.length === 0 && (
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

          {/* Product Detail Modal */}
          {isProductModalOpen && (
            <ProductDetailModal
              product={selectedProduct}
              userId={userId}
              onClose={() => {
                setIsProductModalOpen(false)
                setSelectedProduct(null)
              }}
            />
          )}
        </>
      )}
    </AnimatePresence>
  )
}
