import { motion, AnimatePresence } from 'framer-motion'

interface NarrationBannerProps {
  message: string
  icon?: string
  visible: boolean
}

export function NarrationBanner({ message, icon, visible }: NarrationBannerProps) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 pointer-events-none"
        >
          <div className="bg-slate-900/95 backdrop-blur-lg border border-primary/30 rounded-lg px-4 py-3 shadow-xl shadow-primary/20">
            <div className="flex items-center gap-3 text-white">
              {icon && <span className="text-2xl">{icon}</span>}
              <span className="text-sm font-medium">{message}</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

