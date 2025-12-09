import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Clock, ShoppingBag, TrendingUp, CheckCircle2, Mountain, Users, Snowflake, Compass, Car, UserCircle, Footprints, Building } from 'lucide-react'
import { UserId, UserPersona } from '../types'
import { api } from '../lib/api'

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

interface UserAccountPageProps {
  currentUserId: UserId | string
  onSelectUser: (userId: string, persona: UserPersona | null) => void
}

export function UserAccountPage({ currentUserId, onSelectUser }: UserAccountPageProps) {
  const [personas, setPersonas] = useState<UserPersona[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPersonas()
  }, [])

  const loadPersonas = async () => {
    try {
      const data = await api.getUserPersonas()
      setPersonas(data.personas || [])
    } catch (error) {
      console.error('Failed to load personas:', error)
      // Fallback to default personas if API fails
      setPersonas(getDefaultPersonas())
    } finally {
      setLoading(false)
    }
  }

  const getDefaultPersonas = (): UserPersona[] => {
    return [
      {
        id: 'ultralight_backpacker_sarah',
        name: 'Sarah Martinez',
        avatar_color: 'from-teal-500 to-cyan-500',
        story: 'Planning a 3-week Pacific Crest Trail thru-hike',
        sessions: [
          { goal: 'Research ultralight shelter options', timeframe: '3 days ago', item_count: 12, categories: ['Tents', 'Tarps'] },
          { goal: 'Find lightweight sleep system', timeframe: '2 days ago', item_count: 8, categories: ['Sleeping Bags', 'Pads'] },
          { goal: 'Browse backpacks', timeframe: 'Yesterday', item_count: 15, categories: ['Backpacks'] }
        ],
        total_views: 35,
        total_cart_adds: 3
      },
      {
        id: 'family_camper_mike',
        name: 'Mike Chen',
        avatar_color: 'from-amber-500 to-orange-500',
        story: 'Getting gear for weekend family camping trips',
        sessions: [
          { goal: 'Find a spacious family tent', timeframe: '5 days ago', item_count: 9, categories: ['Tents'] },
          { goal: 'Camp kitchen and cooking gear', timeframe: '3 days ago', item_count: 11, categories: ['Stoves', 'Cookware'] }
        ],
        total_views: 20,
        total_cart_adds: 5
      },
      {
        id: 'winter_mountaineer_alex',
        name: 'Alex Thompson',
        avatar_color: 'from-blue-500 to-indigo-500',
        story: 'Preparing for winter alpine climbing season',
        sessions: [
          { goal: 'Upgrade 4-season tent for alpine', timeframe: '1 week ago', item_count: 6, categories: ['Tents'] },
          { goal: 'Cold weather sleep system', timeframe: '5 days ago', item_count: 7, categories: ['Sleeping Bags', 'Pads'] }
        ],
        total_views: 18,
        total_cart_adds: 4
      },
      {
        id: 'weekend_hiker_emma',
        name: 'Emma Wilson',
        avatar_color: 'from-green-500 to-emerald-500',
        story: 'New to hiking, building out day hike essentials',
        sessions: [
          { goal: 'Day hiking essentials research', timeframe: '4 days ago', item_count: 16, categories: ['Backpacks', 'Hydration'] },
          { goal: 'Revisit favorites', timeframe: 'Yesterday', item_count: 4, categories: ['Backpacks', 'Water Filters'] }
        ],
        total_views: 20,
        total_cart_adds: 1
      },
      {
        id: 'car_camper_david',
        name: 'David Park',
        avatar_color: 'from-purple-500 to-pink-500',
        story: 'Car camping enthusiast, prioritizes comfort and luxury',
        sessions: [
          { goal: 'Luxury camping gear upgrade', timeframe: '6 days ago', item_count: 7, categories: ['Tents', 'Sleeping Bags'] },
          { goal: 'Comfort accessories', timeframe: '3 days ago', item_count: 10, categories: ['Accessories', 'Cookware'] }
        ],
        total_views: 17,
        total_cart_adds: 6
      },
      {
        id: 'user_new',
        name: 'Guest User',
        avatar_color: 'from-gray-500 to-slate-500',
        story: 'First-time visitor, browsing casually',
        sessions: [],
        total_views: 0,
        total_cart_adds: 0
      },
      {
        id: 'user_member',
        name: 'Alex Hiker',
        avatar_color: 'from-emerald-500 to-teal-500',
        story: 'Experienced hiker with ultralight preferences',
        sessions: [
          { goal: 'Ultralight gear browsing', timeframe: '2 days ago', item_count: 13, categories: ['Backpacks', 'Tents'] }
        ],
        total_views: 13,
        total_cart_adds: 2
      },
      {
        id: 'user_business',
        name: 'Casey Campground',
        avatar_color: 'from-orange-500 to-red-500',
        story: 'Campground owner purchasing bulk equipment',
        sessions: [
          { goal: 'Bulk tent purchases', timeframe: '4 days ago', item_count: 11, categories: ['Tents'] },
          { goal: 'Campground amenities', timeframe: 'Yesterday', item_count: 8, categories: ['Cookware', 'Accessories'] }
        ],
        total_views: 19,
        total_cart_adds: 9
      }
    ]
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-400">Loading user personas...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-display font-bold text-white mb-2">
            User Personas
          </h1>
          <p className="text-gray-400">
            Switch between different user profiles to see personalized recommendations based on their browsing history
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {personas.map((user) => (
            <motion.button
              key={user.id}
              onClick={() => onSelectUser(user.id, user)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border-2 transition-all text-left ${
                currentUserId === user.id
                  ? 'border-primary shadow-lg shadow-primary/20'
                  : 'border-slate-700 hover:border-slate-600'
              }`}
            >
              {/* Avatar & Name */}
              <div className="flex items-start gap-4 mb-4">
                {(() => {
                  const IconComponent = PERSONA_ICONS[user.id] || DEFAULT_ICON
                  return (
                    <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${user.avatar_color} flex items-center justify-center flex-shrink-0`}>
                      <IconComponent className="w-8 h-8 text-white" />
                    </div>
                  )
                })()}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-xl font-display font-bold text-white truncate">
                      {user.name}
                    </h3>
                    {currentUserId === user.id && (
                      <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                    )}
                  </div>
                  {currentUserId === user.id && (
                    <span className="inline-block px-2 py-0.5 bg-primary/20 text-primary text-xs font-semibold rounded-full">
                      Active
                    </span>
                  )}
                </div>
              </div>

              {/* Story */}
              <div className="mb-4 p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
                <p className="text-sm text-gray-300 italic">
                  "{user.story}"
                </p>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700/30">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                    <TrendingUp className="w-3 h-3" />
                    <span>Total Views</span>
                  </div>
                  <div className="text-2xl font-bold text-white">{user.total_views}</div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700/30">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                    <ShoppingBag className="w-3 h-3" />
                    <span>Cart Adds</span>
                  </div>
                  <div className="text-2xl font-bold text-primary">{user.total_cart_adds}</div>
                </div>
              </div>

              {/* Recent Sessions */}
              {user.sessions.length > 0 ? (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Recent Shopping Sessions
                  </h4>
                  <div className="space-y-2">
                    {user.sessions.slice(0, 3).map((session, idx) => (
                      <div key={idx} className="bg-slate-900/30 rounded-lg p-3 border border-slate-800/50">
                        <div className="flex items-start gap-2">
                          <Clock className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-300 font-medium mb-1">
                              {session.goal}
                            </p>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs text-gray-500">{session.timeframe}</span>
                              <span className="text-xs text-gray-600">•</span>
                              <span className="text-xs text-gray-500">{session.item_count} items viewed</span>
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {session.categories.map((cat) => (
                                <span key={cat} className="text-xs bg-slate-800 text-gray-400 px-2 py-0.5 rounded border border-slate-700">
                                  {cat}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500 text-sm">
                  No browsing history yet
                </div>
              )}
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  )
}

