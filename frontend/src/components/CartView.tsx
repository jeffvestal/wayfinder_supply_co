import { useEffect, useState } from 'react'
import { Cart, UserId } from '../types'
import { api } from '../lib/api'
import { Loader2, Trash2, ShoppingBag, Sparkles } from 'lucide-react'

interface CartViewProps {
  userId: UserId
  loyaltyTier: string
}

// Import actual generated products for demo cart
import generatedProducts from '../../../generated_products/products.json'

// Mock cart using real product data
const MOCK_CART: Cart = {
  items: generatedProducts.slice(0, 2).map((p: any) => ({
    product_id: p.id,
    title: p.title,
    price: p.price,
    quantity: 1,
    subtotal: p.price,
    image_url: p.image_url
  })),
  subtotal: generatedProducts.slice(0, 2).reduce((sum: number, p: any) => sum + p.price, 0),
  discount: 0,
  total: generatedProducts.slice(0, 2).reduce((sum: number, p: any) => sum + p.price, 0),
  loyalty_perks: []
}

const MOCK_CART_PLATINUM: Cart = {
  ...MOCK_CART,
  discount: Math.round(MOCK_CART.subtotal * 0.1 * 100) / 100,
  total: Math.round(MOCK_CART.subtotal * 0.9 * 100) / 100,
  loyalty_perks: ['10% member discount applied', 'Free expedited shipping', `Bonus reward points: ${Math.floor(MOCK_CART.subtotal * 0.9)}`]
}

export function CartView({ userId, loyaltyTier }: CartViewProps) {
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [usingMockData, setUsingMockData] = useState(false)

  useEffect(() => {
    loadCart()
  }, [userId, loyaltyTier])

  const loadCart = async () => {
    try {
      setLoading(true)
      const data = await api.getCart(userId, loyaltyTier)
      setCart(data)
      setUsingMockData(false)
    } catch (err) {
      console.warn('Backend unavailable, using mock cart')
      // Use mock data based on loyalty tier
      const mockCart = loyaltyTier === 'platinum' ? MOCK_CART_PLATINUM : MOCK_CART
      setCart(mockCart)
      setUsingMockData(true)
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveItem = async (productId: string) => {
    try {
      await api.removeFromCart(userId, productId)
      await loadCart()
    } catch (err) {
      console.error('Failed to remove item:', err)
    }
  }

  const handleClearCart = async () => {
    try {
      await api.clearCart(userId)
      await loadCart()
    } catch (err) {
      console.error('Failed to clear cart:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-12 text-center">
        <ShoppingBag className="w-20 h-20 text-slate-300 mx-auto mb-4" />
        <h3 className="text-2xl font-display font-bold text-slate-900 mb-2">Your cart is empty</h3>
        <p className="text-slate-600">Add some products to get started on your adventure!</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary/10 to-primary/5 border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-3xl font-display font-bold text-slate-900">Shopping Cart</h2>
              {usingMockData && (
                <span className="bg-amber-100 text-amber-800 text-xs font-medium px-3 py-1 rounded-full">
                  Demo Mode
                </span>
              )}
            </div>
            <button
              onClick={handleClearCart}
              className="text-sm text-red-600 hover:text-red-700 font-medium transition-colors"
            >
              Clear Cart
            </button>
          </div>
        </div>

        <div className="p-8">
          {/* Loyalty Perks */}
          {cart.loyalty_perks.length > 0 && (
            <div className="bg-gradient-to-r from-primary/20 to-primary/10 border-2 border-primary/30 rounded-xl p-5 mb-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-display font-bold text-lg text-primary">Loyalty Perks</h3>
              </div>
              <ul className="space-y-2">
                {cart.loyalty_perks.map((perk, index) => (
                  <li key={index} className="flex items-center gap-2 text-slate-700">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                    <span className="text-sm">{perk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Cart Items */}
          <div className="space-y-4 mb-8">
            {cart.items.map((item) => (
              <div
                key={item.product_id}
                className="flex items-center gap-6 bg-slate-50 rounded-xl p-5 border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <img
                  src={item.image_url || '/placeholder.png'}
                  alt={item.title}
                  className="w-24 h-24 object-cover rounded-lg shadow-md"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect fill="%23f1f5f9" width="96" height="96"/></svg>'
                  }}
                />
                <div className="flex-1">
                  <h3 className="font-display font-semibold text-lg text-slate-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-slate-600">
                    ${item.price.toFixed(2)} × {item.quantity}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xl font-display font-bold text-slate-900">${item.subtotal.toFixed(2)}</p>
                </div>
                <button
                  onClick={() => handleRemoveItem(item.product_id)}
                  className="text-red-500 hover:text-red-600 p-2 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="border-t-2 border-slate-200 pt-6 space-y-3">
            <div className="flex justify-between text-slate-600">
              <span className="font-medium">Subtotal</span>
              <span className="font-semibold">${cart.subtotal.toFixed(2)}</span>
            </div>
            {cart.discount > 0 && (
              <div className="flex justify-between text-green-600">
                <span className="font-medium">Discount</span>
                <span className="font-semibold">-${cart.discount.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-2xl font-display font-bold pt-3 border-t-2 border-slate-200">
              <span className="text-slate-900">Total</span>
              <span className="text-gradient">${cart.total.toFixed(2)}</span>
            </div>
            <button className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-lg shadow-primary/20 hover:shadow-primary/40 hover:scale-[1.02] mt-6">
              Proceed to Checkout
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


