import { useState, useEffect } from 'react'
import { Storefront } from './components/Storefront'
import { TripPlanner } from './components/TripPlanner'
import { CartView } from './components/CartView'
import { CheckoutPage } from './components/CheckoutPage'
import { OrderConfirmation } from './components/OrderConfirmation'
import { SearchPanel } from './components/SearchPanel'
import { UserMenu } from './components/UserMenu'
import { UserAccountPage } from './components/UserAccountPage'
import { ErrorBoundary } from './components/ErrorBoundary'
import { DemoOverlay } from './components/DemoOverlay'
import { ShoppingCart, MapPin, Home, Menu, X, Search, Play } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from './lib/api'
import { UserPersona } from './types'

// Legacy user loyalty tiers (for backward compatibility)
const LEGACY_LOYALTY_TIERS: Record<string, string> = {
  'user_new': 'none',
  'user_member': 'platinum',
  'user_business': 'business',
}

type View = 'storefront' | 'trip-planner' | 'cart' | 'checkout' | 'order-confirmation' | 'account'

function App() {
  const [currentUser, setCurrentUser] = useState<string>('ultralight_backpacker_sarah')
  const [currentPersona, setCurrentPersona] = useState<UserPersona | null>(null)
  const [personas, setPersonas] = useState<UserPersona[]>([])
  const [currentView, setCurrentView] = useState<View>('storefront')
  const [searchPanelOpen, setSearchPanelOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [chatInitialMessage, setChatInitialMessage] = useState<string | undefined>()
  const [tripPlannerInitialMessage, setTripPlannerInitialMessage] = useState<string | undefined>()
  const [orderId, setOrderId] = useState<string | null>(null)
  const [confirmationNumber, setConfirmationNumber] = useState<string | null>(null)
  const [isDemoRunning, setIsDemoRunning] = useState(false)

  // Load personas on mount
  useEffect(() => {
    loadPersonas()
  }, [])

  // Update current persona when user changes
  useEffect(() => {
    const persona = personas.find(p => p.id === currentUser)
    setCurrentPersona(persona || null)
  }, [currentUser, personas])

  const loadPersonas = async () => {
    try {
      const data = await api.getUserPersonas()
      setPersonas(data.personas || [])
      // Set initial persona
      const initialPersona = data.personas?.find((p: UserPersona) => p.id === currentUser)
      if (initialPersona) {
        setCurrentPersona(initialPersona)
      }
    } catch (error) {
      console.error('Failed to load personas:', error)
    }
  }

  const refreshPersonaStats = async () => {
    // For guest user, get live stats and update persona
    if (currentUser === 'user_new') {
      try {
        const stats = await api.getUserStats(currentUser)
        // Update the persona in the list
        setPersonas(prev => prev.map(p => 
          p.id === currentUser 
            ? { ...p, total_views: stats.total_views, total_cart_adds: stats.total_cart_adds }
            : p
        ))
        // Update current persona
        setCurrentPersona(prev => prev 
          ? { ...prev, total_views: stats.total_views, total_cart_adds: stats.total_cart_adds }
          : null
        )
      } catch (error) {
        console.error('Failed to refresh stats:', error)
      }
    } else {
      // For other users, reload personas from API
      await loadPersonas()
    }
  }

  const handleClearHistory = async () => {
    // Refresh stats after clearing
    await refreshPersonaStats()
  }

  const getLoyaltyTier = (userId: string): string => {
    return LEGACY_LOYALTY_TIERS[userId] || 'none'
  }

  // Handle opening chat with context from product tags
  const handleStartChatWithContext = (productName: string, tag: string) => {
    setChatInitialMessage(`I'm looking at the **${productName}** and I'm interested in other **${tag}** gear. What do you recommend?`)
    setSearchPanelOpen(true)
  }

  // Handle 1-Click Demo
  const handleStartDemo = async () => {
    setIsDemoRunning(true)
    
    // Wait a moment for overlay to show
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Switch to Sarah Martinez persona
    const sarahPersona = personas.find(p => p.id === 'ultralight_backpacker_sarah')
    if (sarahPersona) {
      setCurrentUser('ultralight_backpacker_sarah')
      setCurrentPersona(sarahPersona)
    }
    
    // Wait for persona switch
    await new Promise(resolve => setTimeout(resolve, 300))
    
    // Set initial message for Trip Planner
    setTripPlannerInitialMessage("Planning a 3-day backpacking trip to Yosemite next month. What gear do I need?")
    
    // Navigate to Trip Planner
    setCurrentView('trip-planner')
    
    // Hide overlay after navigation
    await new Promise(resolve => setTimeout(resolve, 500))
    setIsDemoRunning(false)
  }

  useEffect(() => {
    const handleNavigate = (e: CustomEvent) => {
      if (e.detail === 'trip-planner') {
        setCurrentView('trip-planner')
      } else if (e.detail === 'checkout') {
        setCurrentView('checkout')
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
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-display font-bold text-gradient">Wayfinder</h1>
                <span className="text-gray-500 text-xl">|</span>
                <a
                  href="https://www.elastic.co/search-labs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-primary transition-colors"
                >
                  <img 
                    src="https://storage.googleapis.com/wayfinder_supply_co/logos/elastic%20logo%20cluster.png" 
                    alt="Elastic" 
                    className="w-4 h-4 object-contain"
                  />
                  <span>Powered by Elastic</span>
                </a>
              </div>
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
                onClick={handleStartDemo}
                disabled={isDemoRunning}
                className="hidden sm:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-cyan-500 hover:from-primary-dark hover:to-cyan-600 text-white rounded-lg transition-all border border-primary/30 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm shadow-lg shadow-primary/20"
                title="Watch Demo"
              >
                <Play className="w-4 h-4" />
                Watch Demo
              </button>
              <button
                onClick={() => setSearchPanelOpen(true)}
                className="flex items-center justify-center w-10 h-10 bg-primary/20 hover:bg-primary/30 text-primary rounded-lg transition-all border border-primary/30"
                title="Search & Chat"
              >
                <Search className="w-5 h-5" />
              </button>
              <UserMenu
                currentUserId={currentUser}
                currentPersona={currentPersona}
                onSwitchUser={() => {
                  setCurrentView('account')
                  setMobileMenuOpen(false)
                }}
                onClearHistory={handleClearHistory}
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
        <ErrorBoundary>
          <AnimatePresence mode="wait">
            {currentView === 'storefront' && (
              <motion.div
                key="storefront"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <ErrorBoundary>
                  <Storefront userId={currentUser} onStartChat={handleStartChatWithContext} />
                </ErrorBoundary>
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
                <ErrorBoundary>
                  <TripPlanner 
                    userId={currentUser} 
                    initialMessage={tripPlannerInitialMessage}
                    onInitialMessageSent={() => setTripPlannerInitialMessage(undefined)}
                  />
                </ErrorBoundary>
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
                <ErrorBoundary>
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <CartView userId={currentUser} loyaltyTier={getLoyaltyTier(currentUser)} />
                  </div>
                </ErrorBoundary>
              </motion.div>
            )}
            {currentView === 'checkout' && (
              <motion.div
                key="checkout"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <ErrorBoundary>
                  <CheckoutPage
                    userId={currentUser}
                    loyaltyTier={getLoyaltyTier(currentUser)}
                    onBack={() => setCurrentView('cart')}
                    onOrderComplete={(orderId, confirmationNumber) => {
                      setOrderId(orderId)
                      setConfirmationNumber(confirmationNumber)
                      setCurrentView('order-confirmation')
                    }}
                  />
                </ErrorBoundary>
              </motion.div>
            )}
            {currentView === 'order-confirmation' && orderId && confirmationNumber && (
              <motion.div
                key="order-confirmation"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <ErrorBoundary>
                  <OrderConfirmation
                    userId={currentUser}
                    orderId={orderId}
                    confirmationNumber={confirmationNumber}
                    onContinueShopping={() => setCurrentView('storefront')}
                  />
                </ErrorBoundary>
              </motion.div>
            )}
            {currentView === 'account' && (
              <motion.div
                key="account"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <ErrorBoundary>
                  <UserAccountPage
                    currentUserId={currentUser}
                    onSelectUser={(userId, persona) => {
                      setCurrentUser(userId)
                      if (persona) {
                        setCurrentPersona(persona)
                      }
                      setCurrentView('storefront')
                    }}
                  />
                </ErrorBoundary>
              </motion.div>
            )}
          </AnimatePresence>
        </ErrorBoundary>
      </main>

      {/* Floating Search Button (only on very small screens where header might be cramped) */}
      <button
        onClick={() => setSearchPanelOpen(true)}
        className="fixed bottom-6 right-6 sm:hidden w-14 h-14 bg-primary rounded-full shadow-lg shadow-primary/50 flex items-center justify-center text-white hover:scale-110 transition-transform z-40"
      >
        <Search className="w-6 h-6" />
      </button>

      {/* Search Panel */}
      <ErrorBoundary>
        <SearchPanel
          isOpen={searchPanelOpen}
          onClose={() => setSearchPanelOpen(false)}
          userId={currentUser}
          onOpenTripPlanner={() => setCurrentView('trip-planner')}
          initialMessage={chatInitialMessage}
          onInitialMessageSent={() => setChatInitialMessage(undefined)}
        />
      </ErrorBoundary>

      {/* Demo Overlay */}
      <DemoOverlay isVisible={isDemoRunning} />
    </div>
  )
}

export default App

