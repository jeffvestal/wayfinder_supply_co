import { useEffect, useState } from 'react'
import { ProductCard } from './ProductCard'
import { HeroSection } from './HeroSection'
import { Product, UserId } from '../types'
import { api } from '../lib/api'
import { Loader2, Filter } from 'lucide-react'
import { motion } from 'framer-motion'

// Import actual generated products for demo mode
import generatedProducts from '../../../generated_products/products.json'

interface StorefrontProps {
  userId: UserId
}

const categories = ['All', 'Camping', 'Hiking', 'Climbing', 'Water Sports', 'Winter']

// Use real generated products as fallback when backend is unavailable
const MOCK_PRODUCTS: Product[] = generatedProducts as Product[]

export function Storefront({ userId }: StorefrontProps) {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [usingMockData, setUsingMockData] = useState(false)

  useEffect(() => {
    loadProducts()
  }, [selectedCategory])

  const loadProducts = async () => {
    try {
      setLoading(true)
      const category = selectedCategory === 'All' ? undefined : selectedCategory.toLowerCase()
      const data = await api.getProducts(category, 12)
      setProducts(data.products)
      setUsingMockData(false)
    } catch (err) {
      // Use mock data when backend is unavailable
      console.warn('Backend unavailable, using mock data')
      const category = selectedCategory === 'All' ? undefined : selectedCategory.toLowerCase()
      const filteredMock = category 
        ? MOCK_PRODUCTS.filter(p => p.category === category)
        : MOCK_PRODUCTS
      setProducts(filteredMock)
      setUsingMockData(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-slate-950 min-h-screen">
      {/* Hero Section */}
      <HeroSection />

      {/* Content Section - Dark theme */}
      <div className="relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          {/* Mock Data Banner */}
          {usingMockData && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-center gap-3"
            >
              <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <p className="text-amber-200 text-sm">
                <span className="font-semibold">Demo Mode:</span> Showing sample products (backend unavailable)
              </p>
            </motion.div>
          )}

          {/* Category Filters */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="flex items-center gap-3 mb-6">
              <Filter className="w-5 h-5 text-gray-400" />
              <h2 className="text-2xl font-display font-bold text-white">Shop by Category</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {categories.map((category, index) => (
                <motion.button
                  key={category}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-6 py-2.5 rounded-full font-medium transition-all ${
                    selectedCategory === category
                      ? 'bg-primary text-white shadow-lg shadow-primary/30'
                      : 'bg-slate-800 text-gray-300 hover:bg-slate-700 border border-slate-700'
                  }`}
                >
                  {category}
                </motion.button>
              ))}
            </div>
          </motion.div>

          {/* Products Grid */}
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            >
              {products.map((product, index) => (
                <motion.div
                  key={product.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <ProductCard product={product} userId={userId} />
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}


