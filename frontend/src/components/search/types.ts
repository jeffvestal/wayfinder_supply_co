import { ChatMessage, UserId } from '../../types'

// Agent step for thought trace display
export interface AgentStep {
  type: 'reasoning' | 'tool_call';
  reasoning?: string;
  tool_call_id?: string;
  tool_id?: string;
  params?: any;
  results?: any[];
}

// Extended chat message with agent steps and status
export interface ExtendedChatMessage extends ChatMessage {
  steps?: AgentStep[];
  status?: 'thinking' | 'working' | 'typing' | 'complete';
}

// Search mode type
export type SearchMode = 'chat' | 'hybrid' | 'lexical'

// Demo query type
export type DemoQueryType = 'keyword' | 'semantic' | 'usecase'

// Demo query configuration
export interface DemoQuery {
  query: string;
  label: string;
  description: string;
  icon: string;
  winner: string;
}

// Demo queries configuration
export const DEMO_QUERIES: Record<DemoQueryType, DemoQuery> = {
  keyword: {
    query: "ultralight backpacking tent",
    label: "Keyword Match",
    description: "Exact terms that BM25 handles well",
    icon: "📝",
    winner: "Lexical ≈ Hybrid"
  },
  semantic: {
    query: "gear to keep my feet dry on slippery mountain trails",
    label: "Conceptual",
    description: "No exact keywords - semantic understanding needed",
    icon: "💡",
    winner: "Hybrid Wins"
  },
  usecase: {
    query: "I'm planning a 3-day backpacking trip in Yosemite next month. What tent should I bring?",
    label: "Task-Based",
    description: "Complex intent requiring reasoning",
    icon: "🎯",
    winner: "Agent Excels"
  }
}

// Fallback product image SVG
export const FALLBACK_PRODUCT_IMAGE =
  "data:image/svg+xml,%3Csvg%20xmlns%3D'http%3A//www.w3.org/2000/svg'%20width%3D'200'%20height%3D'200'%20viewBox%3D'0%200%20200%20200'%3E%3Crect%20width%3D'200'%20height%3D'200'%20fill%3D'%231f2937'/%3E%3Cpath%20d%3D'M70%2080h60l-6%2060H76z'%20fill%3D'%23374151'/%3E%3Cpath%20d%3D'M85%2080c0-8%206-14%2015-14s15%206%2015%2014'%20fill%3D'none'%20stroke%3D'%234b5563'%20stroke-width%3D'8'%20stroke-linecap%3D'round'/%3E%3Ctext%20x%3D'100'%20y%3D'165'%20text-anchor%3D'middle'%20font-family%3D'system-ui%2C%20-apple-system%2C%20Segoe%20UI%2C%20Roboto'%20font-size%3D'14'%20fill%3D'%239ca3af'%3ENo%20image%3C/text%3E%3C/svg%3E"

// Persona display names
export const PERSONA_NAMES: Record<string, string> = {
  'user_member': '🏔️ Alex Hiker - Experienced Member',
  'user_business': '👔 Mike - Family Adventurer',
  'user_new': '🆕 New Visitor',
  'ultralight_backpacker_sarah': '👤 Sarah Martinez',
  'family_camper_mike': '👔 Mike Chen',
  'winter_mountaineer_alex': '🏔️ Alex Rivera',
  'water_sports_jordan': '🌊 Jordan Smith',
  'user_guest': '🆕 Guest User',
}

export function getPersonaName(id: UserId): string {
  return PERSONA_NAMES[id] || id
}

