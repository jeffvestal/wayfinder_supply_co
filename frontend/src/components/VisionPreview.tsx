import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Sparkles, X, Download, Loader2, Code2, ChevronDown, ChevronUp } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../lib/api'

interface VisionPreviewProps {
  /** The user-uploaded scene image as base64 (no data URI prefix) */
  sceneImageBase64: string
  /** Product name to visualize in the scene */
  productName: string
  /** Full product description from catalog (for enhanced Imagen prompt) */
  productDescription?: string
  /** Product catalog image URL (used as style reference for Imagen) */
  productImageUrl?: string
  /** Description of the scene (from Jina VLM analysis, passed via context) */
  sceneDescription: string
  /** Whether Imagen is configured */
  imagenReady: boolean
}

export function VisionPreview({
  sceneImageBase64,
  productName,
  productDescription,
  productImageUrl,
  sceneDescription,
  imagenReady,
}: VisionPreviewProps) {
  const [generatedImage, setGeneratedImage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [promptUsed, setPromptUsed] = useState<string>('')
  const [showPrompt, setShowPrompt] = useState(false)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    setShowPrompt(false)
    try {
      const result = await api.generatePreview(
        sceneImageBase64,
        productName,
        sceneDescription,
        productDescription,
        productImageUrl
      )
      setGeneratedImage(result.image_base64)
      setPromptUsed(result.prompt)
      setShowModal(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preview')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!generatedImage) return
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${generatedImage}`
    link.download = `${productName.replace(/\s+/g, '_')}_preview.png`
    link.click()
  }

  if (!imagenReady) return null

  return (
    <>
      {/* Trigger button + inline thumbnail row */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="inline-flex items-center gap-1 px-2 py-1 text-[10px] rounded-md bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 transition-all disabled:opacity-50"
          title={generatedImage ? 'Regenerate product-in-scene preview' : 'Generate product-in-scene preview with AI'}
        >
          {loading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Sparkles className="w-3 h-3" />
          )}
          {generatedImage ? 'Regenerate' : 'Visualize'}
        </button>

        {/* Inline thumbnail — click to re-open modal */}
        {generatedImage && !showModal && (
          <button
            onClick={() => setShowModal(true)}
            className="relative group rounded-md overflow-hidden border border-white/10 hover:border-amber-400/50 transition-all"
            title="Click to enlarge"
          >
            <img
              src={`data:image/png;base64,${generatedImage}`}
              alt={`AI preview of ${productName}`}
              className="w-10 h-10 object-cover"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <p className="text-[10px] text-red-400 mt-0.5">{error}</p>
      )}

      {/* Modal — portaled to document.body so it escapes overflow containers */}
      {createPortal(
        <AnimatePresence>
          {showModal && generatedImage && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
              onClick={() => setShowModal(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-slate-900 border border-white/10 rounded-2xl p-4 max-w-2xl w-full mx-4 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    {productName} — AI Preview
                  </h3>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleDownload}
                      className="p-1.5 rounded-lg bg-white/10 text-zinc-400 hover:text-white transition-colors"
                      title="Download image"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setShowModal(false)}
                      className="p-1.5 rounded-lg bg-white/10 text-zinc-400 hover:text-white transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <img
                  src={`data:image/png;base64,${generatedImage}`}
                  alt={`AI preview of ${productName} in scene`}
                  className="w-full rounded-lg border border-white/10"
                />
                <p className="text-[10px] text-zinc-500 mt-2 text-center">
                  Generated by Imagen 3 — for illustration purposes
                </p>
                {/* Show Prompt toggle */}
                {promptUsed && (
                  <div className="mt-3">
                    <button
                      onClick={() => setShowPrompt(!showPrompt)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] rounded-md bg-white/5 text-zinc-400 hover:text-zinc-200 hover:bg-white/10 transition-all border border-white/5"
                    >
                      <Code2 className="w-3 h-3" />
                      Show Prompt
                      {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                    <AnimatePresence>
                      {showPrompt && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <pre className="mt-2 p-3 rounded-lg bg-black/40 border border-white/5 text-[11px] text-zinc-400 leading-relaxed whitespace-pre-wrap font-mono">
                            {promptUsed}
                          </pre>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  )
}
