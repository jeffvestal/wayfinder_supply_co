import { ThoughtTraceEvent } from '../types'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@radix-ui/react-collapsible'
import { ChevronRight, Brain, Wrench, CheckCircle, XCircle } from 'lucide-react'
import { motion } from 'framer-motion'

interface ThoughtTraceProps {
  events: ThoughtTraceEvent[]
}

export function ThoughtTrace({ events }: ThoughtTraceProps) {
  if (events.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-6 h-full">
        <h3 className="font-display font-bold text-xl text-slate-900 mb-2 flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary" />
          Thought Trace
        </h3>
        <p className="text-sm text-slate-500 text-center py-12">
          Agent reasoning will appear here as it processes your request
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-6 h-full overflow-y-auto scrollbar-hide">
      <h3 className="font-display font-bold text-xl text-slate-900 mb-6 flex items-center gap-2">
        <Brain className="w-5 h-5 text-primary" />
        Thought Trace
      </h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />
        <div className="space-y-4">
          {events.map((event, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <TraceEvent event={event} />
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}

function TraceEvent({ event }: { event: ThoughtTraceEvent }) {
  if (event.event === 'reasoning') {
    return (
      <div className="relative pl-12">
        <div className="absolute left-5 top-2 w-3 h-3 rounded-full bg-primary border-2 border-white shadow-lg" />
        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Brain className="w-4 h-4 text-primary" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-700 leading-relaxed">{event.data}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (event.event === 'tool_call') {
    return (
      <div className="relative pl-12">
        <div className="absolute left-5 top-2 w-3 h-3 rounded-full bg-accent border-2 border-white shadow-lg" />
        <Collapsible>
          <CollapsibleTrigger className="w-full text-left">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
                  <Wrench className="w-4 h-4 text-accent" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-slate-900">
                    Calling: {event.data.tool_id || event.data.name || 'unknown'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Click to see parameters</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
              </div>
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="ml-11 mt-2 bg-slate-900 rounded-lg p-3 border border-slate-700">
              <pre className="text-xs text-slate-300 overflow-x-auto">
                {JSON.stringify(event.data.params || event.data, null, 2)}
              </pre>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>
    )
  }

  if (event.event === 'tool_result') {
    const hasError = event.data.results?.some((r: any) => r.type === 'error')
    return (
      <div className="relative pl-12">
        <div className={`absolute left-5 top-2 w-3 h-3 rounded-full border-2 border-white shadow-lg ${
          hasError ? 'bg-red-500' : 'bg-green-500'
        }`} />
        <Collapsible>
          <CollapsibleTrigger className="w-full text-left">
            <div className={`rounded-xl p-4 border transition-colors cursor-pointer ${
              hasError 
                ? 'bg-red-50 border-red-200 hover:bg-red-100' 
                : 'bg-green-50 border-green-200 hover:bg-green-100'
            }`}>
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  hasError ? 'bg-red-100' : 'bg-green-100'
                }`}>
                  {hasError ? (
                    <XCircle className="w-4 h-4 text-red-600" />
                  ) : (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  )}
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-semibold ${
                    hasError ? 'text-red-900' : 'text-green-900'
                  }`}>
                    Tool {hasError ? 'failed' : 'completed'}
                  </p>
                  <p className={`text-xs mt-1 ${
                    hasError ? 'text-red-600' : 'text-green-600'
                  }`}>
                    Click to see results
                  </p>
                </div>
                <ChevronRight className={`w-4 h-4 flex-shrink-0 ${
                  hasError ? 'text-red-400' : 'text-green-400'
                }`} />
              </div>
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="ml-11 mt-2 bg-slate-900 rounded-lg p-3 border border-slate-700">
              <pre className="text-xs text-slate-300 overflow-x-auto">
                {JSON.stringify(event.data.results || event.data, null, 2)}
              </pre>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>
    )
  }

  return null
}


