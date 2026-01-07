import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Sparkles } from 'lucide-react'

interface DemoOverlayProps {
  isVisible: boolean
  message?: string
}

export function DemoOverlay({ isVisible, message = 'Setting up demo...' }: DemoOverlayProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
          />
          
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="fixed inset-0 z-[101] flex items-center justify-center"
          >
            <div className="bg-slate-900 rounded-2xl p-8 border border-primary/30 shadow-2xl max-w-md mx-4">
              <div className="flex flex-col items-center gap-4">
                <div className="relative">
                  <Loader2 className="w-12 h-12 text-primary animate-spin" />
                  <Sparkles className="w-6 h-6 text-primary absolute -top-1 -right-1 animate-pulse" />
                </div>
                <h3 className="text-xl font-display font-bold text-white text-center">
                  {message}
                </h3>
                <p className="text-sm text-gray-400 text-center">
                  Switching to Sarah Martinez and loading Trip Planner...
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

