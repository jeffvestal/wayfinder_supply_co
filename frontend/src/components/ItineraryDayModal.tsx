import { X, Sun, Moon, Thermometer } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface ItineraryDay {
  day: number
  title: string
  activities: string[]
  weather?: string
  distance?: string
}

interface ItineraryDayModalProps {
  day: ItineraryDay | null
  isOpen: boolean
  onClose: () => void
}

export function ItineraryDayModal({ day, isOpen, onClose }: ItineraryDayModalProps) {
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
            className="fixed inset-0 z-[60] bg-slate-950/90 backdrop-blur-sm"
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.5 }}
            className="fixed inset-0 z-[61] flex items-center justify-center p-4"
            onClick={onClose}
          >
            <div
              className="relative bg-slate-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-slate-700"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-primary/20 to-primary/10 border-b border-slate-700 px-8 py-6 flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-display font-bold text-white mb-1">
                    Day {day.day}: {day.title}
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    {day.weather && (
                      <span className="flex items-center gap-1.5">
                        <Thermometer className="w-4 h-4" /> {day.weather}
                      </span>
                    )}
                    {day.distance && (
                      <span className="flex items-center gap-1.5">
                        📍 {day.distance}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
                >
                  <X className="w-5 h-5 text-gray-300" />
                </button>
              </div>

              {/* Content */}
              <div className="p-8 overflow-y-auto max-h-[calc(90vh-120px)]">
                <h3 className="text-sm font-semibold text-primary mb-4 uppercase tracking-wide">
                  Activities
                </h3>
                <ul className="space-y-4">
                  {day.activities.map((activity: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-4 text-gray-300">
                      {idx === 0 ? (
                        <Sun className="w-6 h-6 mt-0.5 text-amber-400 flex-shrink-0" />
                      ) : idx === day.activities.length - 1 ? (
                        <Moon className="w-6 h-6 mt-0.5 text-blue-400 flex-shrink-0" />
                      ) : (
                        <span className="w-6 h-6 flex items-center justify-center text-primary mt-0.5 flex-shrink-0">
                          •
                        </span>
                      )}
                      <span className="text-lg leading-relaxed">{activity}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Footer hint */}
              <div className="border-t border-slate-700 px-8 py-4 bg-slate-800/50">
                <p className="text-xs text-gray-500 text-center">
                  Click outside or press the X to close
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

