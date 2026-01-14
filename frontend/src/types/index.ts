export interface Product {
  id: string;
  title: string;
  brand: string;
  description: string;
  category: string;
  subcategory: string;
  price: number;
  tags: string[];
  image_url: string;
  explanation?: string;
  average_rating?: number;
  review_count?: number;
  attributes?: {
    temp_rating_f?: number;
    weight_lb?: number;
    season?: string;
    capacity?: number;
    capacity_l?: number;
    fuel_type?: string;
    waterproof?: boolean;
    length_cm?: number;
    width_mm?: number;
  };
}

export interface CartItem {
  product_id: string;
  title: string;
  price: number;
  quantity: number;
  subtotal: number;
  image_url: string;
}

export interface Cart {
  items: CartItem[];
  subtotal: number;
  discount: number;
  total: number;
  loyalty_perks: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  tool_calls?: ToolCall[];
}

export interface ToolCall {
  id: string;
  name: string;
  parameters: Record<string, any>;
  status: 'pending' | 'completed' | 'error';
  result?: any;
}

export interface ThoughtTraceEvent {
  event: string;
  data: any;
  timestamp: Date;
}

export type UserId = 'user_new' | 'user_member' | 'user_business' | 
  'ultralight_backpacker_sarah' | 'family_camper_mike' | 'winter_mountaineer_alex' | 
  'weekend_hiker_emma' | 'car_camper_david' | string;

export interface User {
  id: UserId;
  name: string;
  loyalty_tier: string;
}

export interface Review {
  id: string;
  product_id: string;
  user_id: string;
  rating: number;
  title: string;
  text: string;
  timestamp: Date;
  verified_purchase: boolean;
}

export interface ItineraryDay {
  day: number;
  title: string;
  activities: string[];
  weather?: string;
  gear_needed?: string[];
}

export interface SuggestedProduct {
  id: string;
  title: string;
  price: number;
  image_url?: string;
  reason?: string;
}

export interface UserPersona {
  id: string;
  name: string;
  avatar_color: string;
  story: string;
  sessions: Array<{
    goal: string;
    timeframe: string;
    item_count: number;
    categories: string[];
  }>;
  total_views: number;
  total_cart_adds: number;
}

