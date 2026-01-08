import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { api } from '../lib/api'
import { 
  CheckCircle2, Circle, ChevronLeft, ChevronRight, 
  RefreshCw, Workflow, Wrench, Bot, Loader2
} from 'lucide-react'

interface WorkshopStatus {
  workflows: Array<{ name: string; exists: boolean; user_built: boolean }>;
  tools: Array<{ id: string; exists: boolean; user_built: boolean }>;
  agents: Array<{ id: string; exists: boolean; user_built: boolean }>;
  summary: { complete: number; total: number; percentage: number };
}

interface WorkshopProgressProps {
  defaultExpanded?: boolean;
}

// Friendly display names for components
const DISPLAY_NAMES: Record<string, string> = {
  // Workflows
  'check_trip_safety': 'Check Trip Safety',
  'get_user_affinity': 'Get User Affinity',
  'get_customer_profile': 'Get Customer Profile',
  // Tools
  'tool-search-product-search': 'Product Search',
  'tool-esql-get-user-affinity': 'User Affinity (ES|QL)',
  'tool-workflow-get-customer-profile': 'Customer Profile Tool',
  // Agents
  'wayfinder-search-agent': 'Wayfinder Search',
  'trip-planner-agent': 'Trip Planner',
}

function getDisplayName(id: string): string {
  return DISPLAY_NAMES[id] || id
}

export function WorkshopProgress({ defaultExpanded = true }: WorkshopProgressProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [status, setStatus] = useState<WorkshopStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchStatus = async () => {
    setIsLoading(true)
    try {
      const data = await api.getWorkshopStatus()
      setStatus(data)
      setLastRefresh(new Date())
    } catch (error) {
      console.error('Failed to fetch workshop status:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Initial fetch and polling
  useEffect(() => {
    fetchStatus()
    
    // Poll every 15 seconds
    const interval = setInterval(fetchStatus, 15000)
    return () => clearInterval(interval)
  }, [])

  // Load collapsed state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('workshop-progress-expanded')
    if (saved !== null) {
      setIsExpanded(saved === 'true')
    }
  }, [])

  // Save collapsed state
  const toggleExpanded = () => {
    const newState = !isExpanded
    setIsExpanded(newState)
    localStorage.setItem('workshop-progress-expanded', String(newState))
  }

  const renderStatusIcon = (exists: boolean, userBuilt: boolean) => {
    if (exists) {
      return <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
    }
    return <Circle className={`w-4 h-4 flex-shrink-0 ${userBuilt ? 'text-amber-400' : 'text-gray-600'}`} />
  }

  const renderSection = (
    title: string,
    icon: React.ReactNode,
    items: Array<{ name?: string; id?: string; exists: boolean; user_built: boolean }>
  ) => (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{title}</span>
      </div>
      <div className="space-y-1.5">
        {items.map((item) => {
          const id = item.name || item.id || ''
          return (
            <div 
              key={id}
              className={`flex items-center gap-2 text-sm ${
                item.exists ? 'text-gray-200' : item.user_built ? 'text-amber-300' : 'text-gray-500'
              }`}
            >
              {renderStatusIcon(item.exists, item.user_built)}
              <span className="truncate">{getDisplayName(id)}</span>
              {item.user_built && !item.exists && (
                <span className="text-[10px] bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded ml-auto flex-shrink-0">
                  Build this!
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )

  // Collapsed badge view
  if (!isExpanded) {
    return (
      <motion.button
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        onClick={toggleExpanded}
        className="fixed right-4 top-24 z-40 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 flex items-center gap-2 hover:bg-slate-700 transition-colors shadow-lg"
        title="Show workshop progress"
      >
        <div className="flex items-center gap-1.5">
          {status ? (
            <>
              <span className="text-sm font-medium text-white">
                {status.summary.complete}/{status.summary.total}
              </span>
              <CheckCircle2 className="w-4 h-4 text-green-400" />
            </>
          ) : (
            <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
          )}
        </div>
        <ChevronLeft className="w-4 h-4 text-gray-400" />
      </motion.button>
    )
  }

  // Expanded sidebar view
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="fixed right-4 top-24 z-40 w-64 bg-slate-900 border border-slate-700 rounded-xl shadow-xl overflow-hidden"
    >
      {/* Header */}
      <div className="bg-slate-800 px-4 py-3 flex items-center justify-between border-b border-slate-700">
        <h3 className="text-sm font-semibold text-white">Workshop Progress</h3>
        <button
          onClick={toggleExpanded}
          className="p-1 hover:bg-slate-700 rounded transition-colors"
          title="Collapse"
        >
          <ChevronRight className="w-4 h-4 text-gray-400" />
        </button>
      </div>

      {/* Progress bar */}
      {status && (
        <div className="px-4 py-3 border-b border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">
              {status.summary.complete} of {status.summary.total} complete
            </span>
            <span className="text-xs font-medium text-primary">
              {status.summary.percentage}%
            </span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${status.summary.percentage}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-primary to-cyan-500 rounded-full"
            />
          </div>
        </div>
      )}

      {/* Content */}
      <div className="px-4 py-3 max-h-[400px] overflow-y-auto">
        {isLoading && !status ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-primary animate-spin" />
          </div>
        ) : status ? (
          <>
            {renderSection(
              'Workflows',
              <Workflow className="w-4 h-4 text-purple-400" />,
              status.workflows
            )}
            {renderSection(
              'Tools',
              <Wrench className="w-4 h-4 text-cyan-400" />,
              status.tools
            )}
            {renderSection(
              'Agents',
              <Bot className="w-4 h-4 text-amber-400" />,
              status.agents
            )}
          </>
        ) : (
          <div className="text-center py-8 text-gray-500 text-sm">
            Unable to load status
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-700 bg-slate-800/50">
        <button
          onClick={fetchStatus}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
          {lastRefresh ? (
            <span>Updated {lastRefresh.toLocaleTimeString()}</span>
          ) : (
            <span>Refresh</span>
          )}
        </button>
      </div>
    </motion.div>
  )
}

