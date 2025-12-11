import { motion, AnimatePresence } from 'framer-motion'
import { X, MapPin, Clock } from 'lucide-react'

interface ItineraryDay {
  day: number
  title: string
  activities: string[]
  distance?: string
}

interface ItineraryDayModalProps {
  isOpen: boolean
  onClose: () => void
  day: ItineraryDay | null
}

export function ItineraryDayModal({ isOpen, onClose, day }: ItineraryDayModalProps) {
  if (!day) return null

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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 max-w-lg w-full max-h-[80vh] overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-primary to-cyan-500 p-6 relative">
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
                <div className="text-white/80 text-sm font-medium mb-1">Day {day.day}</div>
                <h2 className="text-2xl font-display font-bold text-white">{day.title}</h2>
                {day.distance && (
                  <div className="flex items-center gap-2 mt-2 text-white/80">
                    <MapPin className="w-4 h-4" />
                    <span className="text-sm">{day.distance}</span>
                  </div>
                )}
              </div>

              {/* Activities */}
              <div className="p-6 overflow-y-auto max-h-[50vh]">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Activities</h3>
                <div className="space-y-3">
                  {day.activities.map((activity, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-start gap-3 bg-slate-800/50 rounded-lg p-4 border border-slate-700"
                    >
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                        <span className="text-xs font-bold text-primary">{index + 1}</span>
                      </div>
                      <p className="text-gray-300 text-sm leading-relaxed">{activity}</p>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-slate-700 bg-slate-800/50">
                <button
                  onClick={onClose}
                  className="w-full py-2 px-4 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

