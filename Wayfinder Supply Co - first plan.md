# Product Requirement Document: "Wayfinder Supply Co." Workshop

**Version:** 1.5
**Status:** Final
**Target Audience:** Workshop Attendees (DevOps, SRE, Search Engineers)
**Tech Stack:** Elastic Search (Workflows, Agent Builder), Python (FastAPI/MCP), React (Vite + Tailwind)

## 1. Executive Summary

This workshop demonstrates the power of **Agentic Search** by moving beyond simple keyword matching. Participants will build the intelligent backend for **"Wayfinder Supply Co.,"** a fictional high-tech outdoor retailer. The goal is to build an "Adventure Logistics Agent" that doesn't just find products—it validates whether those products are safe and appropriate for the user's specific upcoming trip.

**The "Impossible" Use Case:**
A standard search engine cannot answer: *"I'm going camping in the Rockies this weekend."* because the answer depends on:

1. **Live External Conditions:** Weather and Road Regulations (Dynamic).

2. **Federated Enterprise Data:** Customer purchase history and loyalty status living in **Salesforce CRM**.

3. **Inferred Context:** The user's implied preference for "Ultralight" gear (Clickstream logs).

4. **Synthesis:** The need to combine all this into a coherent itinerary with a "one-click" purchase path.

### 1.1 Proposed Project Structure
To ensure consistency, the project should follow this structure:
```text
wayfinder-workshop/
├── docker-compose.yml          # ES, Kibana, App containers
├── README.md                   # Lab Guide
├── backend/                    # Python MCP Server
│   ├── main.py                 # FastAPI/MCP entry point
│   ├── requirements.txt
│   ├── data/                   # Mock Data files
│   │   └── crm_mock.json       # Simulating Salesforce response
│   └── tools/                  # Tool logic
│       ├── weather_service.py
│       └── salesforce_client.py # Renamed from inventory.py
├── frontend/                   # React + Vite App
│   ├── src/
│   │   ├── components/         # ChatInterface.tsx, ProductGrid.tsx
│   │   └── lib/                # API clients
│   └── package.json
└── scripts/                    # Data Generation
    ├── generate_catalog.py     # Vertex AI generation
    ├── seed_products.py        # Elastic indexer
    └── seed_logs.py            # Clickstream generator
```

## 2. System Architecture

The system consists of a "Dumb" Frontend and a "Smart" Backend Agent.

**Architecture Note:** This workshop explicitly demonstrates the three types of tools available in Elastic Agent Builder:

1. **Built-in Tools:** Standard semantic search.

2. **ES|QL Tools:** Custom internal queries for personalization (Clickstream).

3. **Workflow Tools:** The bridge to external systems (CRM & Weather).

```mermaid
graph TD
    User[User] -->|Chat Message| UI[Wayfinder Store UI]
    UI -->|API Call| Agent[Elastic Agent]
    
    subgraph "Elastic Agent Builder"
        Agent -->|Tool: Search| Search_Tool[Built-in Search]
        Agent -->|Tool: Affinity| ESQL_Tool[Custom ES|QL Tool]
        Agent -->|Tool: Logistics| WF_Logistics[Workflow: Check Conditions]
        Agent -->|Tool: CRM| WF_CRM[Workflow: Customer Profile]
        Agent -->|Tool: Planner| WF_Planner[Workflow: Build Itinerary]
    end

    subgraph "Elastic Workflow Engine"
        WF_Logistics -->|Call MCP| MCP_Client_1[MCP Connector]
        WF_CRM -->|Call MCP| MCP_Client_2[MCP Connector]
        WF_Planner -->|Call MCP| MCP_Client_3[MCP Connector]
    end

    subgraph "External MCP Server"
        MCP_Client_1 -->|API| Tool_Weather[Weather/Roads]
        MCP_Client_2 -->|API| Tool_SFDC[Salesforce Service]
        MCP_Client_3 -->|Data| Tool_Trails[Trail Recommendations]
    end

    subgraph "Elastic Data"
        Search_Tool --> Index_Products[(Product Index)]
        ESQL_Tool --> Index_Logs[(Clickstream Index)]
    end
```

## 3. Data Layer Specifications

We need three distinct data sources to force the Agent to "federate" information.

### A. Elastic Index: `product-catalog`

* **Purpose:** The main inventory.

* **Search Method:** Hybrid (Text + Vector).

* **Schema:**

  ```json
  {
    "id": "keyword",
    "title": "text", // e.g., "Wayfinder Inferno 0° Bag"
    "brand": "keyword", // e.g., "Wayfinder Labs", "North Face"
    "description": "text", // Semantic text enabled
    "image_url": "keyword", // Local path: /images/products/p_123.jpg
    "category": "keyword", // [Tent, Sleeping Bag, Accessories]
    "attributes": {
      "temp_rating_f": "integer", // e.g., 15
      "weight_lb": "float",       // e.g., 2.5
      "season": "keyword"         // [3-season, 4-season]
    },
    "price": "float",
    "tags": "keyword", // [ultralight, budget, expedition]
    "vector_embedding": "dense_vector" // For semantic matching
  }
  ```

### B. Elastic Index: `user-clickstream`

* **Purpose:** Raw logs used to infer user "affinity" (Personalization).

* **Schema:**

  ```json
  {
    "@timestamp": "date",
    "user_id": "keyword",
    "action": "keyword", // [view_item, add_to_cart]
    "product_id": "keyword",
    "meta_tags": "keyword" // Snapshot of tags, e.g., [ultralight, expensive]
  }
  ```

### C. Salesforce CRM (Simulated via JSON)

* **Purpose:** Represents the Enterprise "System of Record" containing purchase history and loyalty status.
* **Format:** `crm_mock.json` (Loaded by Python MCP).
* **Schema (Mock Response):**
  ```json
  {
    "user_id": "101",
    "name": "Alex Hiker",
    "loyalty_tier": "Platinum", // Used for logic branching
    "lifetime_value": 4500.00,
    "purchase_history": [
      { "sku": "WF-TIRE-CHAIN-01", "name": "Thule 16mm Chains", "date": "2023-11-15" },
      { "sku": "WF-STOVE-MSR", "name": "PocketRocket Stove", "date": "2022-06-01" }
    ]
  }
  ```

### 3.1. Data Generation Strategy (The "Synthetic Pipeline")

To ensure high quality and visual consistency, the product catalog will be **AI-Generated** prior to the workshop using **Google Vertex AI**.

1. **Metadata Generation (Gemini 1.5 Pro):** Generate ~100 diverse JSON product records.
   * *Prompt:* "Generate a list of high-end outdoor gear items. Use brand 'Wayfinder Supply'. Include realistic attributes for temperature and weight."

2. **Image Generation (Vertex AI - Imagen 3):** Generate 1 image per product ID.
   * *Prompt Template:* "Studio photography of a {Product_Title}, {Product_Description}, white background, soft lighting, 4k, product shot, no text."
   * *Tooling:* `generate_catalog.py` will loop through the JSON and call the Vertex AI API.

3. **Output:** A folder `/public/images/products/` containing the assets, and a `products.json` file for seeding.

## 4. Tool & Workflow Definitions

The engineering team must implement these tools to be registered in Agent Builder.

### A. Custom ES|QL Tool: `get_user_affinity`

* **Type:** `ES|QL` (Internal)
* **Purpose:** Analyzes clickstream data to find the user's preferred gear style.
* **Query Logic:**
  ```sql
  FROM user-clickstream
  | WHERE user_id == ?
  | STATS count = COUNT(*) BY meta_tags
  | SORT count DESC
  | LIMIT 1
  ```

### B. Workflow Tool: `check_trip_safety`

* **Type:** `Workflow` (External via MCP)
* **Flow:** Agent -> Workflow -> MCP Server (`get_trip_conditions`)
* **Description:** Simulates a live call to checking weather and road laws.
* **Arguments:** `location` (string), `dates` (string)
* **Hardcoded Logic (in MCP):**
  * If `location` contains "Denver" or "Rockies": Return `{ "weather": "snowy", "min_temp_f": 15, "road_alert": "traction_law_active" }`
  * Else: Return `{ "weather": "sunny", "min_temp_f": 60, "road_alert": "none" }`

### C. Workflow Tool: `get_customer_profile` (Replaces SQL Lookup)

* **Type:** `Workflow` (External via MCP)
* **Flow:** Agent -> Workflow -> MCP Server (`salesforce_client.get_profile`)
* **Description:** Retrieves the Customer 360 profile from Salesforce, including past orders and loyalty tier.
* **Arguments:** `user_id` (int)
* **Logic (in MCP):**
  * Simulates a REST API call to Salesforce.
  * Reads from `crm_mock.json`.
  * Returns the full JSON object (History + Tier).

### D. Workflow Tool: `build_trip_plan`

* **Type:** `Workflow` (External via MCP)
* **Flow:** Agent -> Workflow -> MCP Server (`get_trail_recommendations`)
* **Description:** Generates the final itinerary and splits the gear list into "Owned" and "To Buy".
* **Arguments:** `location` (string), `owned_items` (list[str]), `needed_items` (list[str]), `loyalty_tier` (string)
* **Logic (in MCP):**
  * Calls `get_trail_data(location)` (Simulated).
  * Returns a structured Markdown response:
    * **Day 1:** Arrive at {Location}.
    * **Gear Checklist:** ...
    * **Shipping:** *Conditional Logic:* If `loyalty_tier` == "Platinum", add "✨ Free Overnight Shipping Applied".
  * *Metadata Return:* Returns a generated "Cart Link" (e.g., `/cart?add=item1,item2`).

## 5. Agent Workflow Logic

The Agent must be configured with this "System Prompt" / Logic Flow:

**Trigger:** User asks about a trip (e.g., "Camping in Rockies").

1. **Safety Check:** Call `check_trip_safety`.
   * *If `min_temp_f` < 30:* Add "0-degree Sleeping Bag" to requirements.
   * *If `road_alert` == "traction_law_active":* Add "Tire Chains" to requirements.

2. **CRM Federation:** Call `get_customer_profile`.
   * Extract `purchase_history` list.
   * Extract `loyalty_tier`.
   * *Logic:* Check `purchase_history` against requirements. If user owns "Tire Chains", move to "Owned List".

3. **Personalization:** Call `get_user_affinity`.
   * *Result:* "Ultralight".

4. **Execution (Search):** Call Built-in Search Tool for items in the "Buy List".
   * *Filter:* `temp_rating_f` <= 20
   * *Boost:* `tags` == "Ultralight"
   * *Action:* Store the specific Product IDs found.

5. **Final Synthesis:** Call `build_trip_plan`.
   * *Inputs:* Location, Owned List, Buy List, Loyalty Tier.
   * *Output:* Display the final Itinerary + Cart Link + Shipping Perks.

## 6. Frontend Requirements ("The Wayfinder Store")

A simple React/Vue web application (recommend Vite + Tailwind).

### View 1: The Storefront

* A grid of ~6 dummy products.
* **User Switcher:** A dropdown in the nav bar to toggle between:
  * `User A` (Platinum Member, owns chains).
  * `User B` (New Customer, owns nothing).
  * *Note:* Switching users must update the `user_id` sent to the Agent.

### View 2: The Agent Chat Interface

* Standard chat bubble UI.
* **CRITICAL FEATURE: The "Thought Trace" Panel**
  * A side panel that visualizes the Agent's steps.
  * **Expected Log JSON Structure (for display):**
    ```json
    {
      "step": "CRM Lookup",
      "tool": "get_customer_profile",
      "status": "complete",
      "data": { "tier": "Platinum", "found_items": ["Thule Chains"] }
    }
    ```

## 7. Deliverables Checklist for Engineering

* [ ] **Infrastructure:** `docker-compose.yml` (ES 8.16+, Kibana, App Container).
* [ ] **MCP Server:** Python script using the Elastic MCP SDK.
* [ ] **Data Mocks:** `crm_mock.json` containing profiles for User A and User B.
* [ ] **Asset Generation (Pre-Workshop):**
  * `generate_catalog.py`: Python script using **Vertex AI (Imagen 3)** to create 100 items + images.
  * **Output:** `/public/images/products/*` folder committed to the repo.
* [ ] **Seeding Scripts:**
  * `seed_products.py`: Indexes the generated catalog into Elastic.
  * `seed_logs.py`: Generates fake click traffic for User A (Ultralight items) and User B (Budget items).
* [ ] **Frontend Code:** React (Vite) app connecting to the Agent endpoint.
* [ ] **Lab Guide:** A markdown tutorial explaining how to configure the Agent in Kibana.