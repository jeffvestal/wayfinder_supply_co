import { useState, useRef, useEffect } from 'react'
import { ChatMessage, UserId, ThoughtTraceEvent } from '../types'
import { api } from '../lib/api'
import { 
  Send, Loader2, MapPin, Calendar, Mountain, ChevronDown, ChevronRight,
  ShoppingCart, Plus, Compass, CloudSun, Backpack, CheckCircle2, Clock,
  Tent, Thermometer, Map, Sun, Moon, RefreshCw
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { motion, AnimatePresence } from 'framer-motion'

interface TripPlannerProps {
  userId: UserId
}

interface SuggestedProduct {
  id: string
  title: string
  price: number
  image_url?: string
  reason?: string
}

interface ItineraryDay {
  day: number
  title: string
  activities: string[]
  weather?: string
  gear_needed?: string[]
}

// Map tool IDs to friendly contextual messages
function getToolStatusMessage(toolId: string): string {
  const toolMessages: Record<string, string> = {
    'tool-workflow-check-trip-safety': 'Checking weather conditions...',
    'tool-workflow-get-customer-profile': 'Looking up your preferences...',
    'tool-workflow-get-user-affinity': 'Analyzing your gear style...',
    'tool-search-product-search': 'Scanning the catalog...',
    'tool-esql-get-user-affinity': 'Reviewing your browsing history...',
  }
  return toolMessages[toolId] || 'Planning your adventure...'
}

// Get current thinking status from trace events
function getCurrentStatus(events: ThoughtTraceEvent[], isLoading: boolean): string {
  if (!isLoading) return ''
  if (events.length === 0) return 'Starting up...'
  
  const lastEvent = events[events.length - 1]
  if (lastEvent.event === 'reasoning') {
    return 'Thinking...'
  } else if (lastEvent.event === 'tool_call') {
    return getToolStatusMessage(lastEvent.data?.tool_id || '')
  } else if (lastEvent.event === 'tool_result') {
    return 'Processing results...'
  }
  return 'Working...'
}

// Known brand names in our catalog
const KNOWN_BRANDS = ['Wayfinder Supply', 'Summit Pro', 'TrailBlazer', 'PocketRocket', 'Basecamp', 'Apex Expedition', 'Summit', 'Wayfinder']

// Gear category keywords for semantic search
const GEAR_CATEGORIES = [
  'sleeping bag', 'tent', 'backpack', 'pack', 'stove', 'pad', 'mat', 
  'jacket', 'boot', 'shoe', 'glove', 'mitt', 'sock', 'layer', 'insulation',
  'headlamp', 'flashlight', 'poles', 'trekking', 'water', 'filter'
]

// Parse product names from agent response text
function parseProductsFromResponse(content: string): { catalogProducts: string[], otherItems: string[], gearSearchTerms: string[] } {
  const catalogProducts: string[] = []
  const otherItems: string[] = []
  const gearSearchTerms: string[] = []
  
  // Remove markdown formatting for easier parsing
  const cleanText = content
    .replace(/#{1,6}\s+/g, '') // Remove headers
    .replace(/\*\*/g, '') // Remove bold
    .replace(/\*/g, '') // Remove italic
    .replace(/`/g, '') // Remove code blocks
  
  // Pattern 1: Products with prices (new format from agent: "Product Name - $XX.XX")
  const pricePattern = /([A-Z][A-Za-z0-9\s&\-]+)\s*[-–]\s*\$(\d+\.?\d*)/g
  
  let match
  while ((match = pricePattern.exec(cleanText)) !== null) {
    const productName = match[1].trim()
    // Check if it contains a known brand
    const hasBrand = KNOWN_BRANDS.some(brand => 
      productName.toLowerCase().includes(brand.toLowerCase())
    )
    
    if (productName.length > 10 && hasBrand && !catalogProducts.includes(productName)) {
      catalogProducts.push(productName)
    }
  }
  
  // Pattern 2: Products with known brands (without prices)
  const brandPattern = new RegExp(
    `(${KNOWN_BRANDS.join('|')})\\s+([A-Za-z0-9\\s&\\-]+(?:Sleeping Bag|Tent|Backpack|Stove|Pad|Mat|Jacket|Boot|Shoe|Pack|System|Line|Series|Expedition|Apex|Basecamp)?(?:\\s+\\d+)?)`,
    'gi'
  )
  
  while ((match = brandPattern.exec(cleanText)) !== null) {
    const productName = `${match[1]} ${match[2]}`.trim()
    if (productName.length > 10 && !catalogProducts.includes(productName)) {
      catalogProducts.push(productName)
    }
  }
  
  // Pattern 3: Extract gear categories mentioned for semantic search
  for (const category of GEAR_CATEGORIES) {
    const categoryPattern = new RegExp(`(\\w+\\s+)?${category}s?(?:\\s+\\w+)?`, 'gi')
    while ((match = categoryPattern.exec(cleanText)) !== null) {
      const term = match[0].trim()
      if (term.length > 5 && !gearSearchTerms.includes(term)) {
        gearSearchTerms.push(term)
      }
    }
  }
  
  // Pattern 4: Generic gear recommendations (for "Other Items")
  // Match bullet points that look like gear but don't have our brands
  const bulletPattern = /[•\-]\s*([A-Z][A-Za-z0-9\s&\-]+(?:Sleeping Bag|Tent|Backpack|Stove|Pad|Mat|Jacket|Boot|Shoe|Pack|Mitts?|Gloves?|Socks?|Layer|Insulation)?(?:\s+\d+)?)/g
  
  while ((match = bulletPattern.exec(cleanText)) !== null) {
    const item = match[1].trim()
    const hasBrand = KNOWN_BRANDS.some(brand => 
      item.toLowerCase().includes(brand.toLowerCase())
    )
    
    // Filter out false positives
    if (item.length > 10 && 
        !item.match(/^(Essential|Recommended|Consider|Add|Include|Use|Bring|Pack|Take|Check|Important|Day\s*\d)/i) &&
        !item.match(/^(Weather|Conditions|Temperatures|Snow|Rain|Wind|Road|Mountain|Start|Explore|Hike|Reserve)/i) &&
        !item.match(/^(Note|What|Why|How|When|Where)/i)) {
      
      if (hasBrand && !catalogProducts.includes(item)) {
        catalogProducts.push(item)
      } else if (!hasBrand && !otherItems.includes(item)) {
        // Check if it looks like a gear item (contains category keyword)
        const isGearItem = GEAR_CATEGORIES.some(cat => item.toLowerCase().includes(cat))
        if (isGearItem) {
          otherItems.push(item)
        }
      }
    }
  }
  
  // Filter out items that are too long or look like headers/descriptions
  const filteredOtherItems = [...new Set(otherItems)].filter(item => {
    // Remove items that are too long (likely descriptions, not product names)
    if (item.length > 100) return false
    // Remove items that look like full sentences or descriptions
    if (item.match(/^[A-Z][a-z]+ [a-z]+ [a-z]+/)) {
      // Check if it's a gear item or just a description
      const hasGearKeyword = GEAR_CATEGORIES.some(cat => item.toLowerCase().includes(cat))
      if (!hasGearKeyword && item.split(' ').length > 5) return false
    }
    return true
  }).slice(0, 10)
  
  return {
    catalogProducts: [...new Set(catalogProducts)].slice(0, 6),
    otherItems: filteredOtherItems,
    gearSearchTerms: [...new Set(gearSearchTerms)].slice(0, 8)
  }
}

export function TripPlanner({ userId }: TripPlannerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [thoughtTrace, setThoughtTrace] = useState<ThoughtTraceEvent[]>([])
  const [expandedThinking, setExpandedThinking] = useState(false)
  // Store thought traces per message for persistence after agent responds
  const [messageTraces, setMessageTraces] = useState<Record<string, ThoughtTraceEvent[]>>({})
  const [tripContext, setTripContext] = useState({
    destination: '',
    dates: '',
    activity: '',
  })
  const [originalContext, setOriginalContext] = useState({
    destination: '',
    dates: '',
    activity: '',
  })
  const [contextModified, setContextModified] = useState(false)
  const [suggestedProducts, setSuggestedProducts] = useState<SuggestedProduct[]>([])
  const [otherRecommendedItems, setOtherRecommendedItems] = useState<string[]>([])
  const [itinerary, setItinerary] = useState<ItineraryDay[]>([])
  const [cartExpanded, setCartExpanded] = useState(true)
  const [otherItemsExpanded, setOtherItemsExpanded] = useState(false)
  const [itineraryExpanded, setItineraryExpanded] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check if context has been modified
  useEffect(() => {
    const modified = 
      tripContext.destination !== originalContext.destination ||
      tripContext.dates !== originalContext.dates ||
      tripContext.activity !== originalContext.activity
    setContextModified(modified)
  }, [tripContext, originalContext])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const messageText = input.trim()
    const isFirstMessage = !tripContext.destination && !tripContext.dates && !tripContext.activity

    // Only parse context on FIRST message when boxes are empty
    // For follow-ups, skip parsing and send immediately
    if (isFirstMessage) {
      // Show user message immediately
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: messageText,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])
      setInput('')
      setIsLoading(true)
      setThoughtTrace([])
      setExpandedThinking(false)

      // Parse context in parallel (don't block on it)
      api.parseTripContext(messageText)
        .then((parsed) => {
          if (parsed.destination || parsed.dates || parsed.activity) {
            const newContext = {
              destination: parsed.destination || tripContext.destination,
              dates: parsed.dates || tripContext.dates,
              activity: parsed.activity || tripContext.activity,
            }
            setTripContext(newContext)
            setOriginalContext(newContext)
          }
        })
        .catch((error) => {
          console.error('Failed to parse trip context:', error)
        })

      // Start chat stream immediately (don't wait for context parsing)
      await sendMessage(messageText, false) // false = don't add user message again
    } else {
      // Follow-up message - send immediately without parsing
      await sendMessage(messageText)
    }
  }

  const handleUpdatePlan = async () => {
    if (isLoading) return
    const updateMessage = `Update my trip plan: Going to ${tripContext.destination} ${tripContext.dates} for ${tripContext.activity}`
    setOriginalContext({ ...tripContext })
    setContextModified(false)
    await sendMessage(updateMessage)
  }

  const sendMessage = async (messageText: string, addUserMessage: boolean = true) => {
    // Generate a unique ID for this message's trace
    const currentMessageId = Date.now().toString()
    
    if (addUserMessage) {
      const userMessage: ChatMessage = {
        id: currentMessageId,
        role: 'user',
        content: messageText,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])
    }
    
    setInput('')
    setIsLoading(true)
    setThoughtTrace([])
    setExpandedThinking(false)
    
    // Track the current user message ID for storing the trace
    const userMessageId = addUserMessage ? currentMessageId : messages[messages.length - 1]?.id || currentMessageId
    
    // Collect trace events locally so we can save them at the end
    const localTraceEvents: ThoughtTraceEvent[] = []

    try {
      let currentAssistantMessage: ChatMessage | null = null
      let messageContent = ''

      await api.streamChat(messageText, userId, (event) => {
        const data = event.data

        if (event.type === 'reasoning') {
          const traceEvent: ThoughtTraceEvent = {
            event: 'reasoning',
            data: data.reasoning || data,
            timestamp: new Date(),
          }
          localTraceEvents.push(traceEvent)
          setThoughtTrace((prev) => [...prev, traceEvent])
        } else if (event.type === 'tool_call') {
          if (!data.tool_id || !data.params || Object.keys(data.params).length === 0) return
          const traceEvent: ThoughtTraceEvent = {
            event: 'tool_call',
            data: {
              tool_id: data.tool_id,
              params: data.params,
              tool_call_id: data.tool_call_id,
            },
            timestamp: new Date(),
          }
          localTraceEvents.push(traceEvent)
          setThoughtTrace((prev) => [...prev, traceEvent])
        } else if (event.type === 'tool_result') {
          const traceEvent: ThoughtTraceEvent = {
            event: 'tool_result',
            data: {
              tool_call_id: data.tool_call_id,
              results: data.results,
            },
            timestamp: new Date(),
          }
          localTraceEvents.push(traceEvent)
          setThoughtTrace((prev) => [...prev, traceEvent])
          
          // Extract products from search results (product_search tool)
          // Results can be an array or an object with products array
          let productsArray: any[] = []
          if (Array.isArray(data.results)) {
            productsArray = data.results
          } else if (data.results && typeof data.results === 'object') {
            // Check if results has a products array
            if (Array.isArray(data.results.products)) {
              productsArray = data.results.products
            } else if (data.results.hits && Array.isArray(data.results.hits)) {
              // Elasticsearch search response format
              productsArray = data.results.hits.map((hit: any) => ({
                ...hit._source,
                id: hit._id,
              }))
            } else {
              // Try to extract any array-like structure
              const keys = Object.keys(data.results)
              for (const key of keys) {
                if (Array.isArray(data.results[key]) && data.results[key].length > 0) {
                  productsArray = data.results[key]
                  break
                }
              }
            }
          }
          
          if (productsArray.length > 0) {
            const products = productsArray
              .filter((r: any) => r && (r.title || r.name) && r.price)
              .map((r: any) => ({
                id: r.id || r._id || r.sku || `product-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                title: r.title || r.name,
                price: typeof r.price === 'number' ? r.price : parseFloat(r.price) || 0,
                image_url: r.image_url || r.image,
                reason: (r.description || r.reason || '').slice(0, 100),
              }))
              .filter((p: SuggestedProduct) => p.price > 0)
            
            if (products.length > 0) {
              setSuggestedProducts((prev) => {
                const existingIds = new Set(prev.map(p => p.id))
                const newProducts = products.filter((p: SuggestedProduct) => !existingIds.has(p.id))
                const combined = [...prev, ...newProducts]
                const unique = combined.filter((p, idx, arr) => 
                  arr.findIndex(pp => pp.id === p.id) === idx
                )
                return unique.slice(0, 6)
              })
            }
          }
        } else if (event.type === 'message_chunk') {
          messageContent += data.text_chunk || ''
          if (!currentAssistantMessage) {
            currentAssistantMessage = {
              id: data.message_id || Date.now().toString(),
              role: 'assistant',
              content: messageContent,
              timestamp: new Date(),
            }
            setMessages((prev) => [...prev, currentAssistantMessage!])
          } else {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === currentAssistantMessage!.id
                  ? { ...msg, content: messageContent }
                  : msg
              )
            )
          }
        } else if (event.type === 'message_complete') {
          messageContent = data.message_content || messageContent
          if (currentAssistantMessage) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === currentAssistantMessage!.id
                  ? { ...msg, content: messageContent }
                  : msg
              )
            )
          }
          
          // Parse itinerary from response (quick regex-based)
          parseItineraryFromResponse(messageContent)
          
          // Skip slow entity extraction - products already extracted from tool_result events
          // Use fallback regex extraction as backup (runs in parallel, won't hurt)
          extractProductsFromResponseFallback(messageContent)
        }
      })
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      // Store the thought trace for this message so it persists after assistant responds
      if (localTraceEvents.length > 0) {
        setMessageTraces(prev => ({
          ...prev,
          [userMessageId]: localTraceEvents
        }))
      }
    }
  }

  const parseItineraryFromResponse = (content: string) => {
    // Look for day-by-day patterns in the response
    const dayPatterns = [
      /Day\s*(\d+)[:\s-]+(.+?)(?=Day\s*\d+|$)/gis,
      /(\d+)(?:st|nd|rd|th)\s+Day[:\s-]+(.+?)(?=\d+(?:st|nd|rd|th)\s+Day|$)/gis,
    ]
    
    const days: ItineraryDay[] = []
    
    for (const pattern of dayPatterns) {
      let match
      while ((match = pattern.exec(content)) !== null) {
        const dayNum = parseInt(match[1])
        const dayContent = match[2].trim()
        
        // Extract activities from the day content
        const activities = dayContent
          .split(/[•\-\n]/)
          .map(a => a.trim())
          .filter(a => a.length > 0 && a.length < 200)
          .slice(0, 5)
        
        if (activities.length > 0) {
          days.push({
            day: dayNum,
            title: `Day ${dayNum}`,
            activities,
          })
        }
      }
      if (days.length > 0) break
    }
    
    // If no structured days found, create a simple itinerary from key points
    if (days.length === 0 && content.length > 100) {
      const bulletPoints = content
        .split(/[•\-\n]/)
        .map(a => a.trim())
        .filter(a => a.length > 20 && a.length < 200)
        .slice(0, 6)
      
      if (bulletPoints.length >= 2) {
        setItinerary([{
          day: 1,
          title: 'Trip Overview',
          activities: bulletPoints,
        }])
        return
      }
    }
    
    if (days.length > 0) {
      setItinerary(days)
    }
  }

  // Regex-based extraction (fallback if tool_result doesn't capture products)
  const extractProductsFromResponseFallback = async (content: string) => {
    const { catalogProducts, otherItems, gearSearchTerms } = parseProductsFromResponse(content)
    
    const existingIds = new Set<string>()
    
    // Search all catalog products in parallel
    const catalogSearchPromises = catalogProducts.map(async (productName) => {
      try {
        const searchResult = await api.searchProducts(productName, 1)
        if (searchResult.products && searchResult.products.length > 0) {
          const product = searchResult.products[0]
          if (product.price > 0) {
            return {
              id: product.id || product._id,
              title: product.title || productName,
              price: product.price,
              image_url: product.image_url,
              reason: product.description?.slice(0, 100),
            }
          }
        }
      } catch (error) {
        console.error(`Failed to search for product "${productName}":`, error)
      }
      return null
    })
    
    // Also search gear terms in parallel
    const gearSearchPromises = gearSearchTerms.slice(0, 4).map(async (term) => {
      try {
        const searchResult = await api.searchProducts(term, 1)
        if (searchResult.products && searchResult.products.length > 0) {
          const product = searchResult.products[0]
          if (product.price > 0) {
            return {
              id: product.id || product._id,
              title: product.title,
              price: product.price,
              image_url: product.image_url,
              reason: `Great for ${term}`,
            }
          }
        }
      } catch (error) {
        console.error(`Failed semantic search for "${term}":`, error)
      }
      return null
    })
    
    // Wait for all searches
    const [catalogResults, gearResults] = await Promise.all([
      Promise.all(catalogSearchPromises),
      Promise.all(gearSearchPromises)
    ])
    
    // Combine and dedupe
    const allResults = [...catalogResults, ...gearResults]
    const foundProducts: SuggestedProduct[] = allResults
      .filter((p): p is NonNullable<typeof p> => p !== null)
      .filter(p => {
        if (existingIds.has(p.id)) return false
        existingIds.add(p.id)
        return true
      })
      .slice(0, 6)
    
    if (foundProducts.length > 0) {
      setSuggestedProducts((prev) => {
        const combined = [...prev, ...foundProducts]
        const unique = combined.filter((p, idx, arr) => 
          arr.findIndex(pp => pp.id === p.id) === idx
        )
        return unique.slice(0, 6)
      })
    }
    
    if (otherItems.length > 0) {
      setOtherRecommendedItems((prev) => {
        const combined = [...prev, ...otherItems]
        const unique = combined.filter((item, idx, arr) => 
          arr.findIndex(ii => ii.toLowerCase() === item.toLowerCase()) === idx
        )
        const filtered = unique.filter(item => 
          !foundProducts.some(fp => item.toLowerCase().includes(fp.title.toLowerCase().split(' ')[0]))
        )
        const final = filtered.filter(item => {
          if (item.length > 100) return false
          if (item.split(' ').length > 8 && !GEAR_CATEGORIES.some(cat => item.toLowerCase().includes(cat))) {
            return false
          }
          return true
        }).slice(0, 10)
        return final
      })
    }
  }

  const handleAddToCart = async (product: SuggestedProduct) => {
    try {
      await api.addToCart(userId, product.id, 1)
      // Visual feedback - could add a toast notification
    } catch (error) {
      console.error('Failed to add to cart:', error)
    }
  }

  const currentStatus = getCurrentStatus(thoughtTrace, isLoading)

  return (
    <div className="h-[calc(100vh-5rem)] bg-slate-950 flex flex-col overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 flex flex-col min-h-0 w-full">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-4xl font-display font-bold text-white mb-2">
            Trip Planner
          </h1>
          <p className="text-gray-300">
            Plan your perfect adventure with AI-powered recommendations
          </p>
        </motion.div>

        {/* Trip Context Inputs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6"
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="glass rounded-xl p-4">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                <MapPin className="w-4 h-4 text-primary" />
                Destination
              </label>
              <input
                type="text"
                value={tripContext.destination}
                onChange={(e) => setTripContext({ ...tripContext, destination: e.target.value })}
                placeholder="e.g., Rocky Mountains"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="glass rounded-xl p-4">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                <Calendar className="w-4 h-4 text-primary" />
                Dates
              </label>
              <input
                type="text"
                value={tripContext.dates}
                onChange={(e) => setTripContext({ ...tripContext, dates: e.target.value })}
                placeholder="e.g., This weekend"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="glass rounded-xl p-4">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                <Mountain className="w-4 h-4 text-primary" />
                Activity
              </label>
              <input
                type="text"
                value={tripContext.activity}
                onChange={(e) => setTripContext({ ...tripContext, activity: e.target.value })}
                placeholder="e.g., Camping, Hiking"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            {/* Update Plan Button */}
            <div className="flex items-end">
              <AnimatePresence>
                {contextModified && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    onClick={handleUpdatePlan}
                    disabled={isLoading}
                    className="w-full bg-primary hover:bg-primary-dark text-white px-4 py-3 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2 font-medium shadow-lg shadow-primary/20"
                  >
                    <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Update Plan
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Main Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
          {/* Chat Section */}
          <div className={`lg:col-span-2 flex flex-col rounded-2xl overflow-hidden transition-all duration-500 h-full ${
            messages.length === 0 
              ? 'bg-slate-200 shadow-xl border border-slate-300' 
              : 'bg-transparent'
          }`}>
            {/* Messages */}
            <div className={`flex-1 overflow-y-auto transition-all duration-500 ${
              messages.length === 0 ? 'p-6' : 'p-4'
            }`}>
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-center">
                  <div>
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                      <Compass className="w-8 h-8 text-primary" />
                    </div>
                    <h3 className="text-2xl font-display font-bold text-slate-800 mb-2">
                      Start Planning Your Adventure
                    </h3>
                    <p className="text-slate-600 mb-4">
                      Tell me about your trip and I'll recommend the perfect gear
                    </p>
                    <div className="text-sm text-slate-500 space-y-1">
                      <p className="flex items-center justify-center gap-2">
                        <Tent className="w-4 h-4" />
                        "I'm going camping in the Rockies this weekend"
                      </p>
                      <p className="flex items-center justify-center gap-2">
                        <Map className="w-4 h-4" />
                        "Planning a 3-day backpacking trip in Yosemite"
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      {/* Message bubble */}
                      <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                          className={`max-w-[85%] rounded-2xl px-5 py-3 shadow-lg ${
                            message.role === 'user'
                              ? 'bg-primary text-white'
                              : 'bg-white text-slate-800 shadow-sm border border-slate-200'
                          }`}
                        >
                        {message.role === 'assistant' ? (
                          <div className="prose prose-sm max-w-none prose-headings:text-slate-800 prose-p:text-slate-700 prose-strong:text-slate-800 prose-li:text-slate-700">
                            <ReactMarkdown
                              components={{
                                h1: ({ children }) => (
                                  <h1 className="text-xl font-display font-bold text-slate-800 mb-3 flex items-center gap-2">
                                    <Compass className="w-5 h-5 text-primary" />
                                    {children}
                                  </h1>
                                ),
                                h2: ({ children }) => (
                                  <h2 className="text-lg font-display font-semibold text-slate-800 mt-4 mb-2 flex items-center gap-2">
                                    {String(children).toLowerCase().includes('weather') && <CloudSun className="w-4 h-4 text-amber-500" />}
                                    {String(children).toLowerCase().includes('gear') && <Backpack className="w-4 h-4 text-primary" />}
                                    {String(children).toLowerCase().includes('recommend') && <CheckCircle2 className="w-4 h-4 text-green-500" />}
                                    {children}
                                  </h2>
                                ),
                                h3: ({ children }) => (
                                  <h3 className="text-base font-semibold text-slate-700 mt-3 mb-1">
                                    {children}
                                  </h3>
                                ),
                                ul: ({ children }) => (
                                  <ul className="space-y-1 my-2">{children}</ul>
                                ),
                                li: ({ children }) => (
                                  <li className="flex items-start gap-2 text-slate-700">
                                    <span className="text-primary mt-1">•</span>
                                    <span>{children}</span>
                                  </li>
                                ),
                                strong: ({ children }) => (
                                  <strong className="font-semibold text-slate-800">{children}</strong>
                                ),
                                p: ({ children }) => (
                                  <p className="text-slate-700 mb-2 leading-relaxed">{children}</p>
                                ),
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <p className="text-sm">{message.content}</p>
                        )}
                        <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/70' : 'text-slate-400'}`}>
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    
                    {/* Thinking section under user message - show for current message or stored traces */}
                    {message.role === 'user' && (
                      (index === messages.length - 1 && (isLoading || thoughtTrace.length > 0)) ||
                      messageTraces[message.id]?.length > 0
                    ) && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="ml-4"
                      >
                        <button
                          onClick={() => setExpandedThinking(!expandedThinking)}
                          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-300 transition-colors py-1"
                        >
                          {expandedThinking ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                          {isLoading && index === messages.length - 1 ? (
                            <span className="flex items-center gap-2">
                              <Loader2 className="w-3 h-3 animate-spin text-primary" />
                              <span className="text-primary font-medium">{currentStatus}</span>
                            </span>
                          ) : (
                            <span className="flex items-center gap-2">
                              <CheckCircle2 className="w-3 h-3 text-green-400" />
                              <span>Completed {(messageTraces[message.id] || thoughtTrace).length} steps</span>
                            </span>
                          )}
                        </button>
                        
                        <AnimatePresence>
                          {expandedThinking && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              className="mt-2 ml-6 space-y-2 border-l-2 border-slate-600 pl-4"
                            >
                              {(index === messages.length - 1 ? thoughtTrace : messageTraces[message.id] || []).map((trace, idx) => (
                                <div key={idx} className="text-xs">
                                  {trace.event === 'reasoning' && (
                                    <div className="flex items-start gap-2 text-slate-400">
                                      <Clock className="w-3 h-3 mt-0.5 text-blue-400" />
                                      <span>{typeof trace.data === 'string' ? trace.data : trace.data?.reasoning}</span>
                                    </div>
                                  )}
                                  {trace.event === 'tool_call' && (
                                    <div className="flex items-start gap-2 text-slate-400">
                                      <Backpack className="w-3 h-3 mt-0.5 text-amber-400" />
                                      <span>
                                        <span className="font-medium">{getToolStatusMessage(trace.data?.tool_id)}</span>
                                        {trace.data?.params && Object.keys(trace.data.params).length > 0 && (
                                          <span className="text-slate-500 ml-1">
                                            ({Object.values(trace.data.params).join(', ')})
                                          </span>
                                        )}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    )}
                    </motion.div>
                  ))}
                </div>
              )}
              {isLoading && messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
                <div className="flex justify-start mt-4">
                  <div className="bg-white rounded-2xl px-5 py-3 flex items-center gap-2 shadow-lg border border-slate-200">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-slate-600">{currentStatus}</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} className="h-2" />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className={`border-t p-4 transition-all duration-500 ${
              messages.length === 0 
                ? 'border-slate-300 bg-slate-100' 
                : 'border-slate-700/50 bg-slate-900/50 backdrop-blur-sm'
            }`}>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Tell me about your trip..."
                  className={`flex-1 rounded-xl px-4 py-3 transition-all duration-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                    messages.length === 0
                      ? 'bg-white border border-slate-300 text-slate-800 placeholder-slate-400'
                      : 'bg-white/90 backdrop-blur-sm border border-white/20 text-slate-800 placeholder-slate-500'
                  }`}
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg shadow-primary/20 hover:shadow-primary/40"
                >
                  <Send className="w-4 h-4" />
                  Send
                </button>
              </div>
            </form>
          </div>

          {/* Right Panel - Suggested Cart & Itinerary */}
          <div className="lg:col-span-1 space-y-4">
            {/* Suggested Cart */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="glass rounded-2xl overflow-hidden"
            >
              <button
                onClick={() => setCartExpanded(!cartExpanded)}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
                    <ShoppingCart className="w-5 h-5 text-primary" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-display font-semibold text-white">Suggested Gear</h3>
                    <p className="text-xs text-gray-400">
                      {suggestedProducts.length} in catalog
                      {otherRecommendedItems.length > 0 && ` • ${otherRecommendedItems.length} other items`}
                    </p>
                  </div>
                </div>
                {cartExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </button>
              
              <AnimatePresence>
                {cartExpanded && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    exit={{ height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="p-4 pt-0 space-y-4 max-h-[400px] overflow-y-auto">
                      {/* From Our Catalog Section */}
                      {suggestedProducts.length === 0 && otherRecommendedItems.length === 0 ? (
                        <p className="text-sm text-gray-400 text-center py-4">
                          Gear recommendations will appear here
                        </p>
                      ) : (
                        <>
                          {suggestedProducts.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2 flex items-center gap-2">
                                <CheckCircle2 className="w-3 h-3 text-green-400" />
                                From Our Catalog
                              </h4>
                              <div className="space-y-3">
                                {suggestedProducts.map((product) => (
                                  <div
                                    key={product.id}
                                    className="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10 hover:border-primary/30 transition-colors"
                                  >
                                    {product.image_url ? (
                                      <img
                                        src={product.image_url}
                                        alt={product.title}
                                        className="w-12 h-12 rounded-lg object-cover"
                                      />
                                    ) : (
                                      <div className="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center">
                                        <Backpack className="w-6 h-6 text-slate-500" />
                                      </div>
                                    )}
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm font-medium text-white truncate">{product.title}</p>
                                      <p className="text-xs text-primary font-semibold">${product.price.toFixed(2)}</p>
                                    </div>
                                    <button
                                      onClick={() => handleAddToCart(product)}
                                      className="p-2 rounded-lg bg-primary/20 hover:bg-primary/30 text-primary transition-colors"
                                      title="Add to cart"
                                    >
                                      <Plus className="w-4 h-4" />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Other Recommended Items Section */}
                          {otherRecommendedItems.length > 0 && (
                            <div>
                              <button
                                onClick={() => setOtherItemsExpanded(!otherItemsExpanded)}
                                className="w-full flex items-center justify-between mb-2"
                              >
                                <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide flex items-center gap-2">
                                  <Backpack className="w-3 h-3 text-amber-400" />
                                  Other Recommended Items
                                  <span className="text-gray-500 normal-case">({otherRecommendedItems.length})</span>
                                </h4>
                                {otherItemsExpanded ? (
                                  <ChevronDown className="w-3 h-3 text-gray-400" />
                                ) : (
                                  <ChevronRight className="w-3 h-3 text-gray-400" />
                                )}
                              </button>
                              <AnimatePresence>
                                {otherItemsExpanded && (
                                  <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                  >
                                    <div className="max-h-[200px] overflow-y-auto pr-2">
                                      <ul className="space-y-2 pl-4">
                                        {otherRecommendedItems.map((item, idx) => (
                                          <li
                                            key={idx}
                                            className="text-xs text-gray-400 flex items-start gap-2"
                                          >
                                            <span className="text-gray-600 mt-1">•</span>
                                            <span>{item}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-2 italic">
                                      These items aren't in our catalog yet, but we're working on adding them!
                                    </p>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Itinerary */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="glass rounded-2xl overflow-hidden"
            >
              <button
                onClick={() => setItineraryExpanded(!itineraryExpanded)}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                    <Map className="w-5 h-5 text-amber-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-display font-semibold text-white">Trip Itinerary</h3>
                    <p className="text-xs text-gray-400">{itinerary.length > 0 ? `${itinerary.length} day plan` : 'Day-by-day breakdown'}</p>
                  </div>
                </div>
                {itineraryExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </button>
              
              <AnimatePresence>
                {itineraryExpanded && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    exit={{ height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="p-4 pt-0 space-y-3 max-h-[400px] overflow-y-auto">
                      {itinerary.length === 0 ? (
                        <p className="text-sm text-gray-400 text-center py-4">
                          Your trip itinerary will appear here
                        </p>
                      ) : (
                        itinerary.map((day) => (
                          <div
                            key={day.day}
                            className="p-3 bg-white/5 rounded-xl border border-white/10"
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center">
                                <span className="text-xs font-bold text-amber-400">{day.day}</span>
                              </div>
                              <h4 className="text-sm font-semibold text-white">{day.title}</h4>
                            </div>
                            <ul className="space-y-1 ml-8">
                              {day.activities.map((activity, idx) => (
                                <li key={idx} className="text-xs text-gray-300 flex items-start gap-2">
                                  {idx === 0 ? (
                                    <Sun className="w-3 h-3 mt-0.5 text-amber-400 flex-shrink-0" />
                                  ) : idx === day.activities.length - 1 ? (
                                    <Moon className="w-3 h-3 mt-0.5 text-blue-400 flex-shrink-0" />
                                  ) : (
                                    <span className="w-3 h-3 flex items-center justify-center text-gray-500">•</span>
                                  )}
                                  <span>{activity}</span>
                                </li>
                              ))}
                            </ul>
                            {day.weather && (
                              <div className="mt-2 ml-8 flex items-center gap-1 text-xs text-gray-400">
                                <Thermometer className="w-3 h-3" />
                                {day.weather}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}
