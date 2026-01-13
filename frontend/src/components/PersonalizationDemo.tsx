import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Product } from '../types'
import { api } from '../lib/api'
import { ProductCard } from './ProductCard'
import { Loader2, X, Terminal } from 'lucide-react'

interface PersonalizationDemoProps {
  onClose: () => void
}

export function PersonalizationDemo({ onClose }: PersonalizationDemoProps) {
  const [guestResults, setGuestResults] = useState<Product[]>([])
  const [sarahResults, setSarahResults] = useState<Product[]>([])
  const [guestDebug, setGuestDebug] = useState<any>(null)
  const [sarahDebug, setSarahDebug] = useState<any>(null)
  const [clickstreamDebug, setClickstreamDebug] = useState<any>(null)
  const [showDebug, setShowDebug] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const query = 'backpacking gear'

  useEffect(() => {
    const runComparison = async () => {
      setIsLoading(true)
      try {
        // Search as guest (no personalization)
        const guestSearch = await api.hybridSearch(query, 10, undefined)
        setGuestDebug(guestSearch)
        
        // Search as Sarah (ultralight backpacker)
        const sarahSearch = await api.hybridSearch(query, 10, 'ultralight_backpacker_sarah')
        setSarahDebug(sarahSearch)

        // Get clickstream debug info
        try {
          const response = await fetch(`${api.getBaseUrl()}/products/debug/clickstream/ultralight_backpacker_sarah`)
          const data = await response.json()
          setClickstreamDebug(data)
        } catch (e) {
          console.error('Failed to fetch clickstream debug:', e)
        }
        
        setGuestResults(guestSearch.products)
        setSarahResults(sarahSearch.products)
      } catch (error) {
        console.error('Personalization demo failed:', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    runComparison()
  }, [])

  // Find products that differ between users
  const guestIds = new Set(guestResults.map(p => p.id))
  const sarahIds = new Set(sarahResults.map(p => p.id))
  const onlyInGuest = guestResults.filter(p => !sarahIds.has(p.id))
  const onlyInSarah = sarahResults.filter(p => !guestIds.has(p.id))

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-sm flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 w-full max-w-7xl max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div>
            <h2 className="text-2xl font-display font-bold text-white mb-1">
              Personalization Comparison
            </h2>
            <p className="text-gray-400 text-sm">
              Same query: &quot;{query}&quot;
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowDebug(!showDebug)}
              className={`p-2 rounded-lg transition-colors flex items-center gap-2 text-sm ${
                showDebug ? 'bg-primary text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
              }`}
              title="Show Debug Info"
            >
              <Terminal className="w-4 h-4" />
              <span className="hidden sm:inline">Debug Info</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5 text-gray-300" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : showDebug ? (
            <div className="grid grid-cols-1 gap-6">
              <div className="space-y-4">
                <h3 className="font-mono text-sm text-primary uppercase tracking-wider">Sarah Clickstream Data (Remote VM)</h3>
                <pre className="bg-black/50 p-4 rounded-xl text-[10px] font-mono text-amber-400 overflow-auto max-h-[40vh] border border-white/10">
                  {JSON.stringify(clickstreamDebug, null, 2)}
                </pre>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
                <div className="space-y-4">
                  <h3 className="font-mono text-sm text-primary uppercase tracking-wider">Guest User API Response</h3>
                  <pre className="bg-black/50 p-4 rounded-xl text-[10px] font-mono text-cyan-400 overflow-auto max-h-[60vh] border border-white/10">
                    {JSON.stringify(guestDebug, (k, v) => k === 'raw_hits' ? undefined : v, 2)}
                  </pre>
                </div>
                <div className="space-y-4">
                  <h3 className="font-mono text-sm text-primary uppercase tracking-wider">Sarah User API Response</h3>
                  <pre className="bg-black/50 p-4 rounded-xl text-[10px] font-mono text-green-400 overflow-auto max-h-[60vh] border border-white/10">
                    {JSON.stringify(sarahDebug, (k, v) => k === 'raw_hits' ? undefined : v, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Guest Results */}
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Guest User (No Personalization)
                  </h3>
                  <p className="text-sm text-gray-400">
                    {guestResults.length} results
                  </p>
                </div>
                <div className="space-y-4">
                  {guestResults.map((product, idx) => {
                    const isDifferent = onlyInGuest.some(p => p.id === product.id)
                    return (
                      <motion.div
                        key={product.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className={isDifferent ? 'ring-2 ring-amber-500/50 rounded-lg' : ''}
                      >
                        <ProductCard product={product} userId="user_new" />
                      </motion.div>
                    )
                  })}
                </div>
              </div>

              {/* Sarah Results */}
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Sarah (Ultralight Backpacker)
                  </h3>
                  <p className="text-sm text-gray-400">
                    {sarahResults.length} results (personalized)
                  </p>
                </div>
                <div className="space-y-4">
                  {sarahResults.map((product, idx) => {
                    const isDifferent = onlyInSarah.some(p => p.id === product.id)
                    return (
                      <motion.div
                        key={product.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className={isDifferent ? 'ring-2 ring-primary/50 rounded-lg' : ''}
                      >
                        <ProductCard product={product} userId="ultralight_backpacker_sarah" />
                      </motion.div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}

