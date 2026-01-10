export const TOOL_STATUS_MESSAGES: Record<string, string> = {
  'tool-workflow-check-trip-safety': 'Checking weather conditions...',
  'tool-workflow-get-customer-profile': 'Looking up your preferences...',
  'tool-search-product-search': 'Scanning the catalog...',
  'tool-esql-get-user-affinity': 'Reviewing your browsing history...',
};

export function getToolStatusMessage(toolId: string): string {
  return TOOL_STATUS_MESSAGES[toolId] || 'Planning your adventure...';
}

export const NARRATION_MESSAGES: Record<string, { message: string; icon: string }> = {
  'lexical_search': {
    message: 'Searching with BM25 keyword matching...',
    icon: '🔍'
  },
  'hybrid_search': {
    message: 'Combining semantic + keyword search...',
    icon: '🧠'
  },
  'agent_start': {
    message: 'AI Agent analyzing your request...',
    icon: '🤖'
  },
  'tool_weather': {
    message: 'Checking weather conditions...',
    icon: '🌤️'
  },
  'tool_profile': {
    message: 'Looking up customer profile...',
    icon: '👤'
  },
  'tool_search': {
    message: 'Searching product catalog...',
    icon: '📦'
  },
  'tool_affinity': {
    message: 'Analyzing browsing preferences...',
    icon: '📊'
  },
  'personalized': {
    message: 'Results personalized for your style!',
    icon: '✨'
  },
}

