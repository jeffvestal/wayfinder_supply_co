import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Product } from '../types'
import { api, StreamEvent } from '../lib/api'
import { ProductCard } from './ProductCard'
import { Loader2, X, BookOpen, Search, MessageSquare, ChevronDown, ChevronRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { ExtendedChatMessage, AgentStep } from './search/types'
import { StepRenderer } from './search/StepRenderer'

interface SearchComparisonDemoProps {
  onClose: () => void
  userId: string
}

export function SearchComparisonDemo({ onClose, userId }: SearchComparisonDemoProps) {
  const [lexicalResults, setLexicalResults] = useState<Product[]>([])
  const [hybridResults, setHybridResults] = useState<Product[]>([])
  const [agenticMessage, setAgenticMessage] = useState<ExtendedChatMessage | null>(null)
  const [agenticProducts, setAgenticProducts] = useState<Product[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [stepsExpanded, setStepsExpanded] = useState<boolean>(false)

  const query = 'gear to keep my feet dry on slippery mountain trails'

  // Helper to extract product IDs from agent tool results
  const extractProductIdsFromSteps = (steps: AgentStep[]): string[] => {
    const productIds: string[] = []
    for (const step of steps) {
      if (step.type === 'tool_call' && step.results) {
        for (const result of step.results) {
          if (result?.data?.reference?.id) {
            productIds.push(result.data.reference.id)
          }
          if (result?.content) {
            try {
              const content = typeof result.content === 'string' ? JSON.parse(result.content) : result.content
              if (content.documents && Array.isArray(content.documents)) {
                for (const doc of content.documents) {
                  if (doc.id) productIds.push(doc.id)
                  if (doc._source?.id) productIds.push(doc._source.id)
                }
              }
            } catch (e) {}
          }
        }
      }
    }
    return [...new Set(productIds)].slice(0, 3)
  }

  const fetchProductsFromIds = async (productIds: string[]): Promise<Product[]> => {
    const products: Product[] = []
    for (const id of productIds) {
      try {
        const product = await api.getProduct(id)
        if (product) products.push(product)
      } catch (e) {}
    }
    return products
  }

  useEffect(() => {
    const runComparison = async () => {
      setIsLoading(true)
      try {
        // Run lexical and hybrid searches
        const [lexical, hybrid] = await Promise.all([
          api.lexicalSearch(query, 10, undefined),
          api.hybridSearch(query, 10, undefined)
        ])
        setLexicalResults(lexical.products)
        setHybridResults(hybrid.products)

        // Initialize agentic message
        const initialAgentic: ExtendedChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          steps: [],
          status: 'thinking'
        }
        setAgenticMessage(initialAgentic)

        let currentSteps: AgentStep[] = []
        let currentContent = ''

        await api.streamChat(query, 'user_new', (event: StreamEvent) => {
          const { type, data } = event
          switch (type) {
            case 'reasoning':
              currentSteps = [...currentSteps, { type: 'reasoning', reasoning: data.reasoning }]
              setAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'thinking' } : null)
              break
            case 'tool_call':
              if (!data.tool_id) break
              currentSteps = [...currentSteps, {
                type: 'tool_call',
                tool_call_id: data.tool_call_id,
                tool_id: data.tool_id,
                params: data.params,
                results: []
              }]
              setAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'working' } : null)
              break
            case 'tool_result':
              currentSteps = currentSteps.map(step => 
                step.tool_call_id === data.tool_call_id ? { ...step, results: data.results } : step
              )
              setAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'working' } : null)
              break
            case 'message_chunk':
              currentContent += data.text_chunk || ''
              setAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'typing' } : null)
              break
            case 'message_complete':
            case 'completion':
              currentContent = data.message_content || currentContent
              setAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'complete' } : null)
              const ids = extractProductIdsFromSteps(currentSteps)
              fetchProductsFromIds(ids).then(products => setAgenticProducts(products))
              break
          }
        })
      } catch (error) {
        console.error('Search comparison demo failed:', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    runComparison()
  }, [])

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepId)) newSet.delete(stepId)
      else newSet.add(stepId)
      return newSet
    })
  }

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-sm flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 w-full max-w-7xl max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div>
            <h2 className="text-2xl font-display font-bold text-white mb-1">
              Search Mode Comparison
            </h2>
            <p className="text-gray-400 text-sm">
              Query: &quot;{query}&quot;
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5 text-gray-300" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Lexical Search */}
            <div className="bg-amber-950/20 border border-amber-700/30 rounded-lg p-4 h-fit">
              <div className="flex items-center gap-2 mb-4">
                <BookOpen className="w-5 h-5 text-amber-400" />
                <h3 className="text-lg font-semibold text-white">Lexical</h3>
                <span className="text-xs bg-amber-600/20 text-amber-400 px-2 py-0.5 rounded">
                  BM25
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-4">
                Keyword matching only - misses conceptual intent
              </p>
              <div className="space-y-3">
                {lexicalResults.length > 0 ? (
                  lexicalResults.slice(0, 3).map((product) => (
                    <ProductCard key={product.id} product={product} userId={userId} />
                  ))
                ) : isLoading ? (
                  <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-amber-500/50" /></div>
                ) : (
                  <p className="text-gray-500 text-sm">No results</p>
                )}
              </div>
            </div>

            {/* Hybrid Search */}
            <div className="bg-cyan-950/20 border border-cyan-700/30 rounded-lg p-4 h-fit">
              <div className="flex items-center gap-2 mb-4">
                <Search className="w-5 h-5 text-cyan-400" />
                <h3 className="text-lg font-semibold text-white">Hybrid</h3>
                <span className="text-xs bg-cyan-600/20 text-cyan-400 px-2 py-0.5 rounded">
                  Semantic + BM25
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-4">
                Combines semantic understanding with keywords
              </p>
              <div className="space-y-3">
                {hybridResults.length > 0 ? (
                  hybridResults.slice(0, 3).map((product) => (
                    <ProductCard key={product.id} product={product} userId={userId} />
                  ))
                ) : isLoading ? (
                  <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-cyan-500/50" /></div>
                ) : (
                  <p className="text-gray-500 text-sm">No results</p>
                )}
              </div>
            </div>

            {/* Agentic Search */}
            <div className="bg-primary/10 border border-primary/30 rounded-lg p-4 h-fit">
              <div className="flex items-center gap-2 mb-4">
                <MessageSquare className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold text-white">Agentic</h3>
                <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded">
                  AI Reasoning
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-4">
                AI agent reasons about intent and uses tools
              </p>
              
              <div className="bg-slate-800/50 rounded-lg p-4 mb-4">
                {agenticMessage ? (
                  <>
                    {/* Status */}
                    {agenticMessage.status !== 'complete' && (
                      <div className="flex items-center gap-2 mb-3">
                        <Loader2 className="w-4 h-4 animate-spin text-primary" />
                        <span className="text-xs text-primary font-medium">Agent is thinking...</span>
                      </div>
                    )}

                    {/* Thought Trace */}
                    {agenticMessage.steps && agenticMessage.steps.length > 0 && (
                      <div className="mb-3">
                        <button
                          onClick={() => setStepsExpanded(!stepsExpanded)}
                          className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300"
                        >
                          {stepsExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                          <span>Thought Trace ({agenticMessage.steps.length})</span>
                        </button>
                        {stepsExpanded && (
                          <div className="space-y-1 mt-2">
                            {agenticMessage.steps.map((step, idx) => (
                              <StepRenderer
                                key={idx}
                                step={step}
                                index={idx}
                                messageId={agenticMessage.id}
                                isExpanded={expandedSteps.has(`${agenticMessage.id}-${idx}`)}
                                onToggle={toggleStep}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Text content */}
                    <div className="prose prose-invert prose-sm max-w-none text-gray-200">
                      <ReactMarkdown>{agenticMessage.content}</ReactMarkdown>
                    </div>
                  </>
                ) : (
                  <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-primary/50" /></div>
                )}
              </div>

              {/* Agentic Products */}
              {agenticProducts.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-slate-700">
                  <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Recommended Gear</p>
                  {agenticProducts.map(product => (
                    <ProductCard key={product.id} product={product} userId={userId} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
