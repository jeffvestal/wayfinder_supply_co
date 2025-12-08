import { Product, UserId } from '../types'
import { api } from '../lib/api'
import { X, ShoppingCart, Tag, Package, Star } from 'lucide-react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface ProductDetailModalProps {
  product: Product | null
  userId: UserId
  onClose: () => void
  onTagClick?: (productName: string, tag: string) => void
}

export function ProductDetailModal({ product, userId, onClose, onTagClick }: ProductDetailModalProps) {
  const [adding, setAdding] = useState(false)
  const [quantity, setQuantity] = useState(1)

  if (!product) return null

  const handleAddToCart = async () => {
    try {
      setAdding(true)
      await api.addToCart(userId, product.id, quantity)
      onClose()
    } catch (err) {
      console.error('Failed to add to cart:', err)
    } finally {
      setAdding(false)
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" />
        
        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: 'spring', duration: 0.5 }}
          className="relative bg-slate-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-slate-700"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 rounded-full bg-slate-800/80 hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5 text-gray-300" />
          </button>

          <div className="flex flex-col md:flex-row">
            {/* Image Section */}
            <div className="md:w-1/2 bg-slate-800">
              <div className="aspect-square">
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect fill="%231e293b" width="400" height="400"/><text fill="%2364748b" font-family="sans-serif" font-size="18" x="50%25" y="50%25" text-anchor="middle" dy=".3em">No Image</text></svg>'
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-500">
                    <Package className="w-24 h-24" />
                  </div>
                )}
              </div>
            </div>

            {/* Details Section */}
            <div className="md:w-1/2 p-8 overflow-y-auto max-h-[60vh] md:max-h-[90vh]">
              {/* Brand & Category */}
              <div className="flex items-center gap-2 mb-2">
                <span className="text-primary font-medium">{product.brand}</span>
                <span className="text-gray-500">•</span>
                <span className="text-gray-400 capitalize">{product.category}</span>
              </div>

              {/* Title */}
              <h2 className="text-3xl font-display font-bold text-white mb-4">
                {product.title}
              </h2>

              {/* Price */}
              <div className="flex items-baseline gap-2 mb-6">
                <span className="text-4xl font-display font-bold text-primary">
                  ${product.price.toFixed(2)}
                </span>
              </div>

              {/* Rating placeholder */}
              <div className="flex items-center gap-1 mb-6">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`w-5 h-5 ${star <= 4 ? 'text-amber-400 fill-amber-400' : 'text-gray-600'}`}
                  />
                ))}
                <span className="text-gray-400 ml-2">(24 reviews)</span>
              </div>

              {/* Description */}
              <p className="text-gray-300 leading-relaxed mb-6">
                {product.description}
              </p>

              {/* Tags */}
              <div className="mb-8">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Features
                  {onTagClick && <span className="text-xs text-gray-500 font-normal ml-2">(click to explore)</span>}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {product.tags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => onTagClick?.(product.title, tag)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 text-gray-300 rounded-full text-sm font-medium border border-slate-700 transition-all ${
                        onTagClick 
                          ? 'hover:bg-primary/20 hover:border-primary/50 hover:text-primary cursor-pointer' 
                          : ''
                      }`}
                    >
                      <Tag className="w-3.5 h-3.5 text-primary" />
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quantity & Add to Cart */}
              <div className="flex items-center gap-4">
                <div className="flex items-center bg-slate-800 rounded-xl border border-slate-700">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="px-4 py-3 text-gray-300 hover:text-white transition-colors"
                  >
                    -
                  </button>
                  <span className="px-4 py-3 text-white font-medium min-w-[3rem] text-center">
                    {quantity}
                  </span>
                  <button
                    onClick={() => setQuantity(quantity + 1)}
                    className="px-4 py-3 text-gray-300 hover:text-white transition-colors"
                  >
                    +
                  </button>
                </div>
                <button
                  onClick={handleAddToCart}
                  disabled={adding}
                  className="flex-1 bg-primary hover:bg-primary-dark text-white font-semibold py-4 px-6 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-primary/20 hover:shadow-primary/40"
                >
                  <ShoppingCart className="w-5 h-5" />
                  {adding ? 'Adding...' : 'Add to Cart'}
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

