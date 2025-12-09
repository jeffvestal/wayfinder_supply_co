import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Clock } from 'lucide-react'
import { api } from '../lib/api'

interface ClickstreamEvent {
  product_id: string
  product_name: string
  timestamp: string
  action: string
}

interface ClickstreamEventsModalProps {
  userId: string
  action: 'view_item' | 'add_to_cart'
  title: string
  isOpen: boolean
  onClose: () => void
}

export function ClickstreamEventsModal({
  userId,
  action,
  title,
  isOpen,
  onClose,
}: ClickstreamEventsModalProps) {
  const [events, setEvents] = useState<ClickstreamEvent[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadEvents()
    }
  }, [isOpen, userId, action])

  const loadEvents = async () => {
    try {
      setLoading(true)
      const data = await api.getUserEvents(userId, action)
      setEvents(data.events)
    } catch (err) {
      console.error('Failed to load events:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } catch {
      return 'Unknown time'
    }
  }

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    } catch {
      return 'Unknown date'
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-900 rounded-xl border border-slate-700 p-6 z-50 max-w-md w-full max-h-96 overflow-y-auto shadow-2xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">{title}</h2>
              <button
                onClick={onClose}
                className="p-1 hover:bg-slate-800 rounded transition-colors"
              >
                <X className="w-5 h-5 text-gray-400 hover:text-gray-300" />
              </button>
            </div>

            {loading ? (
              <div className="text-gray-400 text-center py-8">Loading events...</div>
            ) : events.length === 0 ? (
              <div className="text-gray-500 text-center py-8">No events yet</div>
            ) : (
              <div className="space-y-2">
                {events.map((event, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 hover:border-slate-600 transition-colors"
                  >
                    <p className="text-sm font-medium text-white line-clamp-2 mb-2">
                      {event.product_name}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>{formatDate(event.timestamp)}</span>
                      <span className="text-gray-600">•</span>
                      <span>{formatTime(event.timestamp)}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

