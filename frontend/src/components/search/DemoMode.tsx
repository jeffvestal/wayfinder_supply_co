import { motion } from 'framer-motion'
import { Product, UserId } from '../../types'
import { 
  Search, Loader2, ChevronRight, ChevronDown, MessageSquare, 
  Zap, BookOpen, Database, Target, FileText, Plus, ShoppingCart, Check 
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { 
  ExtendedChatMessage, AgentStep, DemoQueryType, 
  DEMO_QUERIES, FALLBACK_PRODUCT_IMAGE, getPersonaName 
} from './types'
import { StepRenderer } from './StepRenderer'
import { getToolStatusMessage } from '../../lib/constants'

type DemoStep = 'intro' | 'lexical' | 'hybrid' | 'agentic' | 'complete'

interface DemoModeProps {
  userId: UserId
  isLoading: boolean
  personalizationEnabled: boolean
  demoStep: DemoStep
  selectedDemoQuery: DemoQueryType | null
  // Lexical results
  demoLexicalResults: Product[]
  demoLexicalQuery: any
  demoLexicalRawHits: any[]
  // Hybrid results
  demoHybridResults: Product[]
  demoHybridQuery: any
  demoHybridRawHits: any[]
  // Agentic results
  demoAgenticMessage: ExtendedChatMessage | null
  demoAgenticProducts: Product[]
  // UI state
  queryExpanded: { lexical: boolean; hybrid: boolean }
  stepsExpanded: Record<string, boolean>
  expandedSteps: Set<string>
  addingToCart: string | null
  justAddedToCart: string | null
  // Callbacks
  onRunDemo: (queryType: DemoQueryType) => void
  onAdvanceDemo: () => void
  onProductClick: (product: Product) => void
  onAddToCart: (product: Product) => void
  onToggleQueryExpanded: (type: 'lexical' | 'hybrid') => void
  onToggleStepsExpanded: (messageId: string) => void
  onToggleStep: (stepId: string) => void
  onExitDemo: () => void
  onStartChat: () => void
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

export function DemoMode({
  userId,
  isLoading,
  personalizationEnabled,
  demoStep,
  selectedDemoQuery,
  demoLexicalResults,
  demoLexicalQuery,
  demoLexicalRawHits,
  demoHybridResults,
  demoHybridQuery,
  demoHybridRawHits,
  demoAgenticMessage,
  demoAgenticProducts,
  queryExpanded,
  stepsExpanded,
  expandedSteps,
  addingToCart,
  justAddedToCart,
  onRunDemo,
  onAdvanceDemo,
  onProductClick,
  onAddToCart,
  onToggleQueryExpanded,
  onToggleStepsExpanded,
  onToggleStep,
  onExitDemo,
  onStartChat,
}: DemoModeProps) {
  return (
    <div className="space-y-6">
      {/* Demo Query Header - only show when a query is selected */}
      {selectedDemoQuery && (
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-2">🎯 Demo Query</h3>
          <p className="text-primary font-medium mb-2">"{DEMO_QUERIES[selectedDemoQuery].query}"</p>
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
            <span className="bg-slate-700 px-2 py-1 rounded">{DEMO_QUERIES[selectedDemoQuery].icon} {DEMO_QUERIES[selectedDemoQuery].label}</span>
            <span>→</span>
            <span className="text-cyan-400">{DEMO_QUERIES[selectedDemoQuery].winner}</span>
          </div>
          <div className="flex flex-col gap-2 text-sm text-gray-400 border-t border-slate-700 pt-3 mt-3">
            <div className="flex items-center gap-2">
              <span>Persona:</span>
              <span className="text-cyan-400 font-medium">{getPersonaName(userId)}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Personalization:</span>
              {personalizationEnabled ? (
                <span className="flex items-center gap-1 text-green-400 font-medium">
                  <Target className="w-3 h-3" /> ON - results boosted by browsing history
                </span>
              ) : (
                <span className="text-gray-500">OFF - generic results</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Demo Selection - show when no query selected yet */}
      {demoStep === 'intro' && !selectedDemoQuery && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800/50 rounded-xl p-6 border border-slate-700"
        >
          <div className="text-center mb-6">
            <Zap className="w-12 h-12 text-primary mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">Choose a Demo Scenario</h3>
            <p className="text-gray-400">
              Each scenario highlights different search strengths
            </p>
          </div>
          
          <div className="space-y-3">
            {/* Keyword Demo - Lexical shines */}
            <button
              onClick={() => onRunDemo('keyword')}
              className="w-full text-left bg-amber-950/30 hover:bg-amber-900/40 border border-amber-700/50 hover:border-amber-600 rounded-xl p-4 transition-all group"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{DEMO_QUERIES.keyword.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-white">{DEMO_QUERIES.keyword.label}</span>
                    <span className="text-xs bg-amber-900/50 text-amber-300 px-2 py-0.5 rounded-full">{DEMO_QUERIES.keyword.winner}</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-1 truncate">"{DEMO_QUERIES.keyword.query}"</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-amber-400 transition-colors flex-shrink-0" />
              </div>
            </button>

            {/* Semantic Demo - Hybrid shines */}
            <button
              onClick={() => onRunDemo('semantic')}
              className="w-full text-left bg-cyan-950/30 hover:bg-cyan-900/40 border border-cyan-700/50 hover:border-cyan-600 rounded-xl p-4 transition-all group"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{DEMO_QUERIES.semantic.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-white">{DEMO_QUERIES.semantic.label}</span>
                    <span className="text-xs bg-cyan-900/50 text-cyan-300 px-2 py-0.5 rounded-full">{DEMO_QUERIES.semantic.winner}</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-1 truncate">"{DEMO_QUERIES.semantic.query}"</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-cyan-400 transition-colors flex-shrink-0" />
              </div>
            </button>

            {/* Use Case Demo - Agent shines */}
            <button
              onClick={() => onRunDemo('usecase')}
              className="w-full text-left bg-primary/10 hover:bg-primary/20 border border-primary/30 hover:border-primary/50 rounded-xl p-4 transition-all group"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{DEMO_QUERIES.usecase.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-white">{DEMO_QUERIES.usecase.label}</span>
                    <span className="text-xs bg-primary/30 text-primary px-2 py-0.5 rounded-full">{DEMO_QUERIES.usecase.winner}</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-1 truncate">"{DEMO_QUERIES.usecase.query}"</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors flex-shrink-0" />
              </div>
            </button>
          </div>
          
          <div className="mt-6 pt-4 border-t border-slate-700">
            <p className="text-xs text-gray-500 text-center mb-3">
              Each demo runs: Lexical → Hybrid → Agentic search
            </p>
            <ul className="text-xs text-gray-400 space-y-1">
              <li className="flex items-center gap-2"><BookOpen className="w-3 h-3 text-amber-400" /> <strong>Lexical:</strong> BM25 keyword matching</li>
              <li className="flex items-center gap-2"><Search className="w-3 h-3 text-cyan-400" /> <strong>Hybrid:</strong> Semantic + BM25 combined</li>
              <li className="flex items-center gap-2"><MessageSquare className="w-3 h-3 text-primary" /> <strong>Agentic:</strong> AI reasoning with tools</li>
            </ul>
          </div>
        </motion.div>
      )}

      {/* Lexical Search Results */}
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
                    onClick={() => onToggleQueryExpanded('lexical')}
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
                        onClick={() => onProductClick(product)}
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

      {/* Hybrid Search Results */}
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
                    onClick={() => onToggleQueryExpanded('hybrid')}
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
                        onClick={() => onProductClick(product)}
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

      {/* Agentic Search Results */}
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
                    onClick={() => onToggleStepsExpanded('demo')}
                    className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300"
                  >
                    {stepsExpanded['demo'] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    <span>Thought Trace ({demoAgenticMessage.steps.filter(s => s.reasoning || s.tool_id).length} steps)</span>
                  </button>
                  {stepsExpanded['demo'] && (
                    <div className="space-y-1 mt-2">
                      {demoAgenticMessage.steps
                        .filter(step => step.reasoning || (step.tool_id && step.params))
                        .map((step, idx) => (
                          <StepRenderer
                            key={idx}
                            step={step}
                            index={idx}
                            messageId="demo"
                            isExpanded={expandedSteps.has(`demo-${idx}`)}
                            onToggle={onToggleStep}
                          />
                        ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* Product Cards with Intro Text */}
              {demoAgenticProducts.length > 0 && (
                <div className="space-y-3">
                  {/* Intro text extracted from agent response */}
                  {demoAgenticMessage.content && (
                    <p className="text-sm text-gray-300">
                      {/* Extract first sentence/intro before product listings */}
                      {demoAgenticMessage.content.split(/\n\n|\*\*[A-Z]/)[0].replace(/[*#]/g, '').trim()}
                    </p>
                  )}
                  
                  <div className="text-xs font-semibold text-primary/70 uppercase tracking-wide">Recommended Products</div>
                  <div className="grid gap-2">
                    {demoAgenticProducts.map((product) => (
                      <div
                        key={product.id}
                        className="flex gap-3 bg-slate-800/80 rounded-lg p-3 border border-primary/20 hover:border-primary/40 transition-colors"
                      >
                        {/* Product Image */}
                        <div className="flex-shrink-0 w-14 h-14 bg-slate-700 rounded-lg overflow-hidden">
                          {product.image_url ? (
                            <img
                              src={product.image_url}
                              alt={product.title}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = FALLBACK_PRODUCT_IMAGE
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-500">
                              <ShoppingCart className="w-5 h-5" />
                            </div>
                          )}
                        </div>
                        
                        {/* Product Info with Description */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <h5 
                                className="font-medium text-white text-sm cursor-pointer hover:text-primary transition-colors"
                                onClick={() => onProductClick(product)}
                              >
                                {product.title}
                              </h5>
                              <p className="text-xs text-primary font-medium">${product.price?.toFixed(2)}</p>
                            </div>
                            {/* Add to Cart Button */}
                            <button
                              onClick={() => onAddToCart(product)}
                              disabled={addingToCart === product.id || justAddedToCart === product.id}
                              className={`flex-shrink-0 flex items-center gap-1 px-2 py-1 text-white text-xs font-medium rounded transition-all duration-300 ${
                                justAddedToCart === product.id 
                                  ? 'bg-green-500 scale-110 animate-pulse' 
                                  : 'bg-primary hover:bg-primary-dark disabled:opacity-50'
                              }`}
                            >
                              {addingToCart === product.id ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : justAddedToCart === product.id ? (
                                <Check className="w-3 h-3" />
                              ) : (
                                <Plus className="w-3 h-3" />
                              )}
                              <span>{justAddedToCart === product.id ? 'Added!' : 'Add'}</span>
                            </button>
                          </div>
                          {/* Product Description - truncated to 2 lines */}
                          {product.description && (
                            <p className="text-xs text-gray-400 mt-1 line-clamp-2">{product.description}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Response Text - only show if NO products (fallback) */}
              {demoAgenticMessage.content && demoAgenticProducts.length === 0 && (
                <div className="bg-slate-800/50 rounded-lg p-3">
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

      {/* Advance Demo Button */}
      {demoStep !== 'intro' && demoStep !== 'complete' && (
        <div className="flex justify-center">
          <button
            onClick={onAdvanceDemo}
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

      {/* Demo Complete */}
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
          <div className="flex gap-3 justify-center">
            <button
              onClick={onExitDemo}
              className="bg-white/10 hover:bg-white/20 text-white px-6 py-2 rounded-lg transition-colors"
            >
              ← Try Another Demo
            </button>
            <button
              onClick={onStartChat}
              className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-lg transition-colors"
            >
              Start Chatting →
            </button>
          </div>
        </motion.div>
      )}
    </div>
  )
}

