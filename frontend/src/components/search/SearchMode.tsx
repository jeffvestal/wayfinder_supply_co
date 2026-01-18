import { motion } from 'framer-motion'
import { Product } from '../../types'
import { Search, Loader2 } from 'lucide-react'

const FALLBACK_IMAGE = "data:image/svg+xml,%3Csvg%20xmlns%3D'http%3A//www.w3.org/2000/svg'%20width%3D'100'%20height%3D'100'%20viewBox%3D'0%200%20100%20100'%3E%3Crect%20width%3D'100'%20height%3D'100'%20fill%3D'%231f2937'/%3E%3Cpath%20d%3D'M35%2040h30l-3%2030H38z'%20fill%3D'%23374151'/%3E%3Cpath%20d%3D'M42.5%2040c0-4%203-7%207.5-7s7.5%203%207.5%207'%20fill%3D'none'%20stroke%3D'%234b5563'%20stroke-width%3D'4'%20stroke-linecap%3D'round'/%3E%3C/svg%3E"

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
    <div className="space-y-3">
      {/* Results */}
      {results.map((product) => (
        <motion.div
          key={product.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-xl border cursor-pointer transition-all flex gap-3 p-3 ${
            mode === 'hybrid' 
              ? 'bg-cyan-950/20 border-cyan-700/40 hover:border-cyan-500 hover:bg-cyan-950/30' 
              : 'bg-amber-950/20 border-amber-700/40 hover:border-amber-500 hover:bg-amber-950/30'
          }`}
          onClick={() => onProductClick(product)}
        >
          {/* Product Image - Small Thumbnail */}
          <div className="flex-shrink-0">
            <img
              src={product.image_url || FALLBACK_IMAGE}
              alt={product.title}
              className="w-20 h-20 object-cover rounded-lg bg-slate-800"
              onError={(e) => {
                e.currentTarget.src = FALLBACK_IMAGE
              }}
            />
          </div>
          
          {/* Product Info */}
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-white mb-1 line-clamp-1">{product.title}</h3>
            <p className={`text-base font-bold mb-1 ${
              mode === 'hybrid' ? 'text-cyan-400' : 'text-amber-400'
            }`}>
              ${product.price?.toFixed(2)}
            </p>
            {product.description && (
              <p className="text-xs text-gray-400 line-clamp-2">{product.description}</p>
            )}
          </div>
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

