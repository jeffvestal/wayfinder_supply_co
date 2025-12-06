import { useState } from 'react'
import { User, UserId } from '../types'
import { ChevronDown, User as UserIcon } from 'lucide-react'

interface UserSwitcherProps {
  currentUser: UserId
  users: Record<UserId, User>
  onUserChange: (userId: UserId) => void
}

export function UserSwitcher({ currentUser, users, onUserChange }: UserSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false)
  const current = users[currentUser]

  const getTierBadge = (tier: string) => {
    if (tier === 'platinum') {
      return <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded">Platinum</span>
    }
    if (tier === 'business') {
      return <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded">Business</span>
    }
    return <span className="text-xs bg-gray-500/20 text-gray-300 px-2 py-0.5 rounded">New</span>
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 glass px-4 py-2 rounded-lg transition-all hover:bg-white/10"
      >
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
          <UserIcon className="w-4 h-4 text-primary" />
        </div>
        <span className="text-sm font-medium text-white hidden sm:inline">{current.name}</span>
        {getTierBadge(current.loyalty_tier)}
        <ChevronDown className={`w-4 h-4 text-gray-300 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-64 glass rounded-xl shadow-2xl z-20 border border-white/20">
            <div className="p-2">
              {Object.values(users).map((user) => (
                <button
                  key={user.id}
                  onClick={() => {
                    onUserChange(user.id)
                    setIsOpen(false)
                  }}
                  className={`w-full text-left px-4 py-3 rounded-lg flex items-center justify-between transition-all ${
                    currentUser === user.id
                      ? 'bg-primary/20 text-primary'
                      : 'hover:bg-white/5 text-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      currentUser === user.id ? 'bg-primary/30' : 'bg-white/10'
                    }`}>
                      <UserIcon className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-medium">{user.name}</span>
                  </div>
                  {getTierBadge(user.loyalty_tier)}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}


