# API Reference

## Backend API

Base URL: `http://localhost:8000` (local) or `http://host-1:8000` (Instruqt)

### Chat Endpoints

#### POST /api/chat

Stream chat messages to Agent Builder.

**Query Parameters**:
- `message` (required): The chat message
- `user_id` (optional): User ID (default: "user_new")
- `agent_id` (optional): Agent ID (default: "trip-planner-agent")

**Response**: Server-Sent Events (SSE) stream

**Example**:
```bash
curl -X POST "http://localhost:8000/api/chat?message=I'm%20going%20camping%20in%20the%20Rockies&user_id=user_member"
```

#### GET /api/chat/health

Health check for chat endpoint.

**Response**:
```json
{
  "status": "healthy",
  "kibana": "connected"
}
```

### Product Endpoints

#### GET /api/products

List products.

**Query Parameters**:
- `category` (optional): Filter by category
- `limit` (optional): Max results (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "products": [...],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

#### GET /api/products/{product_id}

Get single product by ID.

**Response**:
```json
{
  "id": "WF-CAM-SLE-ABC123",
  "title": "Wayfinder Inferno 0° Sleeping Bag",
  "brand": "Wayfinder Supply",
  "description": "...",
  "price": 349.99,
  ...
}
```

#### GET /api/products/search

Semantic search for products.

**Query Parameters**:
- `q` (required): Search query
- `limit` (optional): Max results (default: 20)

**Response**:
```json
{
  "products": [...],
  "total": 10,
  "query": "warm sleeping bag"
}
```

### Cart Endpoints

#### POST /api/cart

Add item to cart.

**Query Parameters**:
- `user_id` (required): User ID

**Body**:
```json
{
  "product_id": "WF-CAM-SLE-ABC123",
  "quantity": 1
}
```

#### GET /api/cart

Get cart contents.

**Query Parameters**:
- `user_id` (required): User ID
- `loyalty_tier` (optional): Loyalty tier for discounts

**Response**:
```json
{
  "items": [...],
  "subtotal": 349.99,
  "discount": 34.99,
  "total": 315.00,
  "loyalty_perks": ["Free overnight shipping"]
}
```

#### DELETE /api/cart

Clear cart.

**Query Parameters**:
- `user_id` (required): User ID

#### DELETE /api/cart/{product_id}

Remove item from cart.

**Query Parameters**:
- `user_id` (required): User ID

## MCP Server API

Base URL: `http://localhost:8001` (local) or `http://host-1:8001` (Instruqt)

### POST /mcp

Handle MCP JSON-RPC requests.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_trip_conditions_tool",
    "arguments": {
      "location": "Rockies",
      "dates": "January 15, 2024"
    }
  },
  "id": "request-123"
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "weather": "snowy",
    "min_temp_f": 15,
    "max_temp_f": 35,
    "road_alert": "traction_law_active",
    "recommendations": [...]
  },
  "id": "request-123"
}
```

### GET /health

Health check.

**Response**:
```json
{
  "status": "healthy"
}
```

## Available MCP Tools

### get_trip_conditions_tool

Get weather conditions for a location and date.

**Arguments**:
- `location` (string): Destination location
- `dates` (string): Date or date range

**Returns**: Weather conditions, temperature, road alerts, recommendations

### get_customer_profile_tool

Get customer profile from CRM.

**Arguments**:
- `user_id` (string): User identifier

**Returns**: Customer details, loyalty tier, purchase history, preferences


