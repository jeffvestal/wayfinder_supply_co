import { useState } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Loader2, ChevronRight, ChevronDown, CheckCircle2, Eye } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { ExtendedChatMessage, AgentStep } from './types'
import { StepRenderer } from './StepRenderer'
import { getToolStatusMessage } from '../../lib/constants'
import { ProductCard } from '../ProductCard'
import { Product, UserId } from '../../types'

interface ChatModeProps {
  messages: ExtendedChatMessage[]
  isLoading: boolean
  stepsExpanded: Record<string, boolean>
  expandedSteps: Set<string>
  onToggleStepsExpanded: (messageId: string) => void
  onToggleStep: (stepId: string) => void
  messagesEndRef: React.RefObject<HTMLDivElement>
  userId: UserId
  onProductClick: (product: Product) => void
}

// Get current thinking status from trace events
function getCurrentStatus(steps: AgentStep[], isLoading: boolean): string {
  if (!isLoading) return ''
  if (steps.length === 0) return 'Starting up...'
  
  const lastStep = steps[steps.length - 1]
  if (lastStep.type === 'reasoning') {
    return 'Thinking...'
  } else if (lastStep.type === 'tool_call') {
    return getToolStatusMessage(lastStep.tool_id || '')
  }
  return 'Working...'
}

// Extract intro text before product list (when products are displayed as cards)
function extractIntroText(content: string): string {
  if (!content) return content
  
  // Split by lines
  const lines = content.split('\n')
  const introLines: string[] = []
  
  for (const line of lines) {
    const trimmed = line.trim()
    
    // Stop if we hit a product list pattern
    if (
      /^\d+\.\s+\*?\*?/.test(trimmed) ||  // Numbered list: "1. **Product"
      /^[-•*]\s+\*?\*?/.test(trimmed) ||   // Bullet list: "- **Product"
      /\$\d+\.?\d*/.test(trimmed)          // Price: "$123.45"
    ) {
      break
    }
    
    introLines.push(line)
  }
  
  return introLines.join('\n').trim()
}

export function ChatMode({
  messages,
  isLoading: _isLoading,
  stepsExpanded,
  expandedSteps,
  onToggleStepsExpanded,
  onToggleStep,
  messagesEndRef,
  userId,
  onProductClick
}: ChatModeProps) {
  // Vision analysis card expand state (keyed by message ID)
  const [visionExpanded, setVisionExpanded] = useState<Record<string, boolean>>({})

  // Find the source image from the preceding user message
  const getSourceImage = (messageIndex: number): string | undefined => {
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user' && messages[i].image_url) {
        return messages[i].image_url
      }
    }
    return undefined
  }

  // Empty state
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-center">
        <div>
          <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2 text-white">Start a Conversation</h3>
          <p className="text-gray-400 text-sm">
            Ask about gear, get recommendations, or plan your trip
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((message, msgIndex) => (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div className={`flex flex-col w-full ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
            {/* Thought Trace - Moved above the bubble for assistant */}
            {message.role === 'assistant' && message.steps && message.steps.length > 0 && (
              <div className="mb-2 ml-4">
                <button
                  onClick={() => onToggleStepsExpanded(message.id)}
                  className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300 transition-colors"
                >
                  {stepsExpanded[message.id] ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  {message.status === 'complete' || !message.status ? (
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-green-500" />
                      <span>Completed {message.steps.filter(s => s.reasoning || s.tool_id).length} steps</span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5">
                      <Loader2 className="w-3 h-3 animate-spin text-primary" />
                      <span>{getCurrentStatus(message.steps || [], true)}</span>
                    </span>
                  )}
                </button>
                {stepsExpanded[message.id] && (
                  <div className="space-y-1 mt-2 w-full max-w-[85%]">
                    {message.steps
                      .filter(step => step.reasoning || (step.tool_id && step.params))
                      .map((step, idx) => (
                        <StepRenderer
                          key={idx}
                          step={step}
                          index={idx}
                          messageId={message.id}
                          isExpanded={expandedSteps.has(`${message.id}-${idx}`)}
                          onToggle={onToggleStep}
                        />
                      ))}
                  </div>
                )}
              </div>
            )}

            {/* Vision Analysis Card - between reasoning and response */}
            {message.role === 'assistant' && message.vision_analysis && (
              <div className="mb-2 ml-4 w-full max-w-[85%]">
                <button
                  onClick={() => setVisionExpanded(prev => ({ ...prev, [message.id]: !prev[message.id] }))}
                  className="w-full flex items-center gap-2 px-3 py-2 bg-purple-900/30 border border-purple-700/40 rounded-lg text-sm text-purple-300 hover:bg-purple-900/40 transition-colors"
                >
                  <Eye className="w-4 h-4 text-purple-400" />
                  <span className="font-medium">Vision Analysis</span>
                  {message.vision_analysis.product_type && (
                    <span className="text-purple-400/70 ml-1">— {message.vision_analysis.product_type}</span>
                  )}
                  <span className="ml-auto">
                    {visionExpanded[message.id]
                      ? <ChevronDown className="w-4 h-4" />
                      : <ChevronRight className="w-4 h-4" />
                    }
                  </span>
                </button>
                {visionExpanded[message.id] && (
                  <div className="mt-1 px-3 py-2 bg-purple-900/20 border border-purple-700/30 rounded-lg text-xs">
                    <div className="flex gap-3">
                      {/* Source image thumbnail */}
                      {(() => {
                        const sourceImg = getSourceImage(msgIndex)
                        return sourceImg ? (
                          <img
                            src={sourceImg}
                            alt="Source"
                            className="w-16 h-16 object-cover rounded-lg border border-purple-700/30 shrink-0"
                          />
                        ) : null
                      })()}
                      <div className="space-y-1.5 flex-1">
                        {message.vision_analysis.product_type && (
                          <div className="flex gap-2">
                            <span className="text-purple-400 font-medium w-20 shrink-0">Type:</span>
                            <span className="text-gray-300">{message.vision_analysis.product_type}</span>
                          </div>
                        )}
                        {message.vision_analysis.category && (
                          <div className="flex gap-2">
                            <span className="text-purple-400 font-medium w-20 shrink-0">Category:</span>
                            <span className="text-gray-300">{message.vision_analysis.category}</span>
                          </div>
                        )}
                        {message.vision_analysis.key_terms && message.vision_analysis.key_terms.length > 0 && (
                          <div className="flex gap-2">
                            <span className="text-purple-400 font-medium w-20 shrink-0">Terms:</span>
                            <div className="flex flex-wrap gap-1">
                              {message.vision_analysis.key_terms.map((term: string, i: number) => (
                                <span key={i} className="px-1.5 py-0.5 bg-purple-800/40 text-purple-300 rounded text-xs">
                                  {term}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {message.vision_analysis.description && (
                          <div className="flex gap-2">
                            <span className="text-purple-400 font-medium w-20 shrink-0">Details:</span>
                            <span className="text-gray-400">{message.vision_analysis.description}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-primary text-white'
                  : 'bg-slate-800 text-gray-100 shadow-lg'
              }`}
            >
              {/* Status indicator - simplified since trace is above */}
              {message.role === 'assistant' && message.status && message.status !== 'complete' && message.steps?.length === 0 && (
                <div className="flex items-center gap-2 mb-2">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <span className="text-xs text-primary font-medium">
                    Thinking...
                  </span>
                </div>
              )}

              {/* Message content */}
            {message.role === 'assistant' ? (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>
                  {message.products && message.products.length > 0 
                    ? extractIntroText(message.content)
                    : message.content
                  }
                </ReactMarkdown>
              </div>
            ) : (
              <>
                {/* User-uploaded image thumbnail */}
                {message.image_url && (
                  <img
                    src={message.image_url}
                    alt="Uploaded product"
                    className="max-w-[200px] max-h-[150px] object-cover rounded-lg mb-2"
                  />
                )}
                <p className="text-sm">{message.content}</p>
              </>
            )}
            
            <p className="text-xs opacity-70 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </p>
          </div>
          
          {/* Product Cards - display below assistant messages */}
          {message.role === 'assistant' && message.products && message.products.length > 0 && (
            <div className="mt-3 ml-4 space-y-2 w-full max-w-[85%]">
              <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Recommended Gear</p>
              <div className="grid grid-cols-1 gap-2">
                {message.products.map((product) => (
                  <ProductCard 
                    key={product.id} 
                    product={product} 
                    userId={userId}
                    onClick={() => onProductClick(product)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  )
}

