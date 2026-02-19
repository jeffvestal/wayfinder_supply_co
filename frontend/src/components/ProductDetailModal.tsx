import { Product, UserId, Review } from '../types'
import { api } from '../lib/api'
import { X, ShoppingCart, Tag, Package, Star, ChevronDown, ChevronUp } from 'lucide-react'
import { useState, useEffect } from 'react'
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
  const [reviews, setReviews] = useState<Review[]>([])
  const [reviewsExpanded, setReviewsExpanded] = useState(false)
  const [loadingReviews, setLoadingReviews] = useState(false)

  useEffect(() => {
    if (product && product.review_count && product.review_count > 0) {
      loadReviews()
    }
  }, [product])

  const loadReviews = async () => {
    if (!product) return
    try {
      setLoadingReviews(true)
      const data = await api.getProductReviews(product.id, 10)
      setReviews(data.reviews.map((r: any) => ({
        ...r,
        timestamp: new Date(r.timestamp)
      })))
    } catch (err) {
      console.error('Failed to load reviews:', err)
    } finally {
      setLoadingReviews(false)
    }
  }

  if (!product) return null

  const averageRating = product.average_rating || 0
  const reviewCount = product.review_count || 0

  const handleAddToCart = async () => {
    try {
      setAdding(true)
      await api.addToCart(userId, product.id, quantity)
      
      // Track add to cart event for guest user
      if (userId === 'user_new') {
        api.trackEvent(userId, 'add_to_cart', product.id)
      }
      
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
              <div className="h-48 md:aspect-square md:h-auto">
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
            <div className="md:w-1/2 flex flex-col max-h-[60vh] md:max-h-[90vh]">
            <div className="flex-1 overflow-y-auto p-8 pb-4">
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

              {/* Rating */}
              {averageRating > 0 && reviewCount > 0 && (
                <button
                  onClick={() => setReviewsExpanded(!reviewsExpanded)}
                  className="flex items-center gap-1 mb-6 hover:opacity-80 transition-opacity cursor-pointer"
                >
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={star}
                      className={`w-5 h-5 ${
                        star <= Math.round(averageRating)
                          ? 'text-amber-400 fill-amber-400'
                          : 'text-gray-600'
                      }`}
                    />
                  ))}
                  <span className="text-gray-400 ml-2">
                    {averageRating.toFixed(1)} ({reviewCount} reviews)
                  </span>
                  {reviewsExpanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-400 ml-1" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400 ml-1" />
                  )}
                </button>
              )}

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
                      onClick={() => {
                        // Track tag click for guest user
                        if (userId === 'user_new') {
                          api.trackEvent(userId, 'click_tag', product.id, tag)
                        }
                        onTagClick?.(product.title, tag)
                      }}
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

              {/* Reviews Section */}
              <AnimatePresence>
                {reviewsExpanded && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mb-8 border-t border-slate-700 pt-6"
                  >
                    <h3 className="text-lg font-display font-semibold text-white mb-4">Customer Reviews</h3>
                    {loadingReviews ? (
                      <div className="text-gray-400">Loading reviews...</div>
                    ) : reviews.length === 0 ? (
                      <div className="text-gray-400">No reviews yet.</div>
                    ) : (
                      <div className="space-y-4 max-h-[300px] overflow-y-auto">
                        {reviews.map((review) => (
                          <div key={review.id} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                            <div className="flex items-center gap-2 mb-2">
                              <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <Star
                                    key={star}
                                    className={`w-3 h-3 ${
                                      star <= review.rating
                                        ? 'text-amber-400 fill-amber-400'
                                        : 'text-gray-600'
                                    }`}
                                  />
                                ))}
                              </div>
                              <span className="text-sm font-semibold text-white">{review.title}</span>
                              {review.verified_purchase && (
                                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                                  Verified Purchase
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-300 mb-2">{review.text}</p>
                            <p className="text-xs text-gray-500">
                              {review.user_id} • {review.timestamp.toLocaleDateString()}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

            </div>

              {/* Quantity & Add to Cart -- pinned at bottom */}
              <div className="flex items-center gap-4 p-4 md:px-8 border-t border-slate-700 bg-slate-900 shrink-0">
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
