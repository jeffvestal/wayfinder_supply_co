import { useState, useEffect } from 'react'
import { Cart, UserId } from '../types'
import { api } from '../lib/api'
import { Loader2, Star, CheckCircle2, ShoppingBag } from 'lucide-react'
import { motion } from 'framer-motion'

interface OrderConfirmationProps {
  userId: UserId
  orderId: string
  confirmationNumber: string
  onContinueShopping: () => void
}

interface ReviewForm {
  rating: number
  title: string
  text: string
}

export function OrderConfirmation({ userId, confirmationNumber, onContinueShopping }: OrderConfirmationProps) {
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [reviews, setReviews] = useState<Record<string, ReviewForm>>({})
  const [submitting, setSubmitting] = useState<Set<string>>(new Set())

  useEffect(() => {
    // Get cart items from the order (simplified - in production would fetch from order)
    loadCart()
  }, [])

  const loadCart = async () => {
    try {
      const data = await api.getCart(userId)
      setCart(data)
    } catch (err) {
      console.error('Failed to load cart:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleReviewChange = (productId: string, field: keyof ReviewForm, value: string | number) => {
    setReviews(prev => ({
      ...prev,
      [productId]: {
        ...prev[productId],
        [field]: value,
      } as ReviewForm
    }))
  }

  const handleSubmitReview = async (productId: string) => {
    const review = reviews[productId]
    if (!review || !review.title || !review.text || review.rating === 0) {
      alert('Please fill in all review fields')
      return
    }

    setSubmitting(prev => new Set(prev).add(productId))
    try {
      await api.submitReview(productId, userId, review.rating, review.title, review.text)
      // Remove review form after submission
      setReviews(prev => {
        const next = { ...prev }
        delete next[productId]
        return next
      })
    } catch (err) {
      console.error('Failed to submit review:', err)
      alert('Failed to submit review. Please try again.')
    } finally {
      setSubmitting(prev => {
        const next = new Set(prev)
        next.delete(productId)
        return next
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Success Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center">
          <CheckCircle2 className="w-12 h-12 text-green-400" />
        </div>
        <h1 className="text-4xl font-display font-bold text-white mb-4">Order Confirmed!</h1>
        <p className="text-gray-400 text-lg">
          Your order has been placed successfully
        </p>
        <div className="mt-6 bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700 inline-block">
          <p className="text-sm text-gray-400 mb-2">Order Number</p>
          <p className="text-2xl font-display font-bold text-primary">{confirmationNumber}</p>
        </div>
      </motion.div>

      {/* Order Items */}
      {cart && cart.items.length > 0 && (
        <div className="space-y-6 mb-12">
          <h2 className="text-2xl font-display font-bold text-white mb-6">Order Items</h2>
          {cart.items.map((item) => {
            const review = reviews[item.product_id] || { rating: 0, title: '', text: '' }
            const hasReview = reviews[item.product_id] !== undefined

            return (
              <motion.div
                key={item.product_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700"
              >
                <div className="flex items-start gap-4 mb-6">
                  <img
                    src={item.image_url || '/placeholder.png'}
                    alt={item.title}
                    className="w-24 h-24 object-cover rounded-lg"
                  />
                  <div className="flex-1">
                    <h3 className="text-xl font-display font-semibold text-white mb-1">{item.title}</h3>
                    <p className="text-gray-400">Quantity: {item.quantity}</p>
                    <p className="text-lg font-semibold text-primary mt-2">${item.subtotal.toFixed(2)}</p>
                  </div>
                </div>

                {/* Review Form */}
                {!hasReview ? (
                  <div className="border-t border-slate-700 pt-6">
                    <h3 className="text-lg font-display font-semibold text-white mb-4">Write a Review</h3>
                    
                    {/* Star Rating */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-300 mb-2">Rating</label>
                      <div className="flex items-center gap-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            onClick={() => handleReviewChange(item.product_id, 'rating', star)}
                            className="transition-transform hover:scale-110"
                          >
                            <Star
                              className={`w-6 h-6 ${
                                star <= review.rating
                                  ? 'text-amber-400 fill-amber-400'
                                  : 'text-gray-600'
                              }`}
                            />
                          </button>
                        ))}
                        {review.rating > 0 && (
                          <span className="text-sm text-gray-400 ml-2">{review.rating} stars</span>
                        )}
                      </div>
                    </div>

                    {/* Review Title */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-300 mb-2">Review Title</label>
                      <input
                        type="text"
                        value={review.title}
                        onChange={(e) => handleReviewChange(item.product_id, 'title', e.target.value)}
                        placeholder="Summarize your experience"
                        className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>

                    {/* Review Text */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-300 mb-2">Your Review</label>
                      <textarea
                        value={review.text}
                        onChange={(e) => handleReviewChange(item.product_id, 'text', e.target.value)}
                        placeholder="Share your thoughts about this product..."
                        rows={4}
                        className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                      />
                    </div>

                    {/* Submit Button */}
                    <button
                      onClick={() => handleSubmitReview(item.product_id)}
                      disabled={submitting.has(item.product_id) || !review.title || !review.text || review.rating === 0}
                      className="bg-primary hover:bg-primary-dark text-white font-semibold py-3 px-6 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {submitting.has(item.product_id) ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Submitting...
                        </>
                      ) : (
                        'Submit Review'
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="border-t border-slate-700 pt-6">
                    <div className="flex items-center gap-2 text-green-400">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-medium">Review submitted!</span>
                    </div>
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Continue Shopping */}
      <div className="text-center">
        <button
          onClick={onContinueShopping}
          className="bg-primary hover:bg-primary-dark text-white font-semibold py-4 px-8 rounded-xl transition-all shadow-lg shadow-primary/20 hover:shadow-primary/40 flex items-center gap-2 mx-auto"
        >
          <ShoppingBag className="w-5 h-5" />
          Continue Shopping
        </button>
      </div>
    </div>
  )
}

