import { motion } from 'framer-motion'
import { ArrowRight, MapPin, Calendar, Mountain } from 'lucide-react'

export function HeroSection() {
  const navigate = () => {
    // Navigate to trip planner - will be handled by App state
    const event = new CustomEvent('navigate', { detail: 'trip-planner' })
    window.dispatchEvent(event)
  }

  return (
    <div className="relative w-full min-h-[700px] overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=2000&q=80')`,
        }}
      />
      
      {/* Dark overlay for text readability */}
      <div className="absolute inset-0 bg-gradient-to-r from-slate-950/90 via-slate-900/80 to-slate-900/60" />
      
      {/* Accent gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-primary/10" />
      
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center">
        <div className="max-w-3xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-6xl md:text-7xl font-display font-bold mb-6 leading-tight">
              <span className="text-white">Gear Up for</span>
              <br />
              <span className="text-gradient">Your Next Adventure</span>
            </h1>
          </motion.div>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl text-gray-300 mb-8 leading-relaxed"
          >
            AI-powered trip planning meets premium outdoor gear. Get personalized recommendations 
            for your perfect adventure.
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="flex flex-wrap gap-4"
          >
            <button
              onClick={navigate}
              className="group bg-primary hover:bg-primary-dark text-white font-semibold px-8 py-4 rounded-lg transition-all duration-300 flex items-center gap-2 shadow-lg shadow-primary/20 hover:shadow-primary/40 hover:scale-105"
            >
              Plan Your Adventure
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="glass text-white font-semibold px-8 py-4 rounded-lg transition-all duration-300 hover:bg-slate-800/80">
              Browse Gear
            </button>
          </motion.div>
          
          {/* Quick stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="mt-12 flex flex-wrap gap-8"
          >
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <Mountain className="w-6 h-6 text-primary" />
              </div>
              <div>
                <div className="text-2xl font-display font-bold text-white">10K+</div>
                <div className="text-sm text-gray-400">Products</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <MapPin className="w-6 h-6 text-primary" />
              </div>
              <div>
                <div className="text-2xl font-display font-bold text-white">500+</div>
                <div className="text-sm text-gray-400">Destinations</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <Calendar className="w-6 h-6 text-primary" />
              </div>
              <div>
                <div className="text-2xl font-display font-bold text-white">24/7</div>
                <div className="text-sm text-gray-400">AI Support</div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
      
      {/* Bottom gradient fade to dark */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none" />
    </div>
  )
}

