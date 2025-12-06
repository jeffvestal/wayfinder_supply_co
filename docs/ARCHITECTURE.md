# Architecture Documentation

## System Overview

Wayfinder Supply Co. is a demonstration of Elastic Agentic Search capabilities, showcasing how to build an intelligent search experience that goes beyond keyword matching.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  React Frontend (Vite + TypeScript + Tailwind)           │  │
│  │  - Storefront View                                        │  │
│  │  - Chat Interface (SSE streaming)                         │  │
│  │  - Thought Trace Panel                                    │  │
│  │  - Cart View                                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/SSE
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND PROXY (FastAPI)                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  - Chat Endpoint (SSE proxy to Agent Builder)             │  │
│  │  - Product API (Elasticsearch queries)                    │  │
│  │  - Cart Management                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────────┬─────────────────────┘
             │                              │
             │ SSE                          │ HTTP
             ▼                              ▼
┌──────────────────────────┐  ┌──────────────────────────────┐
│   ELASTIC STACK           │  │   MCP SERVER (FastAPI)        │
│  ┌──────────────────────┐ │  │  ┌────────────────────────┐  │
│  │  Agent Builder       │ │  │  │  Weather Service       │  │
│  │  - Trip Planner      │ │  │  │  CRM Service           │  │
│  │  - Itinerary Agent   │ │  │  └────────────────────────┘  │
│  └──────────┬───────────┘ │  └──────────────────────────────┘
│             │             │
│  ┌──────────▼───────────┐  │
│  │  Workflows          │  │
│  │  - check_trip_safety │  │
│  │  - get_customer_     │  │
│  │    profile          │  │
│  │  - get_user_affinity│  │
│  └──────────┬──────────┘  │
│             │             │
│  ┌──────────▼───────────┐  │
│  │  Elasticsearch       │  │
│  │  - product-catalog   │  │
│  │  - user-clickstream  │  │
│  └─────────────────────┘  │
└────────────────────────────┘
```

## Component Details

### Frontend (React + Vite)

**Technology Stack**:
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Radix UI for accessible components
- React Markdown for message rendering

**Key Features**:
- Server-Sent Events (SSE) for real-time agent responses
- Thought trace visualization
- User persona switching
- Responsive design

### Backend Proxy (FastAPI)

**Responsibilities**:
- Proxy SSE streams from Agent Builder
- Product catalog queries
- Cart management
- Health checks

**Endpoints**:
- `POST /api/chat` - Chat streaming proxy
- `GET /api/products` - List products
- `GET /api/products/{id}` - Get product
- `GET /api/products/search` - Semantic search
- `POST /api/cart` - Add to cart
- `GET /api/cart` - Get cart

### MCP Server (FastAPI)

**Purpose**: Simulate external enterprise systems (CRM, Weather API)

**Tools**:
- `get_trip_conditions_tool` - Dynamic weather based on location and season
- `get_customer_profile_tool` - CRM data lookup

**Protocol**: JSON-RPC over HTTP

### Elastic Stack

#### Agent Builder

**Agents**:
1. **Trip Planner Agent** - Main orchestrator
   - Uses multiple tools (search, workflows, ES|QL)
   - Makes intelligent decisions
   - Calls Itinerary Agent for synthesis

2. **Trip Itinerary Agent** - Content generation
   - Synthesizes trip plans
   - Formats markdown output
   - Applies loyalty perks

#### Workflows

**check_trip_safety**:
- Calls MCP server for weather
- Returns conditions and recommendations

**get_customer_profile**:
- Calls MCP server for CRM data
- Returns purchase history and loyalty tier

**get_user_affinity**:
- ES|QL query on clickstream
- Analyzes user preferences

#### Elasticsearch Indices

**product-catalog**:
- Products with semantic_text field (ELSER)
- Hybrid search (keyword + semantic)
- Rich metadata (tags, attributes, pricing)

**user-clickstream**:
- User browsing behavior
- Tag preferences
- Used for personalization

## Data Flow

### Chat Request Flow

1. User sends message via frontend
2. Frontend streams to backend `/api/chat`
3. Backend proxies to Agent Builder `/api/agent_builder/converse/async`
4. Agent Builder processes:
   - Calls workflow tools (weather, CRM)
   - Executes ES|QL queries (affinity)
   - Searches product catalog
   - Calls Itinerary Agent
5. Responses stream back via SSE
6. Frontend displays in chat + thought trace

### Product Search Flow

1. User searches products
2. Frontend calls `/api/products/search`
3. Backend queries Elasticsearch with semantic search
4. Results ranked by relevance
5. Frontend displays product grid

## Security Considerations

- API keys stored as environment variables
- CORS configured for specific origins
- Input validation on all endpoints
- Error messages don't expose internals
- Rate limiting recommended for production

## Scalability

- Stateless backend services
- Elasticsearch cluster for high availability
- Horizontal scaling of MCP server
- CDN for frontend assets
- Load balancer for API endpoints

## Monitoring

- Structured logging in all services
- Health check endpoints
- Request timing headers
- Error tracking
- Agent execution metrics

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.


