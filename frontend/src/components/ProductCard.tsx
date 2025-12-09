import { Product, UserId } from '../types'
import { api } from '../lib/api'
import { ShoppingCart, Tag, Star } from 'lucide-react'
import { useState } from 'react'
import { motion } from 'framer-motion'

interface ProductCardProps {
  product: Product
  userId: UserId
  onClick?: () => void
}

export function ProductCard({ product, userId, onClick }: ProductCardProps) {
  const [adding, setAdding] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.stopPropagation() // Prevent card click
    try {
      setAdding(true)
      await api.addToCart(userId, product.id, 1)
      
      // Track add to cart event for guest user
      if (userId === 'user_new') {
        api.trackEvent(userId, 'add_to_cart', product.id)
      }
    } catch (err) {
      console.error('Failed to add to cart:', err)
    } finally {
      setAdding(false)
    }
  }

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't track if clicking on the Add to Cart button or any button
    const target = e.target as HTMLElement
    if (target.closest('button')) {
      return
    }
    
    // Track view event for guest user
    if (userId === 'user_new') {
      api.trackEvent(userId, 'view_item', product.id)
    }
    
    // Call original onClick handler if provided
    onClick?.()
  }

  return (
    <motion.div
      whileHover={{ y: -4 }}
      onClick={(e) => handleCardClick(e)}
      className="bg-slate-800/50 backdrop-blur-sm rounded-2xl overflow-hidden border border-slate-700 hover:border-primary/50 shadow-lg hover:shadow-primary/10 transition-all duration-300 group cursor-pointer"
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
            <p className="text-sm text-gray-400 font-medium mb-1">{product.brand}</p>
            {product.average_rating && product.review_count && (
              <div className="flex items-center gap-1.5">
                <div className="flex items-center gap-0.5">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={star}
                      className={`w-3 h-3 ${
                        star <= Math.round(product.average_rating!)
                          ? 'text-amber-400 fill-amber-400'
                          : 'text-gray-600'
                      }`}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-500">
                  {product.average_rating.toFixed(1)} ({product.review_count} reviews)
                </span>
              </div>
            )}
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
          onClick={(e) => handleAddToCart(e)}
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

