import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Product } from '../types'
import { api } from '../lib/api'
import { ProductCard } from './ProductCard'
import { Loader2, X, BookOpen, Search, MessageSquare } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface SearchComparisonDemoProps {
  onClose: () => void
  userId: string
}

export function SearchComparisonDemo({ onClose, userId }: SearchComparisonDemoProps) {
  const [lexicalResults, setLexicalResults] = useState<Product[]>([])
  const [hybridResults, setHybridResults] = useState<Product[]>([])
  const [agenticMessage, setAgenticMessage] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const query = 'gear to keep my feet dry on slippery mountain trails'

  useEffect(() => {
    const runComparison = async () => {
      setIsLoading(true)
      try {
        // Run lexical and hybrid searches
        const [lexical, hybrid] = await Promise.all([
          api.lexicalSearch(query, 10, undefined),
          api.hybridSearch(query, 10, undefined)
        ])
        
        // Run agentic search separately (streaming)
        let agenticMessage = ''
        await api.streamChat(query, 'user_new', (event) => {
          if (event.type === 'message_chunk') {
            agenticMessage += event.data.text_chunk || ''
          } else if (event.type === 'message_complete' || event.type === 'completion') {
            agenticMessage = event.data.message_content || agenticMessage
          }
        })
        
        setLexicalResults(lexical.products)
        setHybridResults(hybrid.products)
        setAgenticMessage(agenticMessage)
      } catch (error) {
        console.error('Search comparison demo failed:', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    runComparison()
  }, [])

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
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Lexical Search */}
              <div className="bg-amber-950/20 border border-amber-700/30 rounded-lg p-4">
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
                  ) : (
                    <p className="text-gray-500 text-sm">No results</p>
                  )}
                </div>
              </div>

              {/* Hybrid Search */}
              <div className="bg-cyan-950/20 border border-cyan-700/30 rounded-lg p-4">
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
                  ) : (
                    <p className="text-gray-500 text-sm">No results</p>
                  )}
                </div>
              </div>

              {/* Agentic Search */}
              <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
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
                <div className="bg-slate-800/50 rounded-lg p-4 text-sm text-gray-300">
                  {agenticMessage ? (
                    <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                      {agenticMessage}
                    </ReactMarkdown>
                  ) : (
                    <p className="text-gray-500">No response</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}

