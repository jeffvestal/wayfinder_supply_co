export const TOOL_STATUS_MESSAGES: Record<string, string> = {
  'tool-workflow-check-trip-safety': 'Checking weather conditions...',
  'tool-workflow-get-customer-profile': 'Looking up your preferences...',
  'tool-search-product-search': 'Scanning the catalog...',
  'tool-esql-get-user-affinity': 'Reviewing your browsing history...',
};

export function getToolStatusMessage(toolId: string): string {
  return TOOL_STATUS_MESSAGES[toolId] || 'Planning your adventure...';
}

