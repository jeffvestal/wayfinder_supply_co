import { ChevronRight, ChevronDown, Settings, Database } from 'lucide-react'
import { AgentStep } from './types'

interface StepRendererProps {
  step: AgentStep
  index: number
  messageId: string
  isExpanded: boolean
  onToggle: (stepId: string) => void
}

export function StepRenderer({ step, index, messageId, isExpanded, onToggle }: StepRendererProps) {
  const stepId = `${messageId}-${index}`

  return (
    <div className="bg-primary/10 rounded-lg border border-primary/20 overflow-hidden">
      <button
        onClick={() => onToggle(stepId)}
        className="w-full flex items-center justify-between p-2 hover:bg-primary/20 transition-colors"
      >
        <div className="flex items-center gap-2">
          {step.type === 'reasoning' ? (
            <>
              <Settings className="h-3 w-3 text-primary" />
              <span className="text-xs font-medium text-primary">Reasoning</span>
            </>
          ) : (
            <>
              <Database className="h-3 w-3 text-primary" />
              <span className="text-xs font-medium text-primary">{step.tool_id || 'Tool Call'}</span>
            </>
          )}
        </div>
        {isExpanded ? <ChevronDown className="h-3 w-3 text-primary" /> : <ChevronRight className="h-3 w-3 text-primary" />}
      </button>

      {isExpanded && (
        <div className="border-t border-primary/20 p-3 space-y-3 bg-primary/5">
          {step.type === 'reasoning' && step.reasoning && (
            <div>
              <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">Agent Thinking:</div>
              <div className="bg-slate-800 rounded-md p-3">
                <div className="text-xs text-gray-300 leading-relaxed">{step.reasoning}</div>
              </div>
            </div>
          )}

          {step.type === 'tool_call' && step.params && Object.keys(step.params).length > 0 && (
            <div>
              <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">Parameters:</div>
              <div className="bg-slate-800 rounded-md p-3">
                <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                  {JSON.stringify(step.params, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {step.type === 'tool_call' && step.results && step.results.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-primary/70 mb-2 uppercase tracking-wide">Results:</div>
              {step.results.map((result: any, resultIdx: number) => (
                <div key={resultIdx} className="bg-slate-800 rounded-md p-3 mb-2">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono max-h-32 overflow-y-auto">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}




