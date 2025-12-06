// Dynamically determine API URL based on where frontend is loaded from
function getApiUrl(): string {
  // Check for explicit env var first
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // In browser, determine URL dynamically
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    
    // Instruqt URLs look like: https://host-1-3000-{sandbox}.env.play.instruqt.com
    // We need to change port 3000 to 8000
    if (hostname.includes('-3000-')) {
      return `${protocol}//${hostname.replace('-3000-', '-8000-')}`;
    }
    
    // Local development: frontend on 3000, backend on 8000
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `${protocol}//${hostname}:8000`;
    }
    
    // Same host, different port
    return `${protocol}//${hostname}:8000`;
  }
  
  // Fallback for SSR or other environments
  return 'http://localhost:8000';
}

const API_URL = getApiUrl();

export interface StreamEvent {
  event: string;
  data: string;
}

export const api = {
  async streamChat(
    message: string,
    userId: string,
    onEvent: (event: StreamEvent) => void
  ): Promise<void> {
    const url = new URL(`${API_URL}/api/chat`);
    url.searchParams.set('message', message);
    url.searchParams.set('user_id', userId);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onEvent({
              event: data.event || 'message',
              data: JSON.stringify(data.data || {}),
            });
          } catch (e) {
            // Skip invalid JSON
          }
        } else if (line.startsWith('event: ')) {
          // Handle event type
        }
      }
    }
  },

  async getProducts(category?: string, limit = 20): Promise<{ products: any[]; total: number }> {
    const url = new URL(`${API_URL}/api/products`);
    if (category) url.searchParams.set('category', category);
    url.searchParams.set('limit', limit.toString());

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getProduct(id: string): Promise<any> {
    const response = await fetch(`${API_URL}/api/products/${id}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getCart(userId: string, loyaltyTier?: string): Promise<any> {
    const url = new URL(`${API_URL}/api/cart`);
    url.searchParams.set('user_id', userId);
    if (loyaltyTier) url.searchParams.set('loyalty_tier', loyaltyTier);

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async addToCart(userId: string, productId: string, quantity = 1): Promise<void> {
    const response = await fetch(`${API_URL}/api/cart?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_id: productId,
        quantity,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  },

  async clearCart(userId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/cart?user_id=${userId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  },

  async removeFromCart(userId: string, productId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/cart/item/${productId}?user_id=${userId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  },
};

