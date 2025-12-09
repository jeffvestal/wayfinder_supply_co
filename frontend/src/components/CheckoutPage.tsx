import { useState, useEffect } from 'react'
import { Cart, UserId } from '../types'
import { api } from '../lib/api'
import { Loader2, CreditCard, MapPin, ArrowLeft } from 'lucide-react'

interface CheckoutPageProps {
  userId: UserId
  loyaltyTier: string
  onBack: () => void
  onOrderComplete: (orderId: string, confirmationNumber: string) => void
}

// Auto-populated fake data
const DEFAULT_SHIPPING = {
  name: 'Jordan Explorer',
  address: '123 Adventure Way',
  city: 'Denver',
  state: 'CO',
  zip: '80202',
  country: 'United States'
}

const DEFAULT_PAYMENT = {
  card_number: '4532-1234-5678-9010',
  card_type: 'Visa',
  expiry_month: '12',
  expiry_year: '2025',
  cvv: '123',
  name_on_card: 'Jordan Explorer'
}

export function CheckoutPage({ userId, loyaltyTier, onBack, onOrderComplete }: CheckoutPageProps) {
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [placingOrder, setPlacingOrder] = useState(false)
  const [shipping, setShipping] = useState(DEFAULT_SHIPPING)
  const [payment, setPayment] = useState(DEFAULT_PAYMENT)

  useEffect(() => {
    loadCart()
  }, [userId, loyaltyTier])

  const loadCart = async () => {
    try {
      setLoading(true)
      const data = await api.getCart(userId, loyaltyTier)
      setCart(data)
    } catch (err) {
      console.error('Failed to load cart:', err)
      onBack()
    } finally {
      setLoading(false)
    }
  }

  const handlePlaceOrder = async () => {
    if (!cart || cart.items.length === 0) return

    try {
      setPlacingOrder(true)
      const order = await api.createOrder(userId, shipping, payment)
      onOrderComplete(order.order_id, order.confirmation_number)
    } catch (err) {
      console.error('Failed to place order:', err)
      alert('Failed to place order. Please try again.')
    } finally {
      setPlacingOrder(false)
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
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-12 text-center">
          <h3 className="text-2xl font-display font-bold text-slate-900 mb-2">Your cart is empty</h3>
          <p className="text-slate-600 mb-4">Add some products to checkout!</p>
          <button
            onClick={onBack}
            className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl transition-all"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Cart
      </button>

      <h1 className="text-4xl font-display font-bold text-white mb-8">Checkout</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Shipping Address */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <MapPin className="w-5 h-5 text-primary" />
              </div>
              <h2 className="text-2xl font-display font-bold text-white">Shipping Address</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
                <input
                  type="text"
                  value={shipping.name}
                  onChange={(e) => setShipping({ ...shipping, name: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">Address</label>
                <input
                  type="text"
                  value={shipping.address}
                  onChange={(e) => setShipping({ ...shipping, address: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">City</label>
                <input
                  type="text"
                  value={shipping.city}
                  onChange={(e) => setShipping({ ...shipping, city: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">State</label>
                <input
                  type="text"
                  value={shipping.state}
                  onChange={(e) => setShipping({ ...shipping, state: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">ZIP Code</label>
                <input
                  type="text"
                  value={shipping.zip}
                  onChange={(e) => setShipping({ ...shipping, zip: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Country</label>
                <input
                  type="text"
                  value={shipping.country}
                  onChange={(e) => setShipping({ ...shipping, country: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          </div>

          {/* Payment Information */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <CreditCard className="w-5 h-5 text-primary" />
              </div>
              <h2 className="text-2xl font-display font-bold text-white">Payment Information</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">Card Number</label>
                <input
                  type="text"
                  value={payment.card_number}
                  onChange={(e) => setPayment({ ...payment, card_number: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">Name on Card</label>
                <input
                  type="text"
                  value={payment.name_on_card}
                  onChange={(e) => setPayment({ ...payment, name_on_card: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Expiry Month</label>
                <input
                  type="text"
                  value={payment.expiry_month}
                  onChange={(e) => setPayment({ ...payment, expiry_month: e.target.value })}
                  placeholder="MM"
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Expiry Year</label>
                <input
                  type="text"
                  value={payment.expiry_year}
                  onChange={(e) => setPayment({ ...payment, expiry_year: e.target.value })}
                  placeholder="YYYY"
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">CVV</label>
                <input
                  type="text"
                  value={payment.cvv}
                  onChange={(e) => setPayment({ ...payment, cvv: e.target.value })}
                  placeholder="123"
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700 sticky top-24">
            <h2 className="text-2xl font-display font-bold text-white mb-6">Order Summary</h2>

            <div className="space-y-3 mb-6">
              {cart.items.map((item) => (
                <div key={item.product_id} className="flex items-center gap-3">
                  <img
                    src={item.image_url || '/placeholder.png'}
                    alt={item.title}
                    className="w-16 h-16 object-cover rounded-lg"
                  />
                  <div className="flex-1">
                    <p className="text-sm text-gray-300 line-clamp-1">{item.title}</p>
                    <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                  </div>
                  <p className="text-sm font-semibold text-white">${item.subtotal.toFixed(2)}</p>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-700 pt-4 space-y-2 mb-6">
              <div className="flex justify-between text-gray-300">
                <span>Subtotal</span>
                <span>${cart.subtotal.toFixed(2)}</span>
              </div>
              {cart.discount > 0 && (
                <div className="flex justify-between text-green-400">
                  <span>Discount</span>
                  <span>-${cart.discount.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-lg font-bold text-white pt-2 border-t border-slate-700">
                <span>Total</span>
                <span className="text-primary">${cart.total.toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={handlePlaceOrder}
              disabled={placingOrder}
              className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-4 px-6 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-primary/20 hover:shadow-primary/40"
            >
              {placingOrder ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                'Place Order'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

