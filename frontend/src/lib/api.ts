// Dynamically determine API URL based on where frontend is loaded from
function getApiUrl(): string {
  // Check for explicit env var first
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // In browser, determine URL dynamically
  if (typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location;
    
    // If frontend is served from port 8000, backend is same origin (unified serving)
    // This works for: Instruqt (unified), Cloud Run, K8s, production deployments
    if (hostname.includes('-8000-') || port === '8000') {
      return ''; // Same origin - use relative URLs
    }
    
    // Instruqt with separate tabs (legacy): host-1-3000-{sandbox} → host-1-8000-{sandbox}
    if (hostname.includes('-3000-')) {
      return `${protocol}//${hostname.replace('-3000-', '-8000-')}`;
    }
    
    // Local development: frontend on 3000, backend on 8000
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      if (port === '3000') {
        return `${protocol}//${hostname}:8000`;
      }
      // Already on port 8000 or no port specified
      return '';
    }
    
    // Production/other: assume same origin
    return '';
  }
  
  // Fallback for SSR or other environments
  return 'http://localhost:8000';
}

const API_URL = getApiUrl();

// Helper to create URL that works with both absolute and relative (empty) API_URL
function createApiUrl(path: string): URL {
  if (API_URL) {
    return new URL(`${API_URL}${path}`);
  }
  // When API_URL is empty, use current origin as base for relative URL
  return new URL(path, window.location.origin);
}

export interface StreamEvent {
  type: string;
  data: any;
}

export interface TripContext {
  destination: string | null;
  dates: string | null;
  activity: string | null;
}

export interface ExtractedProduct {
  name: string;
  price: number;
  category: string;
  reason: string;
}

export interface ExtractedItinerary {
  day: number;
  title: string;
  distance?: string;
  activities: string[];
}

export interface TripEntities {
  products: ExtractedProduct[];
  itinerary: ExtractedItinerary[];
  safety_notes: string[];
  weather: { high: number; low: number; conditions: string } | null;
}

export const api = {
  async parseTripContext(message: string): Promise<TripContext> {
    const url = createApiUrl('/api/parse-trip-context');
    url.searchParams.set('message', message);

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async streamChat(
    message: string,
    userId: string,
    onEvent: (event: StreamEvent) => void
  ): Promise<void> {
    const url = createApiUrl('/api/chat');
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

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const eventData = JSON.parse(line.slice(6));
            onEvent(eventData);
          } catch (e) {
            // Skip invalid JSON
          }
        }
      }
    }
  },

  async getProducts(category?: string, limit = 20): Promise<{ products: any[]; total: number }> {
    const url = createApiUrl('/api/products');
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

  async searchProducts(query: string, limit = 5): Promise<{ products: any[]; total: number }> {
    const url = createApiUrl('/api/products/search');
    url.searchParams.set('q', query);
    url.searchParams.set('limit', limit.toString());

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getCart(userId: string, loyaltyTier?: string): Promise<any> {
    const url = createApiUrl('/api/cart');
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
    const response = await fetch(`${API_URL}/api/cart/${productId}?user_id=${userId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  },

  async updateCartQuantity(userId: string, productId: string, quantity: number): Promise<void> {
    const response = await fetch(`${API_URL}/api/cart/${productId}?user_id=${userId}&quantity=${quantity}`, {
      method: 'PUT',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  },

  async getProductReviews(productId: string, limit = 20, offset = 0): Promise<{ reviews: any[]; total: number }> {
    const url = createApiUrl(`/api/products/${productId}/reviews`);
    url.searchParams.set('limit', limit.toString());
    url.searchParams.set('offset', offset.toString());

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async submitReview(productId: string, userId: string, rating: number, title: string, text: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/products/${productId}/reviews?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        rating,
        title,
        text,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  },

  async createOrder(userId: string, shippingAddress: any, paymentInfo: any): Promise<{ order_id: string; confirmation_number: string }> {
    const response = await fetch(`${API_URL}/api/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        shipping_address: shippingAddress,
        payment_info: paymentInfo,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async extractItinerary(tripPlan: string): Promise<{ days: Array<{ day: number; title: string; activities: string[] }> }> {
    const url = createApiUrl('/api/extract-itinerary');
    url.searchParams.set('trip_plan', tripPlan);

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Return empty structure on error rather than throwing
      return { days: [] };
    }

    return response.json();
  },

  async extractTripEntities(tripPlan: string): Promise<TripEntities> {
    const url = createApiUrl('/api/extract-trip-entities');
    url.searchParams.set('trip_plan', tripPlan);

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Return empty structure on error rather than throwing
      return {
        products: [],
        itinerary: [],
        safety_notes: [],
        weather: null,
      };
    }

    return response.json();
  },

  async getUserPersonas(): Promise<{ personas: any[] }> {
    const response = await fetch(`${API_URL}/api/users/personas`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async trackEvent(
    userId: string,
    action: 'view_item' | 'add_to_cart' | 'click_tag',
    productId?: string,
    tag?: string
  ): Promise<void> {
    // Fire and forget - don't await, don't throw errors
    fetch(`${API_URL}/api/clickstream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        action,
        product_id: productId,
        tag,
      }),
    }).catch((err) => {
      // Silently fail - tracking shouldn't break the app
      console.error('Failed to track event:', err);
    });
  },

  async clearUserHistory(userId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/clickstream/${userId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  },

  async getUserStats(userId: string): Promise<{ total_views: number; total_cart_adds: number; total_events: number }> {
    const response = await fetch(`${API_URL}/api/clickstream/${userId}/stats`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getUserEvents(
    userId: string,
    action: 'view_item' | 'add_to_cart' = 'view_item'
  ): Promise<{
    events: Array<{
      product_id: string;
      product_name: string;
      timestamp: string;
      action: string;
    }>;
  }> {
    const url = createApiUrl(`/api/clickstream/${userId}/events`);
    url.searchParams.set('action', action);

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async lexicalSearch(query: string, limit = 10, userId?: string): Promise<{ products: any[]; total: number; personalized?: boolean }> {
    const url = createApiUrl('/api/products/search/lexical');
    url.searchParams.set('q', query);
    url.searchParams.set('limit', limit.toString());
    if (userId) {
      url.searchParams.set('user_id', userId);
    }

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async hybridSearch(query: string, limit = 10, userId?: string): Promise<{ products: any[]; total: number; personalized?: boolean }> {
    const url = createApiUrl('/api/products/search/hybrid');
    url.searchParams.set('q', query);
    url.searchParams.set('limit', limit.toString());
    if (userId) {
      url.searchParams.set('user_id', userId);
    }

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async generateTripReportPdf(
    userName: string,
    destination: string,
    dates: string,
    itinerary: any[],
    suggestedProducts: any[],
    otherRecommendedItems: string[]
  ): Promise<Response> {
    const response = await fetch(`${API_URL}/api/reports/trip-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_name: userName,
        destination,
        dates,
        itinerary,
        suggested_products: suggestedProducts,
        other_recommended_items: otherRecommendedItems,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response;
  },
};
