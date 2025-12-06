import { Product, UserId } from '../types'
import { api } from '../lib/api'
import { ShoppingCart, Tag } from 'lucide-react'
import { useState } from 'react'
import { motion } from 'framer-motion'

interface ProductCardProps {
  product: Product
  userId: UserId
}

export function ProductCard({ product, userId }: ProductCardProps) {
  const [adding, setAdding] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)

  const handleAddToCart = async () => {
    try {
      setAdding(true)
      await api.addToCart(userId, product.id, 1)
      // Could show a toast notification here
    } catch (err) {
      console.error('Failed to add to cart:', err)
    } finally {
      setAdding(false)
    }
  }

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="bg-slate-800/50 backdrop-blur-sm rounded-2xl overflow-hidden border border-slate-700 hover:border-primary/50 shadow-lg hover:shadow-primary/10 transition-all duration-300 group"
    >
      <div className="aspect-square bg-slate-800 overflow-hidden relative">
        {product.image_url ? (
          <>
            <img
              src={product.image_url}
              alt={product.title}
              className={`w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              onLoad={() => setImageLoaded(true)}
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect fill="%231e293b" width="400" height="400"/><text fill="%2364748b" font-family="sans-serif" font-size="18" x="50%25" y="50%25" text-anchor="middle" dy=".3em">No Image</text></svg>'
                setImageLoaded(true)
              }}
            />
            {!imageLoaded && (
              <div className="absolute inset-0 bg-slate-700 animate-pulse" />
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-500">
            No Image
          </div>
        )}
      </div>
      <div className="p-5">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-display font-bold text-lg text-white mb-1 line-clamp-1">
              {product.title}
            </h3>
            <p className="text-sm text-gray-400 font-medium">{product.brand}</p>
          </div>
          <div className="text-2xl font-display font-bold text-primary ml-3">
            ${product.price.toFixed(2)}
          </div>
        </div>
        <p className="text-sm text-gray-300 mb-4 line-clamp-2 leading-relaxed">
          {product.description}
        </p>
        <div className="flex flex-wrap gap-1.5 mb-4">
          {product.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-700 text-gray-300 rounded-full text-xs font-medium"
            >
              <Tag className="w-3 h-3" />
              {tag}
            </span>
          ))}
        </div>
        <button
          onClick={handleAddToCart}
          disabled={adding}
          className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 px-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-primary/20 hover:shadow-primary/40 hover:scale-[1.02]"
        >
          <ShoppingCart className="w-4 h-4" />
          {adding ? 'Adding...' : 'Add to Cart'}
        </button>
      </div>
    </motion.div>
  )
}


