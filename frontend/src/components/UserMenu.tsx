import { useState, useEffect, useRef } from 'react'
import { ChevronDown, Mountain, Users, Snowflake, Compass, Car, UserCircle, Footprints, Building, ArrowRight, Trash2, Settings } from 'lucide-react'
import { api } from '../lib/api'
import { ClickstreamEventsModal } from './ClickstreamEventsModal'
import { UserPersona } from '../types'

interface UserMenuProps {
  currentUserId: string
  currentPersona: UserPersona | null
  onSwitchUser: () => void
  onClearHistory?: () => void
  onOpenSettings?: () => void
}

// Icon mapping for personas
const PERSONA_ICONS: Record<string, any> = {
  'ultralight_backpacker_sarah': Mountain,
  'family_camper_mike': Users,
  'winter_mountaineer_alex': Snowflake,
  'weekend_hiker_emma': Compass,
  'car_camper_david': Car,
  'user_new': UserCircle,
  'user_member': Footprints,
  'user_business': Building,
}

const DEFAULT_ICON = UserCircle

export function UserMenu({ currentUserId, currentPersona, onSwitchUser, onClearHistory, onOpenSettings }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [liveStats, setLiveStats] = useState<{ total_views: number; total_cart_adds: number } | null>(null)
  const [clearing, setClearing] = useState(false)
  const [eventsModalOpen, setEventsModalOpen] = useState(false)
  const [eventsType, setEventsType] = useState<'view_item' | 'add_to_cart'>('view_item')
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [isOpen])

  // Get icon for current persona
  const IconComponent = PERSONA_ICONS[currentUserId] || DEFAULT_ICON
  const avatarColor = currentPersona?.avatar_color || 'from-gray-500 to-slate-500'
  const displayName = currentPersona?.name || 'Guest User'
  const story = currentPersona?.story || 'First-time visitor'

  // Load live stats for guest user when dropdown opens
  useEffect(() => {
    if (isOpen && currentUserId === 'user_new') {
      loadLiveStats()
      // Poll for updates every 2 seconds while open
      const interval = setInterval(loadLiveStats, 2000)
      return () => clearInterval(interval)
    } else {
      setLiveStats(null)
    }
  }, [isOpen, currentUserId])

  const loadLiveStats = async () => {
    if (currentUserId === 'user_new') {
      try {
        const stats = await api.getUserStats(currentUserId)
        setLiveStats(stats)
      } catch (err) {
        console.error('Failed to load live stats:', err)
      }
    }
  }

  const handleClearHistory = async () => {
    if (!onClearHistory) return
    
    try {
      setClearing(true)
      await api.clearUserHistory(currentUserId)
      setLiveStats({ total_views: 0, total_cart_adds: 0 })
      onClearHistory()
    } catch (err) {
      console.error('Failed to clear history:', err)
    } finally {
      setClearing(false)
    }
  }

  // Use live stats for guest user, persona stats for others
  const displayViews = currentUserId === 'user_new' && liveStats 
    ? liveStats.total_views 
    : currentPersona?.total_views || 0
  const displayCartAdds = currentUserId === 'user_new' && liveStats 
    ? liveStats.total_cart_adds 
    : currentPersona?.total_cart_adds || 0

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 glass px-4 py-2 rounded-lg transition-all hover:bg-white/10"
      >
        <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${avatarColor} flex items-center justify-center flex-shrink-0`}>
          <IconComponent className="w-4 h-4 text-white" />
        </div>
        <span className="text-sm font-medium text-white hidden sm:inline">{displayName}</span>
        <ChevronDown className={`w-4 h-4 text-gray-300 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-80 glass rounded-xl shadow-2xl z-20 border border-white/20 overflow-hidden">
            {/* Current User Info */}
            {currentPersona && (
              <div className="p-4 border-b border-white/10">
                <div className="flex items-start gap-3 mb-3">
                  <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${avatarColor} flex items-center justify-center flex-shrink-0`}>
                    <IconComponent className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-white mb-1">{displayName}</h3>
                    <p className="text-xs text-gray-400 italic line-clamp-2">{story}</p>
                  </div>
                </div>
                
                {/* Stats */}
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <button
                    onClick={() => {
                      setEventsType('view_item')
                      setEventsModalOpen(true)
                    }}
                    disabled={currentUserId !== 'user_new' || displayViews === 0}
                    className="bg-slate-900/50 rounded-lg p-2 border border-slate-700/30 hover:border-slate-600/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-left"
                  >
                    <div className="text-xs text-gray-400 mb-0.5">Views</div>
                    <div className="text-lg font-bold text-white">{displayViews}</div>
                  </button>
                  <button
                    onClick={() => {
                      setEventsType('add_to_cart')
                      setEventsModalOpen(true)
                    }}
                    disabled={currentUserId !== 'user_new' || displayCartAdds === 0}
                    className="bg-slate-900/50 rounded-lg p-2 border border-slate-700/30 hover:border-slate-600/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-left"
                  >
                    <div className="text-xs text-gray-400 mb-0.5">Cart Adds</div>
                    <div className="text-lg font-bold text-primary">{displayCartAdds}</div>
                  </button>
                </div>
              </div>
            )}

            {/* Clear History Button (only for guest user) */}
            {currentUserId === 'user_new' && (displayViews > 0 || displayCartAdds > 0) && (
              <div className="p-2 border-t border-white/10">
                <button
                  onClick={handleClearHistory}
                  disabled={clearing}
                  className="w-full px-4 py-2.5 rounded-lg flex items-center justify-center gap-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-all border border-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Trash2 className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    {clearing ? 'Clearing...' : 'Clear Browsing History'}
                  </span>
                </button>
              </div>
            )}

            {/* Settings */}
            {onOpenSettings && (
              <div className="p-2 border-t border-white/10">
                <button
                  onClick={() => {
                    setIsOpen(false)
                    onOpenSettings()
                  }}
                  className="w-full px-4 py-2.5 rounded-lg flex items-center gap-2 text-gray-300 hover:text-white hover:bg-white/10 transition-all"
                >
                  <Settings className="w-4 h-4" />
                  <span className="text-sm font-medium">Vision Settings</span>
                </button>
              </div>
            )}

            {/* Switch User Button */}
            <div className="p-2 border-t border-white/10">
              <button
                onClick={() => {
                  setIsOpen(false)
                  onSwitchUser()
                }}
                className="w-full px-4 py-3 rounded-lg flex items-center justify-between bg-primary/20 hover:bg-primary/30 text-primary transition-all border border-primary/30 group"
              >
                <span className="text-sm font-medium">Switch User</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </>
      )}

      {/* Events Modal */}
      <ClickstreamEventsModal
        userId={currentUserId}
        action={eventsType}
        title={eventsType === 'view_item' ? 'Product Views' : 'Cart Additions'}
        isOpen={eventsModalOpen}
        onClose={() => setEventsModalOpen(false)}
      />
    </div>
  )
}
