import { motion } from 'framer-motion'
import { MessageSquare, Loader2, ChevronRight, ChevronDown } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { ExtendedChatMessage, AgentStep } from './types'
import { StepRenderer } from './StepRenderer'
import { getToolStatusMessage } from '../../lib/constants'

interface ChatModeProps {
  messages: ExtendedChatMessage[]
  isLoading: boolean
  stepsExpanded: Record<string, boolean>
  expandedSteps: Set<string>
  onToggleStepsExpanded: (messageId: string) => void
  onToggleStep: (stepId: string) => void
  messagesEndRef: React.RefObject<HTMLDivElement>
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

export function ChatMode({
  messages,
  isLoading: _isLoading,
  stepsExpanded,
  expandedSteps,
  onToggleStepsExpanded,
  onToggleStep,
  messagesEndRef
}: ChatModeProps) {
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
      {messages.map((message) => (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[85%] rounded-2xl px-4 py-3 ${
              message.role === 'user'
                ? 'bg-primary text-white'
                : 'bg-slate-800 text-gray-100'
            }`}
          >
            {/* Status indicator */}
            {message.role === 'assistant' && message.status && message.status !== 'complete' && (
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-xs text-primary font-medium">
                  {getCurrentStatus(message.steps || [], true)}
                </span>
              </div>
            )}

            {/* Agent Steps */}
            {message.steps && message.steps.length > 0 && (
              <div className="mb-3">
                <button
                  onClick={() => onToggleStepsExpanded(message.id)}
                  className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300"
                >
                  {stepsExpanded[message.id] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  <span>Thought Trace ({message.steps.filter(s => s.reasoning || s.tool_id).length})</span>
                </button>
                {stepsExpanded[message.id] && (
                  <div className="space-y-1 mt-2">
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

            {/* Message content */}
            {message.role === 'assistant' ? (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm">{message.content}</p>
            )}
            
            <p className="text-xs opacity-70 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </p>
          </div>
        </motion.div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  )
}

