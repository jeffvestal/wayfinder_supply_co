import { ItineraryDay } from '../types'
import { X, Download, Copy, Sun, Moon, Thermometer } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface ItineraryModalProps {
  itinerary: ItineraryDay[]
  isOpen: boolean
  onClose: () => void
}

export function ItineraryModal({ itinerary, isOpen, onClose }: ItineraryModalProps) {
  const handleDownload = () => {
    const content = formatItineraryAsText(itinerary)
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trip-itinerary-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleCopy = async () => {
    const content = formatItineraryAsText(itinerary)
    try {
      await navigator.clipboard.writeText(content)
      // Could show a toast notification here
      alert('Itinerary copied to clipboard!')
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handlePrint = () => {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      const content = formatItineraryAsHTML(itinerary)
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Trip Itinerary</title>
            <style>
              body { font-family: sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
              h1 { color: #0ea5e9; margin-bottom: 30px; }
              .day { margin-bottom: 30px; page-break-inside: avoid; }
              .day-title { font-size: 1.5em; font-weight: bold; margin-bottom: 10px; color: #1e293b; }
              .activities { margin-left: 20px; }
              .activity { margin: 8px 0; }
            </style>
          </head>
          <body>
            ${content}
          </body>
        </html>
      `)
      printWindow.document.close()
      printWindow.focus()
      setTimeout(() => {
        printWindow.print()
      }, 250)
    }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-sm" />
        
        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: 'spring', duration: 0.5 }}
          className="relative bg-slate-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-slate-700"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-primary/20 to-primary/10 border-b border-slate-700 px-8 py-6 flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-display font-bold text-white mb-1">Trip Itinerary</h2>
              <p className="text-sm text-gray-400">{itinerary.length} day plan</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleCopy}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
              >
                <Copy className="w-4 h-4" />
                Copy
              </button>
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
              <button
                onClick={handlePrint}
                className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg transition-colors"
              >
                Print
              </button>
              <button
                onClick={onClose}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
              >
                <X className="w-5 h-5 text-gray-300" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-8 overflow-y-auto max-h-[calc(90vh-120px)]">
            {itinerary.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400">No itinerary available</p>
              </div>
            ) : (
              <div className="space-y-6">
                {itinerary.map((day) => (
                  <div
                    key={day.day}
                    className="bg-slate-800/50 rounded-xl p-6 border border-slate-700"
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                        <span className="text-lg font-bold text-amber-400">{day.day}</span>
                      </div>
                      <h3 className="text-2xl font-display font-bold text-white">{day.title}</h3>
                    </div>
                    <ul className="space-y-3 ml-14">
                      {day.activities.map((activity: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-3 text-gray-300">
                          {idx === 0 ? (
                            <Sun className="w-5 h-5 mt-0.5 text-amber-400 flex-shrink-0" />
                          ) : idx === day.activities.length - 1 ? (
                            <Moon className="w-5 h-5 mt-0.5 text-blue-400 flex-shrink-0" />
                          ) : (
                            <span className="w-5 h-5 flex items-center justify-center text-gray-500 mt-0.5">•</span>
                          )}
                          <span className="text-base leading-relaxed">{activity}</span>
                        </li>
                      ))}
                    </ul>
                    {day.weather && (
                      <div className="mt-4 ml-14 flex items-center gap-2 text-sm text-gray-400">
                        <Thermometer className="w-4 h-4" />
                        {day.weather}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

function formatItineraryAsText(itinerary: ItineraryDay[]): string {
  let text = 'TRIP ITINERARY\n'
  text += '='.repeat(50) + '\n\n'
  
  itinerary.forEach((day) => {
    text += `Day ${day.day}: ${day.title}\n`
    text += '-'.repeat(50) + '\n'
    day.activities.forEach((activity: string, idx: number) => {
      text += `${idx + 1}. ${activity}\n`
    })
    if (day.weather) {
      text += `\nWeather: ${day.weather}\n`
    }
    text += '\n'
  })
  
  return text
}

function formatItineraryAsHTML(itinerary: ItineraryDay[]): string {
  let html = '<h1>Trip Itinerary</h1>'
  
  itinerary.forEach((day) => {
    html += `<div class="day">`
    html += `<div class="day-title">Day ${day.day}: ${day.title}</div>`
    html += '<div class="activities">'
    day.activities.forEach((activity: string) => {
      html += `<div class="activity">• ${activity}</div>`
    })
    html += '</div>'
    if (day.weather) {
      html += `<div style="margin-top: 10px; color: #64748b;">Weather: ${day.weather}</div>`
    }
    html += '</div>'
  })
  
  return html
}

