import { motion } from 'framer-motion'
import { Product } from '../../types'
import { Search, Loader2 } from 'lucide-react'
import { SearchMode as SearchModeType } from './types'

interface SearchModeProps {
  mode: 'lexical' | 'hybrid'
  results: Product[]
  isLoading: boolean
  onProductClick: (product: Product) => void
}

export function SearchMode({ mode, results, isLoading, onProductClick }: SearchModeProps) {
  // Empty state
  if (results.length === 0 && !isLoading) {
    return (
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
    )
  }

  return (
    <div className="space-y-4">
      {/* Results */}
      {results.map((product) => (
        <motion.div
          key={product.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-xl p-4 border cursor-pointer transition-all ${
            mode === 'hybrid' 
              ? 'bg-cyan-950/30 border-cyan-700/50 hover:border-cyan-500' 
              : 'bg-amber-950/30 border-amber-700/50 hover:border-amber-500'
          }`}
          onClick={() => onProductClick(product)}
        >
          <h3 className="text-lg font-semibold text-white mb-1">{product.title}</h3>
          <p className="text-sm text-gray-300 mb-2">${product.price?.toFixed(2)}</p>
          {product.description && (
            <p className="text-sm text-gray-400 line-clamp-2">{product.description}</p>
          )}
        </motion.div>
      ))}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
          <span className="ml-3 text-gray-400">Searching...</span>
        </div>
      )}
    </div>
  )
}

