import { useState, useEffect } from 'react'
import { Storefront } from './components/Storefront'
import { TripPlanner } from './components/TripPlanner'
import { CartView } from './components/CartView'
import { ChatModal } from './components/ChatModal'
import { UserSwitcher } from './components/UserSwitcher'
import { User, UserId } from './types'
import { ShoppingCart, MapPin, Home, MessageSquare, Menu, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const USERS: Record<UserId, User> = {
  user_new: {
    id: 'user_new',
    name: 'Jordan Explorer',
    loyalty_tier: 'none',
  },
  user_member: {
    id: 'user_member',
    name: 'Alex Hiker',
    loyalty_tier: 'platinum',
  },
  user_business: {
    id: 'user_business',
    name: 'Casey Campground',
    loyalty_tier: 'business',
  },
}

type View = 'storefront' | 'trip-planner' | 'cart'

function App() {
  const [currentUser, setCurrentUser] = useState<UserId>('user_new')
  const [currentView, setCurrentView] = useState<View>('storefront')
  const [chatModalOpen, setChatModalOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleNavigate = (e: CustomEvent) => {
      if (e.detail === 'trip-planner') {
        setCurrentView('trip-planner')
      }
    }
    window.addEventListener('navigate', handleNavigate as EventListener)
    return () => window.removeEventListener('navigate', handleNavigate as EventListener)
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header with glass morphism */}
      <header className="sticky top-0 z-50 glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-8">
              <h1 className="text-3xl font-display font-bold text-gradient">Wayfinder</h1>
              {/* Mobile Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 rounded-lg hover:bg-white/5 transition-colors"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6 text-white" />
                ) : (
                  <Menu className="w-6 h-6 text-white" />
                )}
              </button>
              <nav className="hidden lg:flex gap-1">
                <button
                  onClick={() => {
                    setCurrentView('storefront')
                    setMobileMenuOpen(false)
                  }}
                  className={`px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-all ${
                    currentView === 'storefront'
                      ? 'bg-primary/20 text-primary'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Home className="w-4 h-4" />
                  Store
                </button>
                <button
                  onClick={() => {
                    setCurrentView('trip-planner')
                    setMobileMenuOpen(false)
                  }}
                  className={`px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-all ${
                    currentView === 'trip-planner'
                      ? 'bg-primary/20 text-primary'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <MapPin className="w-4 h-4" />
                  Trip Planner
                </button>
                <button
                  onClick={() => {
                    setCurrentView('cart')
                    setMobileMenuOpen(false)
                  }}
                  className={`px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-all relative ${
                    currentView === 'cart'
                      ? 'bg-primary/20 text-primary'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <ShoppingCart className="w-4 h-4" />
                  Cart
                </button>
              </nav>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setChatModalOpen(true)}
                className="hidden lg:flex items-center gap-2 px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-lg transition-all border border-primary/30"
              >
                <MessageSquare className="w-4 h-4" />
                <span className="text-sm font-medium">Quick Chat</span>
              </button>
              <UserSwitcher
                currentUser={currentUser}
                users={USERS}
                onUserChange={setCurrentUser}
              />
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu - Inside header for proper stacking */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden border-t border-white/10 bg-slate-900/95 backdrop-blur-lg overflow-hidden"
            >
              <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col gap-2">
                <button
                  onClick={() => {
                    setCurrentView('storefront')
                    setMobileMenuOpen(false)
                  }}
                  className={`px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-all ${
                    currentView === 'storefront'
                      ? 'bg-primary/20 text-primary'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Home className="w-4 h-4" />
                  Store
                </button>
                <button
                  onClick={() => {
                    setCurrentView('trip-planner')
                    setMobileMenuOpen(false)
                  }}
                  className={`px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-all ${
                    currentView === 'trip-planner'
                      ? 'bg-primary/20 text-primary'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <MapPin className="w-4 h-4" />
                  Trip Planner
                </button>
                <button
                  onClick={() => {
                    setCurrentView('cart')
                    setMobileMenuOpen(false)
                  }}
                  className={`px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-all ${
                    currentView === 'cart'
                      ? 'bg-primary/20 text-primary'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <ShoppingCart className="w-4 h-4" />
                  Cart
                </button>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Main Content */}
      <main>
        <AnimatePresence mode="wait">
          {currentView === 'storefront' && (
            <motion.div
              key="storefront"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Storefront userId={currentUser} />
            </motion.div>
          )}
          {currentView === 'trip-planner' && (
            <motion.div
              key="trip-planner"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <TripPlanner userId={currentUser} />
            </motion.div>
          )}
          {currentView === 'cart' && (
            <motion.div
              key="cart"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <CartView userId={currentUser} loyaltyTier={USERS[currentUser].loyalty_tier} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Floating Chat Button (mobile) */}
      <button
        onClick={() => setChatModalOpen(true)}
        className="fixed bottom-6 right-6 md:hidden w-14 h-14 bg-primary rounded-full shadow-lg shadow-primary/50 flex items-center justify-center text-white hover:scale-110 transition-transform z-40"
      >
        <MessageSquare className="w-6 h-6" />
      </button>

      {/* Chat Modal */}
      <ChatModal
        isOpen={chatModalOpen}
        onClose={() => setChatModalOpen(false)}
        userId={currentUser}
        onOpenTripPlanner={() => setCurrentView('trip-planner')}
      />
    </div>
  )
}

export default App


