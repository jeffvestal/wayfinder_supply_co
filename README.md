# Wayfinder Supply Co. Workshop

A hands-on workshop demonstrating **Elastic Agentic Search** capabilities through "Wayfinder Supply Co." — a fictional outdoor retailer with an AI-powered trip planning assistant.

## Overview

This workshop showcases how to build an intelligent, conversational shopping experience that goes beyond keyword matching:

- **Federated Data**: Combines Elasticsearch product catalog with simulated CRM (Salesforce) and Weather APIs
- **Personalized Recommendations**: Uses clickstream data to understand user preferences (ultralight, budget, expedition, etc.)
- **AI Trip Planning**: Agent Builder orchestrates multi-step trip planning with gear recommendations
- **Location Intelligence**: Covers 30 global adventure destinations with seasonal activity and weather data
- **Real-time Synthesis**: Creates personalized itineraries with gear checklists based on conditions

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      Frontend (React)                         │
│                  Modern UI with Trip Planner                  │
└──────────────────────────────┬────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────┐
│                   Backend Proxy (FastAPI)                     │
│             Handles auth, streaming, user context             │
└──────────────────────────────┬────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────┐
│                        Elastic Stack                          │
│                                                               │
│  ┌─────────────────┐ ┌───────────────┐ ┌───────────────────┐  │
│  │  Elasticsearch  │ │ Agent Builder │ │     Workflows     │  │
│  │  - Products     │ │ Trip Planner  │ │ check_trip_safety │  │
│  │  - Clickstream  │ │               │ │ get_customer_prof │  │
│  └─────────────────┘ └───────────────┘ └─────────┬─────────┘  │
│                                                  │            │
└──────────────────────────────────────────────────┼────────────┘
                                                   │
┌──────────────────────────────────────────────────▼────────────┐
│                     MCP Server (FastMCP)                      │
│            Simulates external APIs (Weather, CRM)             │
│          30 locations with seasonal weather patterns          │
└───────────────────────────────────────────────────────────────┘
```

## Covered Adventure Destinations (30 locations)

| Region | Locations |
|--------|-----------|
| **North America** | Yosemite, Rocky Mountain NP, Yellowstone, Boundary Waters, Moab, PCT, Banff, Whistler, Algonquin |
| **South/Central America** | Patagonia, Costa Rica, Chapada Diamantina (Brazil) |
| **Europe** | Swiss Alps, Scottish Highlands, Norwegian Fjords, Iceland |
| **Africa** | Mount Kilimanjaro, Kruger NP, Atlas Mountains |
| **Asia** | Nepal Himalayas, Japanese Alps, Bali, MacRitchie (Singapore) |
| **Oceania** | NZ South Island, Australian Outback, Great Barrier Reef |
| **Middle East** | Wadi Rum (Jordan), Hatta (Dubai/UAE) |

## Product Catalog

Full catalog covers 10 categories with ~150 products:

- **Camping**: Tents, sleeping bags, pads, kitchen, furniture, lighting
- **Hiking**: Packs, boots, trail runners, poles, hydration, navigation
- **Climbing**: Harnesses, ropes, protection, shoes, helmets, ice gear
- **Winter Sports**: Skis, snowboards, snowshoes, avalanche safety
- **Water Sports**: Kayaks, canoes, paddleboards, wetsuits, snorkel/dive
- **Cycling**: Mountain bikes, helmets, apparel, accessories
- **Fishing**: Rods, tackle, waders, ice fishing gear
- **Apparel**: Base/mid/outer layers, rain gear, sun protection
- **Tropical & Safari**: Insect protection, cooling gear, safari essentials
- **Accessories**: First aid, tools, gloves, gaiters, bags

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for local dev)
- Google Cloud account (for product image generation)

### Local Development

1. **Clone and setup environment**:
   ```bash
   git clone https://github.com/jeffvestal/wayfinder_supply_co.git
   cd wayfinder_supply_co
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Generate product data** (requires Google Cloud credentials):
   ```bash
   pip install -r requirements.txt
   python scripts/generate_products.py --mode full
   ```

3. **Start all services**:
   ```bash
   docker-compose up --build
   ```

4. **Access the app**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MCP Server: http://localhost:8001

### Instruqt Environment

The workshop runs on Instruqt with two VMs:

| VM | Services | Purpose |
|----|----------|---------|
| `kubernetes-vm` | Elasticsearch, Kibana, Agent Builder | Elastic Stack |
| `host-1` | Frontend, Backend, MCP Server | Application layer |

Setup scripts in `instruqt/track_scripts/` handle all configuration.

## Project Structure

```
wayfinder_supply_co/
├── frontend/                 # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   ├── Storefront.tsx
│   │   │   ├── TripPlanner.tsx
│   │   │   ├── ChatModal.tsx
│   │   │   ├── ThoughtTrace.tsx
│   │   │   └── ...
│   │   ├── lib/              # API client
│   │   └── types/            # TypeScript types
│   └── public/               # Static assets
│
├── backend/                  # FastAPI proxy server
│   ├── main.py               # Entry point
│   ├── routers/              # API routes
│   │   ├── chat.py           # Agent streaming
│   │   ├── products.py       # Product search
│   │   └── cart.py           # Cart management
│   └── services/             # Elasticsearch client
│
├── mcp_server/               # FastMCP external API simulation
│   ├── main.py               # Entry point
│   ├── tools/
│   │   ├── weather_service.py  # Location coverage + conditions
│   │   └── crm_service.py      # Customer profiles
│   └── data/
│       ├── locations.json    # 30 adventure destinations
│       └── crm_mock.json     # Sample customer data
│
├── scripts/                  # Setup and generation scripts
│   ├── generate_products.py  # AI product generation (Gemini + Imagen)
│   ├── setup_elastic.py      # Index creation
│   ├── seed_products.py      # Data indexing
│   ├── seed_clickstream.py   # Clickstream generation
│   ├── create_agents.py      # Agent Builder setup
│   └── validate_setup.py     # Health checks
│
├── config/                   # Configuration
│   ├── product_generation.yaml  # Full product catalog config
│   └── workflows/            # Elastic Workflow definitions
│
├── instruqt/                 # Instruqt track configuration
│   ├── track.yml             # Track metadata
│   ├── config.yml            # VM configuration
│   └── track_scripts/        # Setup scripts
│
└── docs/                     # Additional documentation
    └── IMAGE_GENERATION_SETUP.md
```

## User Personas

The demo includes three user personas to showcase personalization:

| Persona | Name | Loyalty Tier | Behavior |
|---------|------|--------------|----------|
| **New User** | Jordan Explorer | None | First-time visitor, no history |
| **Member** | Alex Hiker | Platinum | Ultralight preference, free shipping |
| **Business** | Casey Campground | Business | Bulk buyer, campground owner |

## Workshop Flow

1. **Explore the Store** — Browse products, see semantic search in action
2. **Plan a Trip** — Use the AI Trip Planner to get personalized recommendations
3. **Watch the Agent Think** — See the Thought Trace panel show tool calls
4. **Test Personalization** — Switch users to see different recommendations
5. **Try Different Locations** — Test covered vs. uncovered destinations

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ELASTICSEARCH_URL` | Elasticsearch endpoint | Yes |
| `ELASTICSEARCH_APIKEY` | API key for auth | Yes |
| `KIBANA_URL` | Kibana endpoint | Yes |
| `GOOGLE_API_KEY` | Gemini API key (for product generation) | For generation |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | For generation |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | For generation |

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Framer Motion, Lucide Icons
- **Backend**: Python 3.11+, FastAPI, httpx, SSE
- **MCP Server**: FastMCP, Pydantic
- **Search**: Elasticsearch 9.x, ELSER (semantic), Agent Builder
- **AI Generation**: Google Gemini 2.5 Flash (text), Vertex AI Imagen 3 (images)

## License

See [LICENSE](LICENSE) file.
