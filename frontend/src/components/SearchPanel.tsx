import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Product, UserId, SettingsStatus } from '../types'
import { api, StreamEvent } from '../lib/api'
import { X, Search, Send, Loader2, MessageSquare, Zap, BookOpen, Target, Plus, ImagePlus, ChevronDown, ChevronRight, Eye } from 'lucide-react'
import { resizeImage, MAX_FILE_SIZE_MB } from '../lib/imageUtils'
import { ProductDetailModal } from './ProductDetailModal'
import { ChatMode } from './search/ChatMode'
import { SearchMode } from './search/SearchMode'
import { DemoMode } from './search/DemoMode'
import { NarrationBanner } from './NarrationBanner'
import { NARRATION_MESSAGES } from '../lib/constants'
import { 
  SearchMode as SearchModeType, 
  ExtendedChatMessage, 
  AgentStep, 
  DemoQueryType,
  DEMO_QUERIES 
} from './search/types'

interface SearchPanelProps {
  isOpen: boolean
  onClose: () => void
  userId: UserId
  initialMessage?: string
  onInitialMessageSent?: () => void
  onOpenTripPlanner?: () => void
  startInDemoMode?: boolean
  onDemoModeStarted?: () => void
  narrationMode?: boolean
  // Persisted state from props
  messages: ExtendedChatMessage[]
  setMessages: React.Dispatch<React.SetStateAction<ExtendedChatMessage[]>>
  mode: SearchModeType
  setMode: React.Dispatch<React.SetStateAction<SearchModeType>>
  stepsExpanded: Record<string, boolean>
  setStepsExpanded: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
  expandedSteps: Set<string>
  setExpandedSteps: React.Dispatch<React.SetStateAction<Set<string>>>
  personalizationEnabled: boolean
  setPersonalizationEnabled: React.Dispatch<React.SetStateAction<boolean>>
  settingsStatus?: SettingsStatus
}

export function SearchPanel({ 
  isOpen, 
  onClose, 
  userId, 
  initialMessage, 
  onInitialMessageSent, 
  onOpenTripPlanner: _onOpenTripPlanner, 
  startInDemoMode, 
  onDemoModeStarted, 
  narrationMode = false,
  messages,
  setMessages,
  mode,
  setMode,
  stepsExpanded,
  setStepsExpanded,
  expandedSteps,
  setExpandedSteps,
  personalizationEnabled,
  setPersonalizationEnabled,
  settingsStatus
}: SearchPanelProps) {
  // UI State
  const [panelWidth, setPanelWidth] = useState(50)
  const [isDragging, setIsDragging] = useState(false)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [lastQuery, setLastQuery] = useState('')
  
  // Search state
  const [searchResults, setSearchResults] = useState<Product[]>([])
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [isProductModalOpen, setIsProductModalOpen] = useState(false)
  const [visionAnalysis, setVisionAnalysis] = useState<any>(null)
  const [visionCardExpanded, setVisionCardExpanded] = useState(false)
  const [visionSourceImage, setVisionSourceImage] = useState<string | null>(null)
  
  // Demo state
  const [isDemoRunning, setIsDemoRunning] = useState(false)
  const [demoStep, setDemoStep] = useState<'intro' | 'lexical' | 'hybrid' | 'agentic' | 'complete'>('intro')
  const [selectedDemoQuery, setSelectedDemoQuery] = useState<DemoQueryType | null>(null)
  const [demoLexicalResults, setDemoLexicalResults] = useState<Product[]>([])
  const [demoHybridResults, setDemoHybridResults] = useState<Product[]>([])
  const [demoAgenticMessage, setDemoAgenticMessage] = useState<ExtendedChatMessage | null>(null)
  const [demoAgenticProducts, setDemoAgenticProducts] = useState<Product[]>([])
  const [demoLexicalQuery, setDemoLexicalQuery] = useState<any>(null)
  const [demoLexicalRawHits, setDemoLexicalRawHits] = useState<any[]>([])
  const [demoHybridQuery, setDemoHybridQuery] = useState<any>(null)
  const [demoHybridRawHits, setDemoHybridRawHits] = useState<any[]>([])
  const [queryExpanded, setQueryExpanded] = useState<{ lexical: boolean; hybrid: boolean }>({ lexical: false, hybrid: false })
  const [addingToCart, setAddingToCart] = useState<string | null>(null)
  const [justAddedToCart, setJustAddedToCart] = useState<string | null>(null)
  
  // Narration state
  const [currentNarration, setCurrentNarration] = useState<string | null>(null)
  
  // Image upload state (vision search in chat mode)
  const [pendingImage, setPendingImage] = useState<string | null>(null)
  const [pendingImagePreview, setPendingImagePreview] = useState<string | null>(null)
  const visionEnabled = settingsStatus?.jina_vlm === 'configured_ui' || settingsStatus?.jina_vlm === 'configured_env'

  // Refs
  const dragStartX = useRef(0)
  const dragStartWidth = useRef(50)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialMessageSentRef = useRef(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Extract product IDs from agent tool results (Agent Builder returns "resource" format)
  const extractProductIdsFromSteps = (steps: AgentStep[]): string[] => {
    const productIds: string[] = []
    
    for (const step of steps) {
      if (step.type === 'tool_call' && step.results) {
        // #region agent log
        console.warn('[DBG:extractProductIds] step tool_id=', step.tool_id, 'results count=', step.results?.length, 'results=', JSON.stringify(step.results)?.substring(0, 500))
        // #endregion
        for (const result of step.results) {
          // #region agent log
          console.warn('[DBG:extractProductIds] result type=', typeof result, 'keys=', result && typeof result === 'object' ? Object.keys(result) : 'N/A', 'sample=', JSON.stringify(result)?.substring(0, 300))
          // #endregion

          // Check for Agent Builder "resource" format with data.reference.id
          if (result?.data?.reference?.id) {
            productIds.push(result.data.reference.id)
          }
          
          // Check for Agent Builder "resource" format with documents array
          if (result?.content) {
            try {
              const content = typeof result.content === 'string' ? JSON.parse(result.content) : result.content
              if (content.documents && Array.isArray(content.documents)) {
                for (const doc of content.documents) {
                  if (doc.id) {
                    productIds.push(doc.id)
                  }
                  if (doc._source?.id) {
                    productIds.push(doc._source.id)
                  }
                }
              }
            } catch (e) {
              // Not JSON, continue
            }
          }
          
          // Direct results array with documents
          if (Array.isArray(result)) {
            for (const item of result) {
              if (item?.id) productIds.push(item.id)
              if (item?._source?.id) productIds.push(item._source.id)
            }
          }

          // Agent Builder index_search: result has _id at top level
          if (result?._id) {
            productIds.push(result._id)
          }
          // Agent Builder index_search: result has _source with nested fields
          if (result?._source) {
            if (result._source.id) productIds.push(result._source.id)
          }
          // Agent Builder: result has reference._id
          if (result?.reference?._id) {
            productIds.push(result.reference._id)
          }
          if (result?.reference?.id) {
            productIds.push(result.reference.id)
          }
        }
      }
    }
    
    // #region agent log
    console.warn('[DBG:extractProductIds] final productIds=', productIds)
    // #endregion
    return [...new Set(productIds)].slice(0, 3) // Unique, max 3
  }
  
  // Fetch product details from IDs
  const fetchProductsFromIds = async (productIds: string[]): Promise<Product[]> => {
    const products: Product[] = []
    for (const id of productIds) {
      try {
        const product = await api.getProduct(id)
        if (product) products.push(product)
      } catch (e) {
        console.error('Failed to fetch product:', id, e)
      }
    }
    return products
  }
  
  // Combined extraction helper
  const extractAndFetchProducts = async (steps: AgentStep[]) => {
    const productIds = extractProductIdsFromSteps(steps)
    if (productIds.length > 0) {
      const products = await fetchProductsFromIds(productIds)
      if (products.length > 0) {
        setDemoAgenticProducts(products)
      }
    }
  }

  // Add to cart handler for demo products
  const handleAddToCart = async (product: Product) => {
    setAddingToCart(product.id)
    try {
      await api.addToCart(userId, product.id)
      setJustAddedToCart(product.id)
      setTimeout(() => setJustAddedToCart(null), 1500)
    } catch (error) {
      console.error('Failed to add to cart:', error)
    } finally {
      setAddingToCart(null)
    }
  }

  // Extract products when demo agentic message completes
  useEffect(() => {
    const extractProducts = async () => {
      if (demoAgenticMessage?.status === 'complete' && demoAgenticMessage?.steps) {
        const productIds = extractProductIdsFromSteps(demoAgenticMessage.steps)
        if (productIds.length > 0) {
          const products = await fetchProductsFromIds(productIds)
          if (products.length > 0) {
            setDemoAgenticProducts(products)
          }
        }
      }
    }
    extractProducts()
  }, [demoAgenticMessage?.status, demoAgenticMessage?.steps])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, searchResults, demoLexicalResults, demoHybridResults, demoAgenticMessage])

  // Handle initial message when panel opens with context
  useEffect(() => {
    if (isOpen && initialMessage && !initialMessageSentRef.current && !isLoading) {
      initialMessageSentRef.current = true
      setMode('chat')
      sendMessage(initialMessage)
      onInitialMessageSent?.()
    }
  }, [isOpen, initialMessage])

  // Reset the ref when panel closes
  useEffect(() => {
    if (!isOpen) {
      initialMessageSentRef.current = false
      setIsDemoRunning(false)
      setDemoStep('intro')
      setSelectedDemoQuery(null)
      setDemoLexicalResults([])
      setDemoHybridResults([])
      setDemoAgenticMessage(null)
      setDemoAgenticProducts([])
      setDemoLexicalQuery(null)
      setDemoLexicalRawHits([])
      setDemoHybridQuery(null)
      setDemoHybridRawHits([])
      setQueryExpanded({ lexical: false, hybrid: false })
    }
  }, [isOpen])

  // Auto-enable demo mode when panel opens with startInDemoMode prop
  useEffect(() => {
    if (isOpen && startInDemoMode && !isDemoRunning) {
      setIsDemoRunning(true)
      onDemoModeStarted?.() // Signal parent to reset flag
    }
  }, [isOpen, startInDemoMode, isDemoRunning, onDemoModeStarted])

  // Drag listeners
  useEffect(() => {
    if (isDragging) {
      const handleMouseMove = (e: MouseEvent) => {
        const deltaX = dragStartX.current - e.clientX
        const newWidth = Math.min(90, Math.max(30, dragStartWidth.current + (deltaX / window.innerWidth) * 100))
        setPanelWidth(newWidth)
      }
      const handleMouseUp = () => {
        setIsDragging(false)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
      
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging])

  const handleDragStart = (e: React.MouseEvent) => {
    setIsDragging(true)
    dragStartX.current = e.clientX
    dragStartWidth.current = panelWidth
    document.body.style.cursor = 'ew-resize'
    document.body.style.userSelect = 'none'
  }

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepId)) {
        newSet.delete(stepId)
      } else {
        newSet.add(stepId)
      }
      return newSet
    })
  }

  const toggleStepsExpanded = (messageId: string) => {
    setStepsExpanded(prev => ({ ...prev, [messageId]: !prev[messageId] }))
  }

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    // Reset the input so selecting the same file again triggers onChange
    e.target.value = ''

    // Validate type
    if (!file.type.match(/^image\/(jpeg|png|webp)$/)) {
      alert('Please select a JPEG, PNG, or WebP image.')
      return
    }
    // Validate size
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      alert(`Image must be smaller than ${MAX_FILE_SIZE_MB}MB.`)
      return
    }

    try {
      const base64 = await resizeImage(file)
      setPendingImage(base64)
      setPendingImagePreview(`data:image/jpeg;base64,${base64}`)
    } catch (err) {
      console.error('Failed to process image:', err)
    }
  }

  const clearPendingImage = () => {
    setPendingImage(null)
    setPendingImagePreview(null)
  }

  const sendMessage = async (messageText: string) => {
    // #region agent log
    console.warn('[DBG:sendMessage] entry', { hasPendingImage: !!pendingImage, pendingImageLen: pendingImage?.length || 0, messageText: messageText?.substring(0, 50), isLoading, mode, visionEnabled })
    // #endregion
    // Allow sending if there's text OR a pending image
    if ((!messageText.trim() && !pendingImage) || isLoading) return

    // Capture and clear pending image before async work
    const imageToSend = pendingImage
    const imagePreviewToSend = pendingImagePreview
    // #region agent log
    console.warn('[DBG:sendMessage] captured image', { hasImageToSend: !!imageToSend, imageToSendLen: imageToSend?.length || 0 })
    // #endregion
    clearPendingImage()

    if (messageText.trim()) {
      setLastQuery(messageText.trim())
    }
    
    const userMessage: ExtendedChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText.trim() || (imageToSend ? 'Find similar products' : ''),
      timestamp: new Date(),
      image_url: imagePreviewToSend || undefined,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: ExtendedChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      steps: [],
      status: 'thinking'
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      let currentSteps: AgentStep[] = []
      let currentContent = ''
      
      await api.streamChat(messageText || '', userId, (event: StreamEvent) => {
        const { type, data } = event
        // #region agent log
        console.warn('[DBG:streamChat] SSE event', { type, dataKeys: data ? Object.keys(data) : null })
        // #endregion

        switch (type) {
          case 'vision_analysis': {
            // Add vision analysis as a reasoning step in the collapsible thought trace
            const visionDesc = data.description || (typeof data === 'string' ? data : '')
            const productType = data.product_type || ''
            const category = data.category || ''
            const structuredInfo = productType
              ? `Product: ${productType}${category ? ` | Category: ${category}` : ''}\n${visionDesc}`
              : visionDesc
            currentSteps = [...currentSteps, {
              type: 'reasoning',
              reasoning: `Image Analysis (Jina VLM): ${structuredInfo}`
            }, {
              type: 'reasoning',
              reasoning: `Raw Jina VLM Response:\n${JSON.stringify(data, null, 2)}`
            }]
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, steps: currentSteps, status: 'thinking', vision_analysis: data }
                : msg
            ))
            break
          }

          case 'vision_error': {
            // Vision analysis failed (e.g. Jina cold start 503)
            const errorMsg = data.error || 'Image analysis failed'
            currentSteps = [...currentSteps, {
              type: 'reasoning',
              reasoning: `⚠️ Vision Error: ${errorMsg}`
            }]
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, steps: currentSteps, status: 'thinking' }
                : msg
            ))
            break
          }

          case 'reasoning':
            currentSteps = [...currentSteps, { type: 'reasoning', reasoning: data.reasoning }]
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: currentContent, steps: currentSteps, status: 'thinking' }
                : msg
            ))
            break

          case 'tool_call':
            if (!data.tool_id) break
            const existingToolCall = currentSteps.find(s => s.tool_call_id === data.tool_call_id)
            if (!existingToolCall && data.params && Object.keys(data.params).length > 0) {
              currentSteps = [...currentSteps, {
                type: 'tool_call',
                tool_call_id: data.tool_call_id,
                tool_id: data.tool_id,
                params: data.params,
                results: []
              }]
              setMessages(prev => prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: currentContent, steps: currentSteps, status: 'working' }
                  : msg
              ))
            }
            break

          case 'tool_result':
            const toolCallId = data.tool_call_id
            currentSteps = currentSteps.map(step => 
              step.tool_call_id === toolCallId 
                ? { ...step, results: data.results }
                : step
            )
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: currentContent, steps: currentSteps, status: 'working' }
                : msg
            ))
            break

          case 'message_chunk':
            currentContent += data.text_chunk || ''
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: currentContent, steps: currentSteps, status: 'typing' }
                : msg
            ))
            break

          case 'message_complete':
          case 'completion':
            currentContent = data.message_content || currentContent
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: currentContent, steps: currentSteps, status: 'complete' }
                : msg
            ))
            // Extract and fetch products from tool results
            const productIds = extractProductIdsFromSteps(currentSteps)
            if (productIds.length > 0) {
              fetchProductsFromIds(productIds).then(products => {
                if (products.length > 0) {
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, products }
                      : msg
                  ))
                }
              })
            }
            break

          case 'error':
            currentContent = `Error: ${data.error}`
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: currentContent, steps: currentSteps, status: 'complete' }
                : msg
            ))
            break
        }
      }, undefined, imageToSend || undefined)
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? { ...msg, content: `Error: ${error instanceof Error ? error.message : 'Failed'}`, status: 'complete' }
          : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (mode === 'chat') {
      sendMessage(input)
    } else if (mode === 'hybrid' && pendingImage) {
      // Hybrid search with image — pass pending image for vision analysis
      const imageToSend = pendingImage
      const imagePreview = pendingImagePreview
      clearPendingImage()
      setVisionSourceImage(imagePreview)
      handleSearch(input, undefined, imageToSend)
    } else {
      handleSearch(input)
    }
  }

  const handleSearch = async (query: string, targetMode?: 'hybrid' | 'lexical', imageBase64?: string) => {
    if ((!query.trim() && !imageBase64) || isLoading) return

    const searchMode = targetMode || mode
    
    if (query.trim()) setLastQuery(query.trim())
    setIsLoading(true)
    setInput('')
    setVisionAnalysis(null)
    if (!imageBase64) setVisionSourceImage(null)
    const personalizedUserId = personalizationEnabled ? userId : undefined

    // Show narration banner
    if (narrationMode) {
      const narrationKey = searchMode === 'hybrid' ? 'hybrid_search' : 'lexical_search'
      setCurrentNarration(narrationKey)
      setTimeout(() => setCurrentNarration(null), 3000)
    }

    try {
      const results = searchMode === 'hybrid' 
        ? await api.hybridSearch(query, 10, personalizedUserId, imageBase64)
        : await api.lexicalSearch(query, 10, personalizedUserId)
      setSearchResults(results.products)

      // Store vision analysis if present (from image-enhanced hybrid search)
      if (results.vision_analysis) {
        setVisionAnalysis(results.vision_analysis)
        setVisionCardExpanded(true)
      }

      // Show vision error if image analysis failed (e.g. Jina cold start)
      if (results.vision_error) {
        setVisionAnalysis({ error: results.vision_error })
        setVisionCardExpanded(true)
      }
      
      // Show personalized narration if applicable
      if (narrationMode && personalizationEnabled) {
        setCurrentNarration('personalized')
        setTimeout(() => setCurrentNarration(null), 3000)
      }
    } catch (error: any) {
      console.error('Search error:', error)
      // If the error is a 503 from vision service warming up, show a helpful message
      if (imageBase64 && error?.message?.includes('503')) {
        setVisionAnalysis({ error: 'Image analysis service is warming up — please try again in 30-60 seconds' })
        setVisionCardExpanded(true)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleProductClick = (product: Product) => {
    setSelectedProduct(product)
    setIsProductModalOpen(true)
  }

  // Demo user ID - user_member (Alex Hiker) has clickstream data for personalization
  const DEMO_USER_ID = 'user_member' as UserId

  // Demo functionality
  const runDemo = async (queryType: DemoQueryType) => {
    setSelectedDemoQuery(queryType)
    setIsDemoRunning(true)
    setDemoStep('lexical')
    setDemoLexicalResults([])
    setDemoHybridResults([])
    setDemoAgenticMessage(null)
    setDemoAgenticProducts([])
    setDemoLexicalQuery(null)
    setDemoLexicalRawHits([])
    setDemoHybridQuery(null)
    setDemoHybridRawHits([])
    setQueryExpanded({ lexical: false, hybrid: false })
    setMessages([])
    setSearchResults([])
    
    const demoQuery = DEMO_QUERIES[queryType].query
    const personalizedUserId = personalizationEnabled ? DEMO_USER_ID : undefined
    
      setIsLoading(true)
      try {
      const results = await api.lexicalSearch(demoQuery, 10, personalizedUserId)
        setDemoLexicalResults(results.products)
        setDemoLexicalQuery(results.es_query || null)
        setDemoLexicalRawHits(results.raw_hits || [])
      } catch (error) {
        console.error('Demo lexical search failed:', error)
      } finally {
        setIsLoading(false)
      }
  }

  const advanceDemo = async () => {
    if (isLoading || !selectedDemoQuery) return

    const demoQuery = DEMO_QUERIES[selectedDemoQuery].query
    const personalizedUserId = personalizationEnabled ? DEMO_USER_ID : undefined
    const chatUserId = personalizationEnabled ? DEMO_USER_ID : 'user_new'
    
    if (demoStep === 'lexical') {
      setDemoStep('hybrid')
      setIsLoading(true)
      
      // Show narration
      if (narrationMode) {
        setCurrentNarration('hybrid_search')
        setTimeout(() => setCurrentNarration(null), 3000)
      }
      
      try {
        const results = await api.hybridSearch(demoQuery, 10, personalizedUserId)
        setDemoHybridResults(results.products)
        setDemoHybridQuery(results.es_query || null)
        setDemoHybridRawHits(results.raw_hits || [])
      } catch (error) {
        console.error('Demo hybrid search failed:', error)
      } finally {
        setIsLoading(false)
      }
    } else if (demoStep === 'hybrid') {
      setDemoStep('agentic')
      setIsLoading(true)
      
      // Show narration
      if (narrationMode) {
        setCurrentNarration('agent_start')
        setTimeout(() => setCurrentNarration(null), 3000)
      }
      
      const assistantMessageId = Date.now().toString()
      const assistantMessage: ExtendedChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        steps: [],
        status: 'thinking'
      }
      setDemoAgenticMessage(assistantMessage)

      try {
        let currentSteps: AgentStep[] = []
        let currentContent = ''

        await api.streamChat(demoQuery, chatUserId, (event: StreamEvent) => {
          const { type, data } = event

          switch (type) {
            case 'reasoning':
              currentSteps = [...currentSteps, { type: 'reasoning', reasoning: data.reasoning }]
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'thinking' } : null)
              break

            case 'tool_call':
              if (!data.tool_id) break
              const existingToolCall = currentSteps.find(s => s.tool_call_id === data.tool_call_id)
              if (!existingToolCall && data.params && Object.keys(data.params).length > 0) {
                currentSteps = [...currentSteps, {
                  type: 'tool_call',
                  tool_call_id: data.tool_call_id,
                  tool_id: data.tool_id,
                  params: data.params,
                  results: []
                }]
                setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'working' } : null)
              }
              break

            case 'tool_result':
              const toolCallId = data.tool_call_id
              currentSteps = currentSteps.map(step => 
                step.tool_call_id === toolCallId 
                  ? { ...step, results: data.results }
                  : step
              )
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'working' } : null)
              break

            case 'message_chunk':
              currentContent += data.text_chunk || ''
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'typing' } : null)
              break

            case 'message_complete':
            case 'completion':
              currentContent = data.message_content || currentContent
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'complete' } : null)
              extractAndFetchProducts(currentSteps)
              break

            case 'error':
              currentContent = `Error: ${data.error}`
              setDemoAgenticMessage(prev => prev ? { ...prev, content: currentContent, steps: currentSteps, status: 'complete' } : null)
              break
          }
        })
        extractAndFetchProducts(currentSteps)
      } catch (error) {
        console.error('Demo agentic search failed:', error)
        setDemoAgenticMessage(prev => prev ? { ...prev, content: `Error: ${error instanceof Error ? error.message : 'Failed'}`, status: 'complete' } : null)
      } finally {
        setIsLoading(false)
      }
    } else if (demoStep === 'agentic') {
      setDemoStep('complete')
      setIsDemoRunning(false)
    }
  }

  const getModeBgClass = (currentMode: SearchModeType) => {
    switch (currentMode) {
      case 'chat': return 'bg-slate-900'
      case 'hybrid': return 'bg-gradient-to-br from-slate-900 to-cyan-950/30'
      case 'lexical': return 'bg-gradient-to-br from-slate-900 to-amber-950/30'
      default: return 'bg-slate-900'
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed inset-y-0 right-0 z-50 flex"
            style={{ width: `${panelWidth}vw` }}
          >
            {/* Draggable Resizer */}
            <div
              onMouseDown={handleDragStart}
              className="w-2 bg-slate-700/50 hover:bg-primary/50 cursor-ew-resize absolute left-0 top-0 bottom-0 z-10 transition-colors"
            />

            {/* Panel Content */}
            <div className={`flex flex-col w-full ${getModeBgClass(mode)} shadow-2xl border-l border-slate-700`}>
              {/* Narration Banner */}
              {narrationMode && currentNarration && NARRATION_MESSAGES[currentNarration] && (
                <NarrationBanner
                  message={NARRATION_MESSAGES[currentNarration].message}
                  icon={NARRATION_MESSAGES[currentNarration].icon}
                  visible={true}
                />
              )}
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-slate-700">
                <h2 className="text-xl font-display font-bold text-white">Search & Chat</h2>
                <div className="flex items-center gap-2">
                  {/* New Session Button - shows when there's content */}
                  {(messages.length > 0 || searchResults.length > 0) && !isDemoRunning && (
                    <button
                      onClick={() => {
                        setMessages([])
                        setSearchResults([])
                        setInput('')
                        setLastQuery('')
                        setIsLoading(false)
                      }}
                      className="px-3 py-1.5 text-sm bg-pink-600/20 hover:bg-pink-600/30 text-pink-400 border border-pink-600/30 rounded-lg transition-all flex items-center gap-1.5"
                    >
                      <Plus className="w-4 h-4" />
                      <span className="hidden sm:inline">New Session</span>
                    </button>
                  )}
                  {/* Personalization Toggle */}
                  <button
                    onClick={() => setPersonalizationEnabled(!personalizationEnabled)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-all flex items-center gap-1.5 ${
                      personalizationEnabled
                        ? 'bg-green-600 text-white shadow-md shadow-green-500/30'
                        : 'bg-slate-700 text-gray-400 hover:bg-slate-600'
                    }`}
                    title={personalizationEnabled ? 'Personalization ON' : 'Personalization OFF'}
                  >
                    <Target className={`w-4 h-4 ${personalizationEnabled ? 'animate-pulse' : ''}`} />
                    <span className="hidden sm:inline">{personalizationEnabled ? 'Personal' : 'Generic'}</span>
                  </button>
                  {/* Watch This Demo Button */}
                  <button
                    onClick={() => {
                      setIsDemoRunning(true)
                      setDemoStep('intro')
                      setSelectedDemoQuery(null)
                      setPersonalizationEnabled(true) // Auto-enable for the "Wow" moment
                    }}
                    disabled={isDemoRunning}
                    className="px-3 py-1.5 text-sm bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg transition-colors flex items-center gap-1.5 text-white"
                  >
                    <Zap className="w-4 h-4" /> Watch This
                  </button>
                  <button
                    onClick={onClose}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-300" />
                  </button>
                </div>
              </div>

              {/* Mode Selector */}
              {!isDemoRunning && (
                <div className="p-4 border-b border-slate-700 space-y-2">
                  <div className="flex bg-slate-800 rounded-full p-1">
                    <button
                      onClick={() => { 
                        const prevMode = mode
                        setMode('chat')
                        setSearchResults([])
                        if (lastQuery && prevMode !== 'chat') {
                          setTimeout(() => sendMessage(lastQuery), 100)
                        }
                      }}
                      className={`flex-1 py-2 px-4 rounded-full text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                        mode === 'chat' ? 'bg-primary text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <MessageSquare className="w-4 h-4" /> Chat
                    </button>
                    <button
                      onClick={() => { 
                        const prevMode = mode
                        setMode('hybrid')
                        setMessages([])
                        if (lastQuery && prevMode !== 'hybrid') {
                          setTimeout(() => handleSearch(lastQuery, 'hybrid'), 100)
                        }
                      }}
                      className={`flex-1 py-2 px-4 rounded-full text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                        mode === 'hybrid' ? 'bg-cyan-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <Search className="w-4 h-4" /> Hybrid
                    </button>
                    <button
                      onClick={() => { 
                        const prevMode = mode
                        setMode('lexical')
                        setMessages([])
                        if (lastQuery && prevMode !== 'lexical') {
                          setTimeout(() => handleSearch(lastQuery, 'lexical'), 100)
                        }
                      }}
                      className={`flex-1 py-2 px-4 rounded-full text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                        mode === 'lexical' ? 'bg-amber-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <BookOpen className="w-4 h-4" /> Lexical
                    </button>
                  </div>
                </div>
              )}

              {/* Content Area */}
              <div className="flex-1 overflow-y-auto p-4">
                {isDemoRunning ? (
                  <DemoMode
                    userId={DEMO_USER_ID} // Always show Alex Hiker during demo
                    isLoading={isLoading}
                    personalizationEnabled={personalizationEnabled}
                    demoStep={demoStep}
                    selectedDemoQuery={selectedDemoQuery}
                    demoLexicalResults={demoLexicalResults}
                    demoLexicalQuery={demoLexicalQuery}
                    demoLexicalRawHits={demoLexicalRawHits}
                    demoHybridResults={demoHybridResults}
                    demoHybridQuery={demoHybridQuery}
                    demoHybridRawHits={demoHybridRawHits}
                    demoAgenticMessage={demoAgenticMessage}
                    demoAgenticProducts={demoAgenticProducts}
                    queryExpanded={queryExpanded}
                    stepsExpanded={stepsExpanded}
                    expandedSteps={expandedSteps}
                    addingToCart={addingToCart}
                    justAddedToCart={justAddedToCart}
                    onRunDemo={runDemo}
                    onAdvanceDemo={advanceDemo}
                    onProductClick={handleProductClick}
                    onAddToCart={handleAddToCart}
                    onToggleQueryExpanded={(type) => setQueryExpanded(prev => ({ ...prev, [type]: !prev[type] }))}
                    onToggleStepsExpanded={toggleStepsExpanded}
                    onToggleStep={toggleStep}
                    onExitDemo={() => {
                      setIsDemoRunning(false)
                      setSelectedDemoQuery(null)
                      setDemoStep('intro')
                    }}
                    onStartChat={() => {
                      setIsDemoRunning(false)
                      setSelectedDemoQuery(null)
                      setMode('chat')
                    }}
                  />
                ) : (
                  <>
                    {/* Chat Mode */}
                    {mode === 'chat' && (
                      <ChatMode
                        messages={messages}
                        isLoading={isLoading}
                        stepsExpanded={stepsExpanded}
                        expandedSteps={expandedSteps}
                        onToggleStepsExpanded={toggleStepsExpanded}
                        onToggleStep={toggleStep}
                        messagesEndRef={messagesEndRef}
                        userId={userId}
                        onProductClick={handleProductClick}
                      />
                    )}

                    {/* Hybrid/Lexical Mode */}
                    {(mode === 'hybrid' || mode === 'lexical') && (
                      <>
                        {/* Vision Analysis Card - shown when image search returns structured data */}
                        {visionAnalysis && mode === 'hybrid' && (
                          <div className="mb-4">
                            <button
                              onClick={() => setVisionCardExpanded(!visionCardExpanded)}
                              className={`w-full flex items-center gap-2 px-3 py-2 ${visionAnalysis.error ? 'bg-amber-900/30 border-amber-700/40' : 'bg-purple-900/30 border-purple-700/40'} border rounded-lg text-sm ${visionAnalysis.error ? 'text-amber-300' : 'text-purple-300'} hover:bg-opacity-60 transition-colors`}
                            >
                              <Eye className={`w-4 h-4 ${visionAnalysis.error ? 'text-amber-400' : 'text-purple-400'}`} />
                              <span className="font-medium">{visionAnalysis.error ? 'Vision Error' : 'Vision Analysis'}</span>
                              {!visionAnalysis.error && visionAnalysis.product_type && (
                                <span className="text-purple-400/70 ml-1">— {visionAnalysis.product_type}</span>
                              )}
                              <span className="ml-auto">
                                {visionCardExpanded
                                  ? <ChevronDown className="w-4 h-4" />
                                  : <ChevronRight className="w-4 h-4" />
                                }
                              </span>
                            </button>
                            {visionCardExpanded && (
                              <div className={`mt-1 px-3 py-2 ${visionAnalysis.error ? 'bg-amber-900/20 border-amber-700/30' : 'bg-purple-900/20 border-purple-700/30'} border rounded-lg text-xs`}>
                                {visionAnalysis.error ? (
                                  <div className="flex items-center gap-2 text-amber-300 py-1">
                                    <span className="text-amber-400">⚠️</span>
                                    <span>{visionAnalysis.error}</span>
                                  </div>
                                ) : (
                                <div className="flex gap-3">
                                  {/* Source image thumbnail */}
                                  {visionSourceImage && (
                                    <img
                                      src={visionSourceImage}
                                      alt="Source"
                                      className="w-16 h-16 object-cover rounded-lg border border-purple-700/30 shrink-0"
                                    />
                                  )}
                                  <div className="space-y-1.5 flex-1">
                                    {visionAnalysis.product_type && (
                                      <div className="flex gap-2">
                                        <span className="text-purple-400 font-medium w-20 shrink-0">Type:</span>
                                        <span className="text-gray-300">{visionAnalysis.product_type}</span>
                                      </div>
                                    )}
                                    {visionAnalysis.category && (
                                      <div className="flex gap-2">
                                        <span className="text-purple-400 font-medium w-20 shrink-0">Category:</span>
                                        <span className="text-gray-300">{visionAnalysis.category}</span>
                                      </div>
                                    )}
                                    {visionAnalysis.key_terms && visionAnalysis.key_terms.length > 0 && (
                                      <div className="flex gap-2">
                                        <span className="text-purple-400 font-medium w-20 shrink-0">Terms:</span>
                                        <div className="flex flex-wrap gap-1">
                                          {visionAnalysis.key_terms.map((term: string, i: number) => (
                                            <span key={i} className="px-1.5 py-0.5 bg-purple-800/40 text-purple-300 rounded text-xs">
                                              {term}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                    {visionAnalysis.description && (
                                      <div className="flex gap-2">
                                        <span className="text-purple-400 font-medium w-20 shrink-0">Details:</span>
                                        <span className="text-gray-400">{visionAnalysis.description}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                        <SearchMode
                          mode={mode}
                          results={searchResults}
                          isLoading={isLoading}
                          onProductClick={handleProductClick}
                        />
                      </>
                    )}
                  </>
                )}
              </div>

              {/* Input */}
              {!isDemoRunning && (
                <form onSubmit={handleSubmit} className="p-4 border-t border-slate-700">
                  {/* Hidden file input for image upload */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImageSelect}
                    className="hidden"
                  />

                  {/* Image preview bar */}
                  {pendingImagePreview && (
                    <div className="flex items-center gap-2 mb-2 p-2 bg-slate-800/50 border border-slate-700 rounded-lg">
                      <img
                        src={pendingImagePreview}
                        alt="Upload preview"
                        className="w-12 h-12 object-cover rounded"
                      />
                      <span className="text-xs text-gray-400 flex-1">Image attached</span>
                      <button
                        type="button"
                        onClick={clearPendingImage}
                        className="p-1 hover:bg-white/10 rounded transition-colors"
                      >
                        <X className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  )}

                  <div className="flex gap-2">
                    {/* Image upload button - in chat and hybrid modes when Jina VLM is configured */}
                    {(mode === 'chat' || mode === 'hybrid') && visionEnabled && (
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isLoading}
                        className="bg-slate-800 border border-slate-700 hover:bg-slate-700 text-gray-400 hover:text-white px-3 py-3 rounded-xl transition-all disabled:opacity-50"
                        title="Upload a product image to find similar items"
                      >
                        <ImagePlus className="w-5 h-5" />
                      </button>
                    )}
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder={
                        mode === 'chat'
                          ? (pendingImage ? "Describe what you're looking for, or just send the image..." : "Ask about gear or your trip...")
                          : mode === 'hybrid' && pendingImage
                            ? "Add optional search terms, or just send the image..."
                            : "Search for products..."
                      }
                      className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                      disabled={isLoading}
                    />
                    <button
                      type="submit"
                      disabled={(!input.trim() && !pendingImage) || isLoading}
                      title={pendingImage && !input.trim() ? 'Search by image' : 'Search'}
                      className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl transition-all disabled:opacity-50 flex items-center gap-2"
                    >
                      {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </motion.div>

          {/* Product Detail Modal */}
          {isProductModalOpen && (
            <ProductDetailModal
              product={selectedProduct}
              userId={userId}
              onClose={() => {
                setIsProductModalOpen(false)
                setSelectedProduct(null)
              }}
            />
          )}
        </>
      )}
    </AnimatePresence>
  )
}
