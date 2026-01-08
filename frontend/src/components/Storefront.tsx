import { useEffect, useState } from 'react'
import { ProductCard } from './ProductCard'
import { ProductDetailModal } from './ProductDetailModal'
import { HeroSection } from './HeroSection'
import { WorkshopProgress } from './WorkshopProgress'
import { Product, UserId } from '../types'
import { api } from '../lib/api'
import { Loader2, Filter } from 'lucide-react'
import { motion } from 'framer-motion'

interface StorefrontProps {
  userId: UserId
  onStartChat?: (productName: string, tag: string) => void
}

const categories = ['All', 'Camping', 'Hiking', 'Climbing', 'Water Sports', 'Winter']

// Inline mock products for demo mode (used when backend is unavailable)
const MOCK_PRODUCTS: Product[] = [
  {
    id: 'WF-CAM-TEN-001',
    title: 'Wayfinder Basecamp 4-Season Tent',
    description: 'A rugged 4-season tent designed for extreme conditions. Features reinforced poles, waterproof fabric, and excellent ventilation.',
    category: 'camping',
    subcategory: 'tents',
    price: 549.99,
    brand: 'Wayfinder Supply',
    tags: ['expedition', '4-season'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-CAM-TEN-57250EC4.jpg'
  },
  {
    id: 'WF-CAM-SLE-002',
    title: 'Summit Pro Arctic Sleeping Bag',
    description: 'Rated to -20°F, this mummy-style sleeping bag keeps you warm in the harshest conditions with premium down insulation.',
    category: 'camping',
    subcategory: 'sleeping_bags',
    price: 399.99,
    brand: 'Summit Pro',
    tags: ['expedition', 'cold-weather'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-CAM-SLE-891AFFD1.jpg'
  },
  {
    id: 'WF-HIK-BAC-003',
    title: 'TrailBlazer 65L Expedition Pack',
    description: 'Built for multi-day adventures, featuring adjustable torso, hip belt pockets, and integrated rain cover.',
    category: 'hiking',
    subcategory: 'backpacks',
    price: 279.99,
    brand: 'TrailBlazer',
    tags: ['ultralight', 'backpacking'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-HIK-BAC-F16CA437.jpg'
  },
  {
    id: 'WF-HIK-TRE-004',
    title: 'Summit Pro Carbon Trekking Poles',
    description: 'Ultralight carbon fiber trekking poles with ergonomic cork grips and quick-lock adjustment.',
    category: 'hiking',
    subcategory: 'trekking_poles',
    price: 149.99,
    brand: 'Summit Pro',
    tags: ['ultralight', 'professional'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-HIK-TRE-5777D61A.jpg'
  },
  {
    id: 'WF-CLM-HAR-005',
    title: 'Summit Pro Ascent Harness',
    description: 'Lightweight yet durable climbing harness with gear loops and adjustable leg loops for all-day comfort.',
    category: 'climbing',
    subcategory: 'harnesses',
    price: 89.99,
    brand: 'Summit Pro',
    tags: ['professional', 'lightweight'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-CLI-HAR-000D5F37.jpg'
  },
  {
    id: 'WF-WAT-KAY-006',
    title: 'Pacific Tide Touring Kayak',
    description: 'Stable and fast sea kayak perfect for coastal exploration and multi-day paddling trips.',
    category: 'water sports',
    subcategory: 'kayaks',
    price: 1299.99,
    brand: 'Pacific Tide',
    tags: ['professional', 'touring'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-WAT-KAY-769FDC85.jpg'
  },
  {
    id: 'WF-WIN-SKI-007',
    title: 'Alpine Edge All-Mountain Skis',
    description: 'Versatile skis for groomed runs and powder days, featuring rocker-camber-rocker profile.',
    category: 'winter',
    subcategory: 'skis',
    price: 699.99,
    brand: 'Alpine Edge',
    tags: ['all-mountain', 'intermediate'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-WIN-SKI-09F23736.jpg'
  },
  {
    id: 'WF-WIN-SNO-008',
    title: 'Wayfinder Backcountry Snowshoes',
    description: 'Lightweight aluminum snowshoes with aggressive crampons for steep terrain.',
    category: 'winter',
    subcategory: 'snowshoes',
    price: 199.99,
    brand: 'Wayfinder Supply',
    tags: ['backcountry', 'lightweight'],
    image_url: 'https://storage.googleapis.com/wayfinder_supply_co/products/WF-WIN-SNO-370005B0.jpg'
  }
]

export function Storefront({ userId, onStartChat }: StorefrontProps) {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [usingMockData, setUsingMockData] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)

  const handleTagClick = (productName: string, tag: string) => {
    setSelectedProduct(null) // Close the modal
    onStartChat?.(productName, tag)
  }

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
      <div id="products-section" className="relative z-10">
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
                  <ProductCard 
                    product={product} 
                    userId={userId} 
                    onClick={() => setSelectedProduct(product)}
                  />
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>

      {/* Product Detail Modal */}
      {selectedProduct && (
        <ProductDetailModal
          product={selectedProduct}
          userId={userId}
          onClose={() => setSelectedProduct(null)}
          onTagClick={handleTagClick}
        />
      )}

      {/* Workshop Progress Sidebar */}
      <WorkshopProgress />
    </div>
  )
}


