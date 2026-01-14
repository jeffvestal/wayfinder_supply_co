import { useState, useRef, useEffect } from 'react'
import { ChatMessage, UserId, ThoughtTraceEvent, SuggestedProduct, ItineraryDay } from '../types'
import { api, StreamEvent } from '../lib/api'
import { getToolStatusMessage } from '../lib/constants'
import { ItineraryModal } from './ItineraryModal'
import { 
  Send, Loader2, Calendar, Mountain, ChevronDown, ChevronRight,
  Plus, Compass, Backpack, CheckCircle2, Clock,
  Tent, Map, RefreshCw
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface TripPlannerProps {
  userId: UserId
  initialMessage?: string
  onInitialMessageSent?: () => void
  // Persisted state from props
  messages: ChatMessage[]
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  tripContext: { destination: string; dates: string; activity: string }
  setTripContext: React.Dispatch<React.SetStateAction<{ destination: string; dates: string; activity: string }>>
  originalContext: { destination: string; dates: string; activity: string }
  setOriginalContext: React.Dispatch<React.SetStateAction<{ destination: string; dates: string; activity: string }>>
  suggestedProducts: SuggestedProduct[]
  setSuggestedProducts: React.Dispatch<React.SetStateAction<SuggestedProduct[]>>
  otherRecommendedItems: string[]
  setOtherRecommendedItems: React.Dispatch<React.SetStateAction<string[]>>
  itinerary: ItineraryDay[]
  setItinerary: React.Dispatch<React.SetStateAction<ItineraryDay[]>>
  messageTraces: Record<string, ThoughtTraceEvent[]>
  setMessageTraces: React.Dispatch<React.SetStateAction<Record<string, ThoughtTraceEvent[]>>>
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
      
      if (hasBrand) {
        if (!catalogProducts.includes(item)) catalogProducts.push(item)
      } else {
        if (!otherItems.includes(item)) otherItems.push(item)
      }
    }
  }
  
  return { catalogProducts, otherItems, gearSearchTerms }
}

export function TripPlanner({ 
  userId, 
  initialMessage, 
  onInitialMessageSent,
  messages,
  setMessages,
  tripContext,
  setTripContext: _setTripContext,
  originalContext: _originalContext,
  setOriginalContext: _setOriginalContext,
  suggestedProducts,
  setSuggestedProducts,
  otherRecommendedItems,
  setOtherRecommendedItems,
  itinerary,
  setItinerary: _setItinerary,
  messageTraces,
  setMessageTraces
}: TripPlannerProps) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [stepsExpanded, setStepsExpanded] = useState<Record<string, boolean>>({})
  const [isItineraryOpen, setIsItineraryOpen] = useState(false)
  const [addingToCart, setAddingToCart] = useState<string | null>(null)
  const [justAddedToCart, setJustAddedToCart] = useState<string | null>(null)
  const [searchingGear, setSearchingGear] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialMessageSentRef = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Handle initial message if provided
  useEffect(() => {
    if (initialMessage && !initialMessageSentRef.current) {
      initialMessageSentRef.current = true
      sendMessage(initialMessage)
      if (onInitialMessageSent) onInitialMessageSent()
    }
  }, [initialMessage])

  const handleAddToCart = async (product: SuggestedProduct) => {
    try {
      setAddingToCart(product.id)
      await api.addToCart(userId, product.id)
      
      // Visual feedback
      setJustAddedToCart(product.id)
      setTimeout(() => setJustAddedToCart(null), 2000)
    } catch (error) {
      console.error('Failed to add to cart:', error)
    } finally {
      setAddingToCart(null)
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    }

    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage, assistantMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Check if the trip-planner-agent exists first
      const agentExists = await api.checkAgentExists('trip-planner-agent')
      
      if (!agentExists) {
        // Agent not built yet - show helpful message
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessageId ? { 
            ...msg, 
            content: `## 🏗️ Trip Planner Agent Not Yet Built

The **Trip Planner** feature requires the \`trip-planner-agent\` to be created.

### To enable this feature:
1. Complete **Challenge 4: Build an Agent** in the workshop
2. Create the \`trip-planner-agent\` with the required tools
3. Return here to plan your adventure!

### In the meantime:
- Browse our **Store** for outdoor gear
- Use the **Search** panel to ask questions about products
- The search assistant (\`wayfinder-search-agent\`) is ready to help!

*This is the feature you'll build in Challenge 4 - it orchestrates multiple tools to create personalized trip plans.*`
          } : msg
        ))
        return
      }

      let fullContent = ''
      
      // Use the generic streamChat with the trip-planner-agent ID
      await api.streamChat(content, userId, (event: StreamEvent) => {
        if (event.type === 'content' || event.type === 'message_chunk') {
          const chunk = event.data?.text_chunk || event.data || ''
          fullContent += chunk
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId ? { ...msg, content: fullContent } : msg
          ))
        } else if (event.type === 'message_complete') {
          fullContent = event.data?.message_content || fullContent
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId ? { ...msg, content: fullContent } : msg
          ))
        } else if (event.type === 'error') {
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId ? { 
              ...msg, 
              content: `⚠️ Error: ${event.data?.error || 'Unknown error occurred'}` 
            } : msg
          ))
        } else {
          // Store all other events (reasoning, tool_call, tool_result) in traces
          const traceEvent: ThoughtTraceEvent = {
            event: event.type,
            data: event.data,
            timestamp: new Date()
          }
          setMessageTraces(prev => {
            const currentTraces = prev[assistantMessageId] || []
            return {
              ...prev,
              [assistantMessageId]: [...currentTraces, traceEvent]
            }
          })
        }
      }, 'trip-planner-agent')

      // Once complete, parse for context, itinerary, and products
      const { catalogProducts, otherItems, gearSearchTerms } = parseProductsFromResponse(fullContent)
      
      if (otherItems.length > 0) {
        setOtherRecommendedItems(otherItems)
      }

      // If we found catalog products or gear search terms, fetch them
      if (catalogProducts.length > 0 || gearSearchTerms.length > 0) {
        setSearchingGear(true)
        try {
          // 1. First search for specific brand products mentioned
          const foundProducts: SuggestedProduct[] = []
          
          for (const productName of catalogProducts) {
            const results = await api.searchProducts(productName, 1)
            if (results.products && results.products.length > 0) {
              const p = results.products[0]
              if (!foundProducts.find(fp => fp.id === p.id)) {
                foundProducts.push({
                  id: p.id,
                  title: p.title,
                  price: p.price,
                  image_url: p.image_url,
                  reason: 'Highly recommended for your trip'
                })
              }
            }
          }

          // 2. Then search for gear categories if we don't have enough products
          if (foundProducts.length < 4 && gearSearchTerms.length > 0) {
            for (const term of gearSearchTerms.slice(0, 3)) {
              const results = await api.searchProducts(term, 2)
              if (results.products) {
                for (const p of results.products) {
                  if (!foundProducts.find(fp => fp.id === p.id)) {
                    foundProducts.push({
                      id: p.id,
                      title: p.title,
                      price: p.price,
                      image_url: p.image_url,
                      reason: `Perfect ${term} for your activity`
                    })
                  }
                }
              }
            }
          }
    
    if (foundProducts.length > 0) {
            setSuggestedProducts(foundProducts)
          }
        } catch (err) {
          console.error('Failed to search products:', err)
        } finally {
          setSearchingGear(false)
        }
      }

    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId ? { ...msg, content: 'I apologize, but I encountered an error. Please try again.' } : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const toggleSteps = (messageId: string) => {
    setStepsExpanded(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }))
  }

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] bg-slate-950">
      {/* Trip Header Context */}
      <div className="bg-slate-900 border-b border-white/10 p-4">
        <div className="max-w-5xl mx-auto flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <Compass className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Destination</div>
              <div className="text-sm font-medium text-white">{tripContext.destination || 'Not set'}</div>
            </div>
            </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <Calendar className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Dates</div>
              <div className="text-sm font-medium text-white">{tripContext.dates || 'Not set'}</div>
          </div>
                    </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <Mountain className="w-5 h-5 text-primary" />
                  </div>
                  <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Activity</div>
              <div className="text-sm font-medium text-white">{tripContext.activity || 'Not set'}</div>
                    </div>
          </div>
          
          <div className="ml-auto flex items-center gap-2">
            {itinerary.length > 0 && (
              <button
                onClick={() => setIsItineraryOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-lg transition-all border border-primary/30"
              >
                        <Map className="w-4 h-4" />
                <span>View Itinerary</span>
              </button>
            )}
                    </div>
                  </div>
                </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden border-r border-white/10">
          <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-6">
                <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
                  <Compass className="w-10 h-10 text-primary animate-pulse" />
                          </div>
                <div>
                  <h3 className="text-xl font-display font-bold text-white mb-2">Adventure Trip Planner</h3>
                  <p className="text-gray-400">
                    Tell me where you want to go and what you want to do. I'll help you plan the perfect trip and find the right gear.
                        </p>
                      </div>
                <div className="grid grid-cols-1 gap-2 w-full">
                  <button
                    onClick={() => setInput("Plan a 3-day backpacking trip in the Enchantments, Washington for this July")}
                    className="text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm text-gray-300"
                  >
                    "Plan a 3-day backpacking trip in the Enchantments, Washington..."
                  </button>
                        <button
                    onClick={() => setInput("I want to go car camping in Zion National Park next week with my family")}
                    className="text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm text-gray-300"
                  >
                    "I want to go car camping in Zion National Park..."
                  </button>
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Thought Trace - Moved above the bubble for assistant */}
                  {msg.role === 'assistant' && messageTraces[msg.id] && messageTraces[msg.id].length > 0 && (
                    <div className="mb-2 ml-4">
                      <button
                        onClick={() => toggleSteps(msg.id)}
                        className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300 transition-colors"
                      >
                        {stepsExpanded[msg.id] ? (
                          <ChevronDown className="w-3 h-3" />
                        ) : (
                          <ChevronRight className="w-3 h-3" />
                        )}
                        {isLoading && idx === messages.length - 1 ? (
                          <span className="flex items-center gap-1.5">
                              <Loader2 className="w-3 h-3 animate-spin text-primary" />
                            <span>{getCurrentStatus(messageTraces[msg.id], true)}</span>
                            </span>
                          ) : (
                          <span className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-3 h-3 text-green-500" />
                            <span>Completed {messageTraces[msg.id].length} steps</span>
                            </span>
                          )}
                        </button>
                        
                      {stepsExpanded[msg.id] && (
                        <div className="mt-2 space-y-1 w-full max-w-[85%]">
                          {messageTraces[msg.id].map((event, eventIdx) => (
                            <div key={eventIdx} className="text-[11px] bg-slate-900/50 border border-white/5 rounded px-2 py-1 flex items-center gap-2">
                              {event.event === 'reasoning' && <Clock className="w-3 h-3 text-blue-400" />}
                              {event.event === 'tool_call' && <RefreshCw className="w-3 h-3 text-primary animate-spin" />}
                              {event.event === 'tool_result' && <CheckCircle2 className="w-3 h-3 text-green-500" />}
                              <span className="text-gray-400">
                                {event.event === 'reasoning' ? 'Reasoning' : 
                                 event.event === 'tool_call' ? `Calling ${event.data.tool_id}` : 
                                 'Processed results'}
                                      </span>
                            </div>
                          ))}
                                    </div>
                                  )}
                                </div>
                  )}

                  <div className={`max-w-[85%] rounded-2xl p-4 ${
                    msg.role === 'user' 
                      ? 'bg-primary text-white rounded-tr-none' 
                      : 'bg-slate-900 text-gray-200 border border-white/10 rounded-tl-none'
                  }`}>
                    {msg.content ? (
                      <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" />
                        <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:0.2s]" />
                        <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
              )}
                  </div>
                </div>
              ))
              )}
            <div ref={messagesEndRef} />
            </div>

          {/* Input Area */}
          <div className="p-4 bg-slate-900/50 border-t border-white/10">
            <form 
              onSubmit={(e) => {
                e.preventDefault()
                sendMessage(input)
              }}
              className="relative"
            >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                placeholder="Where should we go next?"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-3 pr-12 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all disabled:opacity-50"
                />
                <button
                  type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-primary hover:bg-primary-dark text-white rounded-lg transition-all disabled:opacity-50"
                >
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
            </form>
          </div>
                  </div>

        {/* Recommendations Sidebar */}
        <div className="w-96 overflow-y-auto bg-slate-900/30 p-4 space-y-6 custom-scrollbar">
          {/* Suggested Gear */}
                            <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Backpack className="w-4 h-4 text-primary" />
                Recommended Gear
                              </h4>
              {searchingGear && <Loader2 className="w-3 h-3 animate-spin text-primary" />}
            </div>
            
            {suggestedProducts.length > 0 ? (
                              <div className="space-y-3">
                {suggestedProducts.map(product => (
                  <div key={product.id} className="bg-slate-900 border border-white/10 rounded-xl p-3 flex gap-3 hover:border-primary/30 transition-all group">
                    <div className="w-16 h-16 bg-white/5 rounded-lg overflow-hidden flex-shrink-0">
                                    {product.image_url ? (
                        <img src={product.image_url} alt={product.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Mountain className="w-6 h-6 text-gray-700" />
                                      </div>
                                    )}
                    </div>
                                    <div className="flex-1 min-w-0">
                      <h5 className="text-xs font-bold text-white truncate mb-1">{product.title}</h5>
                      <div className="text-xs text-primary font-bold mb-1">${product.price}</div>
                      {product.reason && (
                        <div className="text-[10px] text-gray-500 line-clamp-2 italic leading-tight">
                          {product.reason}
                        </div>
                      )}
                                    </div>
                                    <button
                                      onClick={() => handleAddToCart(product)}
                      disabled={addingToCart === product.id || justAddedToCart === product.id}
                      className={`p-2 rounded-lg transition-all duration-300 ${
                        justAddedToCart === product.id 
                          ? 'bg-green-500 scale-110 animate-pulse text-white' 
                          : 'bg-primary/20 hover:bg-primary/30 text-primary'
                      } disabled:opacity-50`}
                      title={justAddedToCart === product.id ? 'Added!' : 'Add to cart'}
                    >
                      {addingToCart === product.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : justAddedToCart === product.id ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : (
                                      <Plus className="w-4 h-4" />
                      )}
                                    </button>
                                  </div>
                                ))}
                              </div>
            ) : (
              <div className="bg-slate-900/50 border border-dashed border-white/10 rounded-xl p-8 text-center">
                <Tent className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                <p className="text-xs text-gray-500">I'll suggest relevant gear as we plan your adventure.</p>
                            </div>
                          )}
          </div>
                          
          {/* Other Items Checklist */}
                          {otherRecommendedItems.length > 0 && (
            <div className="pt-4 border-t border-white/10">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                Essential Checklist
                                </h4>
              <div className="space-y-2">
                                        {otherRecommendedItems.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors">
                    <input type="checkbox" className="mt-1 rounded border-white/10 bg-slate-950 text-primary focus:ring-0 focus:ring-offset-0" />
                    <span className="text-xs text-gray-300 leading-tight">{item}</span>
                                    </div>
                ))}
                              </div>
                          </div>
          )}
        </div>
      </div>
      
      <ItineraryModal
        isOpen={isItineraryOpen}
        onClose={() => setIsItineraryOpen(false)}
        itinerary={itinerary}
      />
    </div>
  )
}
