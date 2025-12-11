import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Product, ChatMessage, UserId } from '../types'
import { api, StreamEvent } from '../lib/api'
import { X, Search, Send, Loader2, ChevronRight, ChevronDown, MessageSquare, Zap, BookOpen, Settings, Database, Target, FileText, Plus, ShoppingCart } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { ProductDetailModal } from './ProductDetailModal'

type SearchMode = 'chat' | 'hybrid' | 'lexical'

interface SearchPanelProps {
  isOpen: boolean
  onClose: () => void
  userId: UserId
  initialMessage?: string
  onInitialMessageSent?: () => void
  onOpenTripPlanner?: () => void
}

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

// Map tool IDs to friendly contextual messages
function getToolStatusMessage(toolId: string): string {
  const toolMessages: Record<string, string> = {
    'tool-workflow-check-trip-safety': 'Checking weather conditions...',
    'tool-workflow-get-customer-profile': 'Looking up your preferences...',
    'tool-workflow-get-user-affinity': 'Analyzing your gear style...',
    'tool-search-product-search': 'Scanning the catalog...',
    'tool-esql-get-user-affinity': 'Reviewing your browsing history...',
  }
  return toolMessages[toolId] || 'Planning your adventure...'
}

// Get current thinking status from trace events
function getCurrentStatus(steps: AgentStep[], isLoading: boolean): string {
  if (!isLoading) return ''
  if (steps.length === 0) return 'Starting up...'
  
  const lastStep = steps[steps.length - 1]
  if (lastStep.type === 'reasoning') {
    return 'Thinking...'
  } else if (lastStep.type === 'tool_call') {
    return getToolStatusMessage(lastStep.tool_id || '')
  }
  return 'Working...'
}

export function SearchPanel({ isOpen, onClose, userId, initialMessage, onInitialMessageSent, onOpenTripPlanner }: SearchPanelProps) {
  const [mode, setMode] = useState<SearchMode>('chat')
  const [panelWidth, setPanelWidth] = useState(50) // Percentage of screen width
  const [isDragging, setIsDragging] = useState(false)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([])
  const [searchResults, setSearchResults] = useState<Product[]>([])
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [isProductModalOpen, setIsProductModalOpen] = useState(false)
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [stepsExpanded, setStepsExpanded] = useState<Record<string, boolean>>({})
  const [isDemoRunning, setIsDemoRunning] = useState(false)
  const [demoStep, setDemoStep] = useState<'intro' | 'lexical' | 'hybrid' | 'agentic' | 'complete'>('intro')
  const [demoLexicalResults, setDemoLexicalResults] = useState<Product[]>([])
  const [demoHybridResults, setDemoHybridResults] = useState<Product[]>([])
  const [demoAgenticMessage, setDemoAgenticMessage] = useState<ExtendedChatMessage | null>(null)
  const [demoAgenticProducts, setDemoAgenticProducts] = useState<Product[]>([])
  const [addingToCart, setAddingToCart] = useState<string | null>(null)
  const [demoLexicalQuery, setDemoLexicalQuery] = useState<any>(null)
  const [demoLexicalRawHits, setDemoLexicalRawHits] = useState<any[]>([])
  const [demoHybridQuery, setDemoHybridQuery] = useState<any>(null)
  const [demoHybridRawHits, setDemoHybridRawHits] = useState<any[]>([])
  const [queryExpanded, setQueryExpanded] = useState<{ lexical: boolean; hybrid: boolean }>({ lexical: false, hybrid: false })
  const [personalizationEnabled, setPersonalizationEnabled] = useState(false)
  const dragStartX = useRef(0)
  const dragStartWidth = useRef(50)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialMessageSentRef = useRef(false)

  const DEMO_QUERY = "waterproof hiking boots for rocky terrain"

  // Get persona display name
  const getPersonaName = (id: UserId) => {
    const personas: Record<string, string> = {
      'user_member': '👤 Sarah - Ultralight Hiker',
      'user_business': '👔 Mike - Family Adventurer', 
      'user_new': '🆕 New Visitor'
    }
    return personas[id] || id
  }

  // Extract products from agent tool results
  const extractProductsFromSteps = (steps: AgentStep[]): Product[] => {
    const products: Product[] = []
    const seenIds = new Set<string>()
    
    for (const step of steps) {
      if (step.type === 'tool_call' && step.results) {
        for (const result of step.results) {
          // Handle product search results (array of products)
          if (Array.isArray(result)) {
            for (const item of result) {
              if (item.id && item.title && !seenIds.has(item.id)) {
                seenIds.add(item.id)
                products.push(item as Product)
              }
            }
          }
          // Handle single product result
          if (result.id && result.title && !seenIds.has(result.id)) {
            seenIds.add(result.id)
            products.push(result as Product)
          }
          // Handle nested results structure
          if (result.products && Array.isArray(result.products)) {
            for (const item of result.products) {
              if (item.id && item.title && !seenIds.has(item.id)) {
                seenIds.add(item.id)
                products.push(item as Product)
              }
            }
          }
        }
      }
    }
    return products.slice(0, 5) // Limit to top 5
  }

  // Add to cart handler for demo products
  const handleAddToCart = async (product: Product) => {
    setAddingToCart(product.id)
    try {
      await api.addToCart(userId, product.id)
      // Could add a toast notification here
    } catch (error) {
      console.error('Failed to add to cart:', error)
    } finally {
      setAddingToCart(null)
    }
  }

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, searchResults, demoLexicalResults, demoHybridResults, demoAgenticMessage])

  // Handle initial message when panel opens with context
  useEffect(() => {
    if (isOpen && initialMessage && !initialMessageSentRef.current && !isLoading) {
      initialMessageSentRef.current = true
      setMode('chat')
      sendMessage(initialMessage)
      onInitialMessageSent?.()
    }
  }, [isOpen, initialMessage])

  // Reset the ref when panel closes
  useEffect(() => {
    if (!isOpen) {
      initialMessageSentRef.current = false
      // Reset demo state when closed
      setIsDemoRunning(false)
      setDemoStep('intro')
      setDemoLexicalResults([])
      setDemoHybridResults([])
      setDemoAgenticMessage(null)
      setDemoAgenticProducts([])
      setDemoLexicalQuery(null)
      setDemoLexicalRawHits([])
      setDemoHybridQuery(null)
      setDemoHybridRawHits([])
      setQueryExpanded({ lexical: false, hybrid: false })
    }
  }, [isOpen])

  // Drag listeners
  useEffect(() => {
    if (isDragging) {
      const handleMouseMove = (e: MouseEvent) => {
        const deltaX = dragStartX.current - e.clientX
        const newWidth = Math.min(90, Math.max(30, dragStartWidth.current + (deltaX / window.innerWidth) * 100))
        setPanelWidth(newWidth)
      }
      const handleMouseUp = () => {
        setIsDragging(false)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
      
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging])

  const handleDragStart = (e: React.MouseEvent) => {
    setIsDragging(true)
    dragStartX.current = e.clientX
    dragStartWidth.current = panelWidth
    document.body.style.cursor = 'ew-resize'
    document.body.style.userSelect = 'none'
  }

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
            if (!data.tool_id) break
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
      updateAssistantMessage(
        assistantMessageId, 
        `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`, 
        [], 
        'complete'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async (query: string, searchMode: SearchMode) => {
    if (!query.trim() || isLoading) return

    setIsLoading(true)
    setSearchResults([])

    try {
      let results: { products: Product[]; total: number; personalized?: boolean }
      const userIdForSearch = personalizationEnabled ? userId : undefined
      if (searchMode === 'lexical') {
        results = await api.lexicalSearch(query, 10, userIdForSearch)
      } else {
        results = await api.hybridSearch(query, 10, userIdForSearch)
      }
      setSearchResults(results.products)
    } catch (error) {
      console.error(`Search error (${searchMode}):`, error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (mode === 'chat') {
      await sendMessage(input)
    } else {
      await handleSearch(input, mode)
    }
  }

  // Demo functionality
  const runDemo = async () => {
    setIsDemoRunning(true)
    setDemoStep('intro')
    setDemoLexicalResults([])
    setDemoHybridResults([])
    setDemoAgenticMessage(null)
    setDemoAgenticProducts([])
    setDemoLexicalQuery(null)
    setDemoLexicalRawHits([])
    setDemoHybridQuery(null)
    setDemoHybridRawHits([])
    setQueryExpanded({ lexical: false, hybrid: false })
    setMessages([])
    setSearchResults([])
  }

  const advanceDemo = async () => {
    if (isLoading) return

    if (demoStep === 'intro') {
      setDemoStep('lexical')
      setIsLoading(true)
      try {
        const results = await api.lexicalSearch(DEMO_QUERY)
        setDemoLexicalResults(results.products)
        setDemoLexicalQuery(results.es_query || null)
        setDemoLexicalRawHits(results.raw_hits || [])
      } catch (error) {
        console.error('Demo lexical search failed:', error)
      } finally {
        setIsLoading(false)
      }
    } else if (demoStep === 'lexical') {
      setDemoStep('hybrid')
      setIsLoading(true)
      try {
        const results = await api.hybridSearch(DEMO_QUERY)
        setDemoHybridResults(results.products)
        setDemoHybridQuery(results.es_query || null)
        setDemoHybridRawHits(results.raw_hits || [])
      } catch (error) {
        console.error('Demo hybrid search failed:', error)
      } finally {
        setIsLoading(false)
      }
    } else if (demoStep === 'hybrid') {
      setDemoStep('agentic')
      setIsLoading(true)
      
      const assistantMessageId = Date.now().toString()
      const assistantMessage: ExtendedChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        steps: [],
        status: 'thinking'
      }
      setDemoAgenticMessage(assistantMessage)

      try {
        let currentSteps: AgentStep[] = []
        let currentContent = ''

        await api.streamChat(DEMO_QUERY, userId, (event: StreamEvent) => {
          const { type, data } = event

          switch (type) {
            case 'reasoning':
              currentSteps = [...currentSteps, {
                type: 'reasoning',
                reasoning: data.reasoning
              }]
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'thinking' } : null)
              break

            case 'tool_call':
              if (!data.tool_id) break
              const existingToolCall = currentSteps.find(s => s.tool_call_id === data.tool_call_id)
              if (!existingToolCall && data.params && Object.keys(data.params).length > 0) {
                currentSteps = [...currentSteps, {
                  type: 'tool_call',
                  tool_call_id: data.tool_call_id,
                  tool_id: data.tool_id,
                  params: data.params,
                  results: []
                }]
                setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'working' } : null)
              }
              break

            case 'tool_result':
              const toolCallId = data.tool_call_id
              currentSteps = currentSteps.map(step => 
                step.tool_call_id === toolCallId 
                  ? { ...step, results: data.results }
                  : step
              )
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'working' } : null)
              break

            case 'message_chunk':
              currentContent += data.text_chunk || ''
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'typing' } : null)
              break

            case 'message_complete':
              currentContent = data.message_content || currentContent
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'complete' } : null)
              break

            case 'completion':
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'complete' } : null)
              // Extract products from tool results
              setDemoAgenticProducts(extractProductsFromSteps(currentSteps))
              break

            case 'error':
              currentContent = `Error: ${data.error}`
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'complete' } : null)
              break
          }
        })
        // Also extract products after stream completes
        setDemoAgenticProducts(extractProductsFromSteps(currentSteps))
      } catch (error) {
        console.error('Demo agentic search failed:', error)
        setDemoAgenticMessage(prev => prev ? { ...prev, content: `Error: ${error instanceof Error ? error.message : 'Failed'}`, status: 'complete' } : null)
      } finally {
        setIsLoading(false)
      }
    } else if (demoStep === 'agentic') {
      setDemoStep('complete')
      setIsDemoRunning(false)
    }
  }

  const handleProductClick = (product: Product) => {
    setSelectedProduct(product)
    setIsProductModalOpen(true)
  }

  const getModeBgClass = (currentMode: SearchMode) => {
    switch (currentMode) {
      case 'chat': return 'bg-slate-900'
      case 'hybrid': return 'bg-gradient-to-br from-slate-900 to-cyan-950/30'
      case 'lexical': return 'bg-gradient-to-br from-slate-900 to-amber-950/30'
      default: return 'bg-slate-900'
    }
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
              </>
            )}
          </div>
          {isExpanded ? <ChevronDown className="h-3 w-3 text-primary" /> : <ChevronRight className="h-3 w-3 text-primary" />}
        </button>

        {isExpanded && (
          <div className="border-t border-primary/20 p-3 space-y-3 bg-primary/5">
            {step.type === 'reasoning' && step.reasoning && (
              <div>
                <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">Agent Thinking:</div>
                <div className="bg-slate-800 rounded-md p-3">
                  <div className="text-xs text-gray-300 leading-relaxed">{step.reasoning}</div>
                </div>
              </div>
            )}

            {step.type === 'tool_call' && step.params && Object.keys(step.params).length > 0 && (
              <div>
                <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">Parameters:</div>
                <div className="bg-slate-800 rounded-md p-3">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                    {JSON.stringify(step.params, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {step.type === 'tool_call' && step.results && step.results.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">Results:</div>
                {step.results.map((result: any, resultIdx: number) => (
                  <div key={resultIdx} className="bg-slate-800 rounded-md p-3 mb-2">
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono max-h-32 overflow-y-auto">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderDemoContent = () => {
    return (
      <div className="space-y-6">
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-2">🎯 Demo Query</h3>
          <p className="text-primary font-medium mb-3">"{DEMO_QUERY}"</p>
          <div className="flex items-center gap-2 text-sm text-gray-400 border-t border-slate-700 pt-3 mt-3">
            <span>Persona:</span>
            <span className="text-cyan-400 font-medium">{getPersonaName(userId)}</span>
            <span className="text-xs text-gray-500">(has personalized clickstream data)</span>
          </div>
        </div>

        {demoStep === 'intro' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 text-center"
          >
            <Zap className="w-12 h-12 text-primary mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">Watch the Difference</h3>
            <p className="text-gray-400 mb-4">
              See how different search approaches handle the same query:
            </p>
            <ul className="text-left text-gray-300 space-y-2 mb-6">
              <li className="flex items-center gap-2"><BookOpen className="w-4 h-4 text-amber-400" /> <strong>Lexical:</strong> Basic keyword matching</li>
              <li className="flex items-center gap-2"><Search className="w-4 h-4 text-cyan-400" /> <strong>Hybrid:</strong> Semantic + keyword combined</li>
              <li className="flex items-center gap-2"><MessageSquare className="w-4 h-4 text-primary" /> <strong>Agentic:</strong> AI-powered with tools</li>
            </ul>
            <button
              onClick={advanceDemo}
              className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl font-medium transition-all"
            >
              Start Demo →
            </button>
          </motion.div>
        )}

        {(demoStep === 'lexical' || demoStep === 'hybrid' || demoStep === 'agentic' || demoStep === 'complete') && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl p-4 border ${demoStep === 'lexical' ? 'bg-amber-950/30 border-amber-700' : 'bg-slate-800/30 border-slate-700'}`}
          >
            <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-400" /> Lexical Search
              <span className="text-xs bg-amber-900/50 text-amber-300 px-2 py-0.5 rounded-full">BM25</span>
            </h4>
            {isLoading && demoStep === 'lexical' ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-5 h-5 animate-spin text-amber-400" />
                <span className="ml-2 text-gray-400">Running keyword search...</span>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Show Query - expandable */}
                {demoLexicalQuery && demoLexicalRawHits.length > 0 && (
                  <>
                    <button
                      onClick={() => setQueryExpanded(prev => ({ ...prev, lexical: !prev.lexical }))}
                      className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300 transition-colors"
                    >
                      {queryExpanded.lexical ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      <span>Show Query (2 sections)</span>
                    </button>
                    
                    {queryExpanded.lexical && (
                      <div className="space-y-2">
                        {/* Query Box */}
                        <div className="bg-slate-800/50 rounded-lg border border-amber-700/30 overflow-hidden">
                          <div className="px-3 py-2 border-b border-amber-700/30 flex items-center gap-2">
                            <Database className="w-4 h-4 text-amber-400" />
                            <span className="text-xs font-medium text-amber-400 uppercase tracking-wide">QUERY</span>
                          </div>
                          <pre className="p-3 text-xs text-gray-300 overflow-x-auto max-h-48 overflow-y-auto">
                            {JSON.stringify(demoLexicalQuery, null, 2)}
                          </pre>
                        </div>
                        
                        {/* Top Results Box */}
                        <div className="bg-slate-800/50 rounded-lg border border-amber-700/30 overflow-hidden">
                          <div className="px-3 py-2 border-b border-amber-700/30 flex items-center gap-2">
                            <FileText className="w-4 h-4 text-amber-400" />
                            <span className="text-xs font-medium text-amber-400 uppercase tracking-wide">TOP 3 RESPONSE DOCS</span>
                          </div>
                          <pre className="p-3 text-xs text-gray-300 overflow-x-auto max-h-64 overflow-y-auto">
                            {JSON.stringify(demoLexicalRawHits, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </>
                )}
                
                {/* Product Results */}
                <div className="space-y-2">
                  {demoLexicalResults.length === 0 ? (
                    <p className="text-gray-500 text-sm">Waiting for search...</p>
                  ) : (
                    <>
                      {demoLexicalResults.slice(0, 3).map((product) => (
                        <div
                          key={product.id}
                          className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 cursor-pointer hover:border-amber-600/50 transition-colors"
                          onClick={() => handleProductClick(product)}
                        >
                          <h5 className="font-medium text-white text-sm">{product.title}</h5>
                          <p className="text-xs text-gray-400 mt-1">${product.price?.toFixed(2)}</p>
                        </div>
                      ))}
                      {demoLexicalResults.length > 3 && (
                        <p className="text-xs text-gray-500">+{demoLexicalResults.length - 3} more results</p>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {(demoStep === 'hybrid' || demoStep === 'agentic' || demoStep === 'complete') && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl p-4 border ${demoStep === 'hybrid' ? 'bg-cyan-950/30 border-cyan-700' : 'bg-slate-800/30 border-slate-700'}`}
          >
            <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
              <Search className="w-5 h-5 text-cyan-400" /> Hybrid Search
              <span className="text-xs bg-cyan-900/50 text-cyan-300 px-2 py-0.5 rounded-full">Semantic + BM25</span>
            </h4>
            {isLoading && demoStep === 'hybrid' ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
                <span className="ml-2 text-gray-400">Running hybrid search...</span>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Show Query - expandable */}
                {demoHybridQuery && demoHybridRawHits.length > 0 && (
                  <>
                    <button
                      onClick={() => setQueryExpanded(prev => ({ ...prev, hybrid: !prev.hybrid }))}
                      className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300 transition-colors"
                    >
                      {queryExpanded.hybrid ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      <span>Show Query (2 sections)</span>
                    </button>
                    
                    {queryExpanded.hybrid && (
                      <div className="space-y-2">
                        {/* Query Box */}
                        <div className="bg-slate-800/50 rounded-lg border border-cyan-700/30 overflow-hidden">
                          <div className="px-3 py-2 border-b border-cyan-700/30 flex items-center gap-2">
                            <Database className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-medium text-cyan-400 uppercase tracking-wide">QUERY</span>
                          </div>
                          <pre className="p-3 text-xs text-gray-300 overflow-x-auto max-h-48 overflow-y-auto">
                            {JSON.stringify(demoHybridQuery, null, 2)}
                          </pre>
                        </div>
                        
                        {/* Top Results Box */}
                        <div className="bg-slate-800/50 rounded-lg border border-cyan-700/30 overflow-hidden">
                          <div className="px-3 py-2 border-b border-cyan-700/30 flex items-center gap-2">
                            <FileText className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-medium text-cyan-400 uppercase tracking-wide">TOP 3 RESPONSE DOCS</span>
                          </div>
                          <pre className="p-3 text-xs text-gray-300 overflow-x-auto max-h-64 overflow-y-auto">
                            {JSON.stringify(demoHybridRawHits, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </>
                )}
                
                {/* Product Results */}
                <div className="space-y-2">
                  {demoHybridResults.length === 0 ? (
                    <p className="text-gray-500 text-sm">Waiting for search...</p>
                  ) : (
                    <>
                      {demoHybridResults.slice(0, 3).map((product) => (
                        <div
                          key={product.id}
                          className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 cursor-pointer hover:border-cyan-600/50 transition-colors"
                          onClick={() => handleProductClick(product)}
                        >
                          <h5 className="font-medium text-white text-sm">{product.title}</h5>
                          <p className="text-xs text-gray-400 mt-1">${product.price?.toFixed(2)}</p>
                        </div>
                      ))}
                      {demoHybridResults.length > 3 && (
                        <p className="text-xs text-gray-500">+{demoHybridResults.length - 3} more results</p>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {(demoStep === 'agentic' || demoStep === 'complete') && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl p-4 border bg-primary/10 border-primary/30"
          >
            <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary" /> Agentic Search
              <span className="text-xs bg-primary/30 text-primary px-2 py-0.5 rounded-full">AI + Tools</span>
            </h4>
            {demoAgenticMessage ? (
              <div className="space-y-3">
                {/* Status */}
                {demoAgenticMessage.status && demoAgenticMessage.status !== 'complete' && (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-sm text-primary font-medium">
                      {getCurrentStatus(demoAgenticMessage.steps || [], true)}
                    </span>
                  </div>
                )}
                
                {/* Steps */}
                {demoAgenticMessage.steps && demoAgenticMessage.steps.length > 0 && (
                  <div className="space-y-1">
                    <button
                      onClick={() => setStepsExpanded(prev => ({ ...prev, 'demo': !prev['demo'] }))}
                      className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300"
                    >
                      {stepsExpanded['demo'] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      <span>Thought Trace ({demoAgenticMessage.steps.filter(s => s.reasoning || s.tool_id).length} steps)</span>
                    </button>
                    {stepsExpanded['demo'] && (
                      <div className="space-y-1 mt-2">
                        {demoAgenticMessage.steps
                          .filter(step => step.reasoning || (step.tool_id && step.params))
                          .map((step, idx) => renderStep(step, idx, 'demo'))}
                      </div>
                    )}
                  </div>
                )}
                
                {/* Product Cards */}
                {demoAgenticProducts.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-primary/70 uppercase tracking-wide">Recommended Products</div>
                    <div className="grid gap-2">
                      {demoAgenticProducts.map((product) => (
                        <div
                          key={product.id}
                          className="flex items-center gap-3 bg-slate-800/80 rounded-lg p-3 border border-primary/20 hover:border-primary/40 transition-colors"
                        >
                          {/* Product Image */}
                          <div className="flex-shrink-0 w-12 h-12 bg-slate-700 rounded-lg overflow-hidden">
                            {product.image_url ? (
                              <img
                                src={product.image_url}
                                alt={product.title}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = '/images/products/placeholder.jpg'
                                }}
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-500">
                                <ShoppingCart className="w-5 h-5" />
                              </div>
                            )}
                          </div>
                          
                          {/* Product Info */}
                          <div className="flex-1 min-w-0">
                            <h5 
                              className="font-medium text-white text-sm truncate cursor-pointer hover:text-primary transition-colors"
                              onClick={() => handleProductClick(product)}
                            >
                              {product.title}
                            </h5>
                            <p className="text-xs text-gray-400">${product.price?.toFixed(2)}</p>
                          </div>
                          
                          {/* Add to Cart Button */}
                          <button
                            onClick={() => handleAddToCart(product)}
                            disabled={addingToCart === product.id}
                            className="flex-shrink-0 flex items-center gap-1 px-3 py-1.5 bg-primary hover:bg-primary-dark disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-colors"
                          >
                            {addingToCart === product.id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Plus className="w-3 h-3" />
                            )}
                            <span>Add</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Response Text (collapsed if products shown) */}
                {demoAgenticMessage.content && (
                  <div className={`bg-slate-800/50 rounded-lg p-3 ${demoAgenticProducts.length > 0 ? 'border border-slate-700' : ''}`}>
                    <div className="prose prose-invert prose-sm max-w-none text-gray-300">
                      <ReactMarkdown>{demoAgenticMessage.content}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Waiting for agent response...</p>
            )}
          </motion.div>
        )}

        {demoStep !== 'intro' && demoStep !== 'complete' && (
          <div className="flex justify-center">
            <button
              onClick={advanceDemo}
              disabled={isLoading}
              className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl font-medium transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  {demoStep === 'lexical' && 'Show Hybrid →'}
                  {demoStep === 'hybrid' && 'Show Agentic →'}
                  {demoStep === 'agentic' && 'Complete Demo'}
                </>
              )}
            </button>
          </div>
        )}

        {demoStep === 'complete' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-primary/20 to-cyan-500/20 rounded-xl p-6 border border-primary/30 text-center"
          >
            <h3 className="text-xl font-bold text-white mb-2">✨ Demo Complete!</h3>
            <p className="text-gray-300 mb-4">
              Notice how agentic search provides context-aware recommendations with reasoning.
            </p>
            <button
              onClick={() => {
                setIsDemoRunning(false)
                setMode('chat')
              }}
              className="bg-white/10 hover:bg-white/20 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Try it yourself
            </button>
          </motion.div>
        )}
      </div>
    )
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop - clicking closes panel */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed inset-y-0 right-0 z-50 flex"
            style={{ width: `${panelWidth}vw` }}
          >
            {/* Draggable Resizer */}
            <div
              onMouseDown={handleDragStart}
              className="w-2 bg-slate-700/50 hover:bg-primary/50 cursor-ew-resize absolute left-0 top-0 bottom-0 z-10 transition-colors"
            />

            {/* Panel Content */}
            <div className={`flex flex-col w-full ${getModeBgClass(mode)} shadow-2xl border-l border-slate-700`}>
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-slate-700">
                <h2 className="text-xl font-display font-bold text-white">Search & Chat</h2>
                <div className="flex items-center gap-2">
                  {/* Personalization Toggle - only show for search modes */}
                  {(mode === 'hybrid' || mode === 'lexical') && !isDemoRunning && (
                    <button
                      onClick={() => setPersonalizationEnabled(!personalizationEnabled)}
                      className={`px-3 py-1.5 text-sm rounded-lg transition-all flex items-center gap-1.5 ${
                        personalizationEnabled
                          ? 'bg-primary text-white shadow-md shadow-primary/30'
                          : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                      }`}
                      title={personalizationEnabled ? 'Disable personalization' : 'Enable personalization based on your browsing history'}
                    >
                      <Target className={`w-4 h-4 ${personalizationEnabled ? 'animate-pulse' : ''}`} />
                      <span className="hidden sm:inline">Personalize</span>
                    </button>
                  )}
                  {/* Watch This Demo Button */}
                  <button
                    onClick={runDemo}
                    disabled={isDemoRunning}
                    className="px-3 py-1.5 text-sm bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg transition-colors flex items-center gap-1.5 text-white"
                  >
                    <Zap className="w-4 h-4" /> Watch This
                  </button>
                  <button
                    onClick={onClose}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-300" />
                  </button>
                </div>
              </div>

              {/* Mode Selector */}
              {!isDemoRunning && (
                <div className="p-4 border-b border-slate-700 space-y-2">
                  {/* Personalization Indicator */}
                  {personalizationEnabled && (mode === 'hybrid' || mode === 'lexical') && (
                    <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/30 rounded-lg">
                      <Target className="w-4 h-4 text-primary" />
                      <span className="text-sm text-primary font-medium">Personalization enabled</span>
                      <span className="text-xs text-gray-400">Results tailored to your browsing history</span>
                    </div>
                  )}
                  <div className="flex bg-slate-800 rounded-full p-1">
                    <button
                      onClick={() => { setMode('chat'); setSearchResults([]) }}
                      className={`flex-1 py-2 px-4 rounded-full text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                        mode === 'chat' ? 'bg-primary text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <MessageSquare className="w-4 h-4" /> Chat
                    </button>
                    <button
                      onClick={() => { setMode('hybrid'); setMessages([]) }}
                      className={`flex-1 py-2 px-4 rounded-full text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                        mode === 'hybrid' ? 'bg-cyan-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <Search className="w-4 h-4" /> Hybrid
                    </button>
                    <button
                      onClick={() => { setMode('lexical'); setMessages([]) }}
                      className={`flex-1 py-2 px-4 rounded-full text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                        mode === 'lexical' ? 'bg-amber-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <BookOpen className="w-4 h-4" /> Lexical
                    </button>
                  </div>
                </div>
              )}

              {/* Content Area */}
              <div className="flex-1 overflow-y-auto p-4">
                {isDemoRunning ? (
                  renderDemoContent()
                ) : (
                  <>
                    {/* Chat Mode */}
                    {mode === 'chat' && (
                      <div className="space-y-4">
                        {messages.length === 0 ? (
                          <div className="flex items-center justify-center h-64 text-center">
                            <div>
                              <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                              <h3 className="text-lg font-semibold mb-2 text-white">Start a Conversation</h3>
                              <p className="text-gray-400 text-sm">
                                Ask about gear, get recommendations, or plan your trip
                              </p>
                            </div>
                          </div>
                        ) : (
                          messages.map((message) => (
                            <motion.div
                              key={message.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                              <div
                                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                                  message.role === 'user'
                                    ? 'bg-primary text-white'
                                    : 'bg-slate-800 text-gray-100'
                                }`}
                              >
                                {/* Status indicator */}
                                {message.role === 'assistant' && message.status && message.status !== 'complete' && (
                                  <div className="flex items-center gap-2 mb-2">
                                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                                    <span className="text-xs text-primary font-medium">
                                      {getCurrentStatus(message.steps || [], true)}
                                    </span>
                                  </div>
                                )}

                                {/* Agent Steps */}
                                {message.steps && message.steps.length > 0 && (
                                  <div className="mb-3">
                                    <button
                                      onClick={() => setStepsExpanded(prev => ({ ...prev, [message.id]: !prev[message.id] }))}
                                      className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300"
                                    >
                                      {stepsExpanded[message.id] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                      <span>Thought Trace ({message.steps.filter(s => s.reasoning || s.tool_id).length})</span>
                                    </button>
                                    {stepsExpanded[message.id] && (
                                      <div className="space-y-1 mt-2">
                                        {message.steps
                                          .filter(step => step.reasoning || (step.tool_id && step.params))
                                          .map((step, idx) => renderStep(step, idx, message.id))}
                                      </div>
                                    )}
                                  </div>
                                )}

                                {/* Message content */}
                                {message.role === 'assistant' ? (
                                  <div className="prose prose-invert prose-sm max-w-none">
                                    <ReactMarkdown>{message.content}</ReactMarkdown>
                                  </div>
                                ) : (
                                  <p className="text-sm">{message.content}</p>
                                )}
                                
                                <p className="text-xs opacity-70 mt-2">
                                  {message.timestamp.toLocaleTimeString()}
                                </p>
                              </div>
                            </motion.div>
                          ))
                        )}
                        <div ref={messagesEndRef} />
                      </div>
                    )}

                    {/* Hybrid/Lexical Mode */}
                    {(mode === 'hybrid' || mode === 'lexical') && (
                      <div className="space-y-4">
                        {searchResults.length === 0 && !isLoading ? (
                          <div className="flex items-center justify-center h-64 text-center">
                            <div>
                              <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                              <h3 className="text-lg font-semibold mb-2 text-white">
                                {mode === 'hybrid' ? 'Hybrid Search' : 'Lexical Search'}
                              </h3>
                              <p className="text-gray-400 text-sm">
                                {mode === 'hybrid' 
                                  ? 'Combines semantic understanding with keyword matching'
                                  : 'Basic BM25 keyword-based search'}
                              </p>
                            </div>
                          </div>
                        ) : (
                          <>
                            {searchResults.map((product) => (
                              <motion.div
                                key={product.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`rounded-xl p-4 border cursor-pointer transition-all ${
                                  mode === 'hybrid' 
                                    ? 'bg-cyan-950/30 border-cyan-700/50 hover:border-cyan-500' 
                                    : 'bg-amber-950/30 border-amber-700/50 hover:border-amber-500'
                                }`}
                                onClick={() => handleProductClick(product)}
                              >
                                <h3 className="text-lg font-semibold text-white mb-1">{product.title}</h3>
                                <p className="text-sm text-gray-300 mb-2">${product.price?.toFixed(2)}</p>
                                {product.description && (
                                  <p className="text-sm text-gray-400 line-clamp-2">{product.description}</p>
                                )}
                              </motion.div>
                            ))}
                          </>
                        )}
                        {isLoading && (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-primary" />
                            <span className="ml-3 text-gray-400">Searching...</span>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Input */}
              {!isDemoRunning && (
                <form onSubmit={handleSubmit} className="p-4 border-t border-slate-700">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder={mode === 'chat' ? "Ask about gear or your trip..." : "Search for products..."}
                      className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                      disabled={isLoading}
                    />
                    <button
                      type="submit"
                      disabled={!input.trim() || isLoading}
                      className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl transition-all disabled:opacity-50 flex items-center gap-2"
                    >
                      {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </button>
                  </div>
                </form>
              )}
            </div>
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
