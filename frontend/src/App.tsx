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
import { PersonalizationDemo } from './components/PersonalizationDemo'
import { SearchComparisonDemo } from './components/SearchComparisonDemo'
import { ShoppingCart, MapPin, Home, Menu, X, Search, Play, Eye, Sparkles, ChevronDown, Settings } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from './lib/api'
import { UserPersona, ChatMessage, ThoughtTraceEvent, SuggestedProduct, ItineraryDay, SettingsStatus } from './types'
import { SettingsPage } from './components/SettingsPage'
import { 
  SearchMode as SearchModeType, 
  ExtendedChatMessage 
} from './components/search/types'

type View = 'storefront' | 'trip-planner' | 'cart' | 'checkout' | 'order-confirmation' | 'account' | 'settings'

const LEGACY_LOYALTY_TIERS: Record<string, string> = {
  'user_member': 'gold',
  'user_business': 'platinum',
  'ultralight_backpacker_sarah': 'gold',
  'family_camper_mike': 'silver',
  'winter_mountaineer_alex': 'gold'
}

function App() {
  const [currentUser, setCurrentUser] = useState<string>('user_member')
  const [currentPersona, setCurrentPersona] = useState<UserPersona | null>(null)
  const [personas, setPersonas] = useState<UserPersona[]>([])
  const [currentView, setCurrentView] = useState<View>('storefront')
  const [searchPanelOpen, setSearchPanelOpen] = useState(false)
  
  // Persisted SearchPanel state
  const [searchMessages, setSearchMessages] = useState<ExtendedChatMessage[]>([])
  const [searchMode, setSearchMode] = useState<SearchModeType>('chat')
  const [searchStepsExpanded, setSearchStepsExpanded] = useState<Record<string, boolean>>({})
  const [searchExpandedSteps, setSearchExpandedSteps] = useState<Set<string>>(new Set())
  const [personalizationEnabled, setPersonalizationEnabled] = useState(false)

  // Persisted TripPlanner state
  const [plannerMessages, setPlannerMessages] = useState<ChatMessage[]>([])
  const [plannerContext, setPlannerContext] = useState({
    destination: '',
    dates: '',
    activity: '',
  })
  const [plannerOriginalContext, setPlannerOriginalContext] = useState({
    destination: '',
    dates: '',
    activity: '',
  })
  const [plannerSuggestedProducts, setPlannerSuggestedProducts] = useState<SuggestedProduct[]>([])
  const [plannerOtherRecommendedItems, setPlannerOtherRecommendedItems] = useState<string[]>([])
  const [plannerItinerary, setPlannerItinerary] = useState<ItineraryDay[]>([])
  const [plannerMessageTraces, setPlannerMessageTraces] = useState<Record<string, ThoughtTraceEvent[]>>({})

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [chatInitialMessage, setChatInitialMessage] = useState<string | undefined>()
  const [tripPlannerInitialMessage, setTripPlannerInitialMessage] = useState<string | undefined>()
  const [orderId, setOrderId] = useState<string | null>(null)
  const [confirmationNumber, setConfirmationNumber] = useState<string | null>(null)
  const [isDemoRunning, setIsDemoRunning] = useState(false)
  const [demoModeRequested, setDemoModeRequested] = useState(false)
  const [focusMode, setFocusMode] = useState(() => 
    localStorage.getItem('wf_focus_mode') === 'true'
  )
  const [narrationMode, setNarrationMode] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search)
    return urlParams.get('narration') === 'true' || localStorage.getItem('wf_narration_mode') === 'true'
  })
  const [showPersonalizationDemo, setShowPersonalizationDemo] = useState(false)
  const [showSearchComparisonDemo, setShowSearchComparisonDemo] = useState(false)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)
  const [wowDropdownOpen, setWowDropdownOpen] = useState(false)
  
  // Vision / settings status
  const [settingsStatus, setSettingsStatus] = useState<SettingsStatus>({
    jina_vlm: 'not_configured',
    vertex_ai: 'not_configured',
    imagen: 'not_configured',
  })

  // Load personas and settings status on mount
  useEffect(() => {
    loadPersonas()
    api.getSettingsStatus().then(setSettingsStatus).catch(() => {})
  }, [])

  // Update current persona when user changes
  useEffect(() => {
    const persona = personas.find(p => p.id === currentUser)
    setCurrentPersona(persona || null)
  }, [currentUser, personas])

  // Close wow dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setWowDropdownOpen(false)
    }
    if (wowDropdownOpen) {
      window.addEventListener('click', handleClickOutside)
      return () => window.removeEventListener('click', handleClickOutside)
    }
  }, [wowDropdownOpen])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus Mode (Ctrl+Shift+F)
      if (e.ctrlKey && e.shiftKey && e.key === 'F') {
        e.preventDefault()
        setFocusMode(prev => {
          const next = !prev
          localStorage.setItem('wf_focus_mode', String(next))
          return next
        })
      }
      // Narration Mode (Ctrl+Shift+N)
      else if (e.ctrlKey && e.shiftKey && e.key === 'N') {
        e.preventDefault()
        setNarrationMode(prev => {
          const next = !prev
          localStorage.setItem('wf_narration_mode', String(next))
          return next
        })
      }
      // Personalization Demo (Ctrl+Shift+1)
      else if (e.ctrlKey && e.shiftKey && e.key === '1') {
        e.preventDefault()
        setShowPersonalizationDemo(true)
      }
      // Search Comparison Demo (Ctrl+Shift+2)
      else if (e.ctrlKey && e.shiftKey && e.key === '2') {
        e.preventDefault()
        setShowSearchComparisonDemo(true)
      }
      // Keyboard Help (?)
      else if (e.key === '?' && !e.ctrlKey && !e.shiftKey && !e.metaKey && !e.altKey) {
        e.preventDefault()
        setShowKeyboardHelp(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

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

  // Handle 1-Click Demo - Opens Search Panel demo (works without trip-planner-agent)
  const handleStartDemo = async () => {
    setIsDemoRunning(true)
    
    // Wait a moment for overlay to show
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Switch to Sarah Martinez persona for personalized results
    const sarahPersona = personas.find(p => p.id === 'ultralight_backpacker_sarah')
    if (sarahPersona) {
      setCurrentUser('ultralight_backpacker_sarah')
      setCurrentPersona(sarahPersona)
    }
    
    // Wait for persona switch
    await new Promise(resolve => setTimeout(resolve, 300))
    
    // Set flag to auto-show demo picker when panel opens
    setDemoModeRequested(true)
    
    // Open Search Panel - it has its own "Watch This" demo that works
    // with wayfinder-search-agent (pre-created, no Challenge 4 needed)
    setSearchPanelOpen(true)
    
    // Hide overlay after panel opens
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
              {!focusMode && (
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
              )}
              {/* Focus Mode Indicator */}
              {focusMode && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/20 text-primary rounded-lg text-sm">
                  <Eye className="w-4 h-4" />
                  <span>Focus Mode</span>
                </div>
              )}
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
              </nav>
            </div>
            <div className="flex items-center gap-3">
              {/* Demos Dropdown - combines Watch Demo + Wow Moments */}
              <div className="relative hidden sm:block">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setWowDropdownOpen(!wowDropdownOpen)
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-cyan-500 hover:from-primary-dark hover:to-cyan-600 text-white rounded-lg transition-all border border-primary/30 font-medium text-sm shadow-lg shadow-primary/20"
                  title="Demos"
                >
                  <Play className="w-4 h-4" />
                  <span>Demos</span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${wowDropdownOpen ? 'rotate-180' : ''}`} />
                </button>
                {wowDropdownOpen && (
                  <div 
                    className="absolute right-0 top-full mt-2 w-64 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => {
                        setWowDropdownOpen(false)
                        handleStartDemo()
                      }}
                      disabled={isDemoRunning}
                      className="w-full px-4 py-3 text-left hover:bg-slate-700 transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Play className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="text-white font-medium">Watch Demo</div>
                        <div className="text-gray-400 text-xs mt-1">Guided search walkthrough</div>
                      </div>
                    </button>
                    <button
                      onClick={() => {
                        setShowPersonalizationDemo(true)
                        setWowDropdownOpen(false)
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-slate-700 transition-colors flex items-center gap-3 border-t border-slate-700"
                    >
                      <Sparkles className="w-4 h-4 text-purple-400 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="text-white font-medium">Personalization Difference</div>
                        <div className="text-gray-400 text-xs mt-1">Compare Guest vs Sarah results</div>
                      </div>
                    </button>
                    <button
                      onClick={() => {
                        setShowSearchComparisonDemo(true)
                        setWowDropdownOpen(false)
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-slate-700 transition-colors flex items-center gap-3 border-t border-slate-700"
                    >
                      <Sparkles className="w-4 h-4 text-pink-400 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="text-white font-medium">Search Mode Comparison</div>
                        <div className="text-gray-400 text-xs mt-1">Lexical vs Hybrid vs Agentic</div>
                      </div>
                    </button>
                  </div>
                )}
              </div>
              {/* Cart Icon */}
              {!focusMode && (
                <button
                  onClick={() => setCurrentView('cart')}
                  className={`flex items-center justify-center w-10 h-10 rounded-lg transition-all border ${
                    currentView === 'cart'
                      ? 'bg-primary/20 text-primary border-primary/30'
                      : 'bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border-white/10'
                  }`}
                  title="Cart"
                >
                  <ShoppingCart className="w-5 h-5" />
                </button>
              )}
              {/* Search Icon */}
              <button
                onClick={() => {
                  setCurrentView('settings')
                  setMobileMenuOpen(false)
                }}
                className={`flex items-center justify-center w-10 h-10 rounded-lg transition-all border ${
                  currentView === 'settings'
                    ? 'bg-primary/20 text-primary border-primary/30'
                    : 'bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border-white/10'
                }`}
                title="Vision Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={() => setSearchPanelOpen(true)}
                className="flex items-center justify-center w-10 h-10 bg-primary/20 hover:bg-primary/30 text-primary rounded-lg transition-all border border-primary/30"
                title="Search & Chat"
              >
                <Search className="w-5 h-5" />
              </button>
              {!focusMode && (
                <UserMenu
                  currentUserId={currentUser}
                  currentPersona={currentPersona}
                  onSwitchUser={() => {
                    setCurrentView('account')
                    setMobileMenuOpen(false)
                  }}
                  onClearHistory={handleClearHistory}
                />
              )}
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu - Inside header for proper stacking */}
        <AnimatePresence>
          {mobileMenuOpen && !focusMode && (
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
                  <Storefront userId={currentUser} onStartChat={handleStartChatWithContext} focusMode={focusMode} />
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
                    settingsStatus={settingsStatus}
                    messages={plannerMessages}
                    setMessages={setPlannerMessages}
                    tripContext={plannerContext}
                    setTripContext={setPlannerContext}
                    originalContext={plannerOriginalContext}
                    setOriginalContext={setPlannerOriginalContext}
                    suggestedProducts={plannerSuggestedProducts}
                    setSuggestedProducts={setPlannerSuggestedProducts}
                    otherRecommendedItems={plannerOtherRecommendedItems}
                    setOtherRecommendedItems={setPlannerOtherRecommendedItems}
                    itinerary={plannerItinerary}
                    setItinerary={setPlannerItinerary}
                    messageTraces={plannerMessageTraces}
                    setMessageTraces={setPlannerMessageTraces}
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
            {currentView === 'settings' && (
              <motion.div
                key="settings"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <ErrorBoundary>
                  <SettingsPage
                    settingsStatus={settingsStatus}
                    onStatusChange={setSettingsStatus}
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
          startInDemoMode={demoModeRequested}
          onDemoModeStarted={() => setDemoModeRequested(false)}
          narrationMode={narrationMode}
          messages={searchMessages}
          setMessages={setSearchMessages}
          mode={searchMode}
          setMode={setSearchMode}
          stepsExpanded={searchStepsExpanded}
          setStepsExpanded={setSearchStepsExpanded}
          expandedSteps={searchExpandedSteps}
          setExpandedSteps={setSearchExpandedSteps}
          personalizationEnabled={personalizationEnabled}
          setPersonalizationEnabled={setPersonalizationEnabled}
          settingsStatus={settingsStatus}
        />
      </ErrorBoundary>

      {/* Demo Overlay */}
      <DemoOverlay isVisible={isDemoRunning} />

      {/* Wow Moment Demos */}
      {showPersonalizationDemo && (
        <PersonalizationDemo onClose={() => setShowPersonalizationDemo(false)} />
      )}
      {showSearchComparisonDemo && (
        <SearchComparisonDemo onClose={() => setShowSearchComparisonDemo(false)} userId={currentUser} />
      )}

      {/* Keyboard Help Modal */}
      {showKeyboardHelp && (
        <div 
          className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setShowKeyboardHelp(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 w-full max-w-2xl"
          >
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <h2 className="text-2xl font-display font-bold text-white">Keyboard Shortcuts</h2>
              <button
                onClick={() => setShowKeyboardHelp(false)}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="w-5 h-5 text-gray-300" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-gray-300">Focus Mode</span>
                  <kbd className="px-2 py-1 bg-slate-800 rounded text-sm text-gray-300">Ctrl+Shift+F</kbd>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-gray-300">Narration Banners</span>
                  <kbd className="px-2 py-1 bg-slate-800 rounded text-sm text-gray-300">Ctrl+Shift+N</kbd>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-gray-300">Personalization Demo</span>
                  <kbd className="px-2 py-1 bg-slate-800 rounded text-sm text-gray-300">Ctrl+Shift+1</kbd>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-gray-300">Search Comparison Demo</span>
                  <kbd className="px-2 py-1 bg-slate-800 rounded text-sm text-gray-300">Ctrl+Shift+2</kbd>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-gray-300">Show This Help</span>
                  <kbd className="px-2 py-1 bg-slate-800 rounded text-sm text-gray-300">?</kbd>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default App

