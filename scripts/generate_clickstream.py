#!/usr/bin/env python3
"""
Generate realistic clickstream data with user personas and coherent session stories.
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from collections import defaultdict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

ES_URL = os.getenv("SNAPSHOT_ELASTICSEARCH_URL", os.getenv("ELASTICSEARCH_URL", "http://kubernetes-vm:30920"))
ES_APIKEY = os.getenv("SNAPSHOT_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))

if not ES_APIKEY:
    raise ValueError("SNAPSHOT_ELASTICSEARCH_APIKEY (or ELASTICSEARCH_APIKEY) environment variable is required")

es = Elasticsearch(
    [ES_URL],
    api_key=ES_APIKEY,
    request_timeout=60
)


# User Personas with realistic shopping stories
USER_PERSONAS = [
    {
        "id": "ultralight_backpacker_sarah",
        "name": "Sarah Martinez",
        "avatar_color": "from-teal-500 to-cyan-500",
        "story": "Planning a 3-week Pacific Crest Trail thru-hike",
        "sessions": [
            {
                "goal": "Research ultralight shelter options",
                "tags": ["ultralight", "expedition"],
                "categories": ["Tents", "Tarps"],
                "days_ago": 3,
                "time_of_day": "evening",
                "num_items": (8, 15),
                "add_to_cart_rate": 0.15,  # Research phase, low conversion
                "behavior": "compare_and_research"
            },
            {
                "goal": "Find lightweight sleep system",
                "tags": ["ultralight", "expedition"],
                "categories": ["Sleeping Bags", "Pads"],
                "days_ago": 2,
                "time_of_day": "morning",
                "num_items": (6, 12),
                "add_to_cart_rate": 0.25,  # More decisive
                "behavior": "decisive_buyer"
            },
            {
                "goal": "Browse backpacks and organization",
                "tags": ["ultralight", "expedition"],
                "categories": ["Backpacks"],
                "days_ago": 1,
                "time_of_day": "evening",
                "num_items": (10, 18),
                "add_to_cart_rate": 0.10,  # Window shopping
                "behavior": "window_shopping"
            }
        ]
    },
    {
        "id": "family_camper_mike",
        "name": "Mike Chen",
        "avatar_color": "from-amber-500 to-orange-500",
        "story": "Getting gear for weekend family camping trips",
        "sessions": [
            {
                "goal": "Find a spacious family tent",
                "tags": ["family", "comfort"],
                "categories": ["Tents"],
                "days_ago": 5,
                "time_of_day": "evening",
                "num_items": (5, 10),
                "add_to_cart_rate": 0.30,  # Needs it, more likely to buy
                "behavior": "careful_researcher"
            },
            {
                "goal": "Camp kitchen and cooking gear",
                "tags": ["family", "comfort"],
                "categories": ["Stoves", "Cookware"],
                "days_ago": 3,
                "time_of_day": "weekend",
                "num_items": (8, 14),
                "add_to_cart_rate": 0.35,  # Bulk buyer
                "behavior": "bulk_buyer"
            },
            {
                "goal": "Sleeping arrangements for family",
                "tags": ["family", "comfort"],
                "categories": ["Sleeping Bags", "Pads"],
                "days_ago": 1,
                "time_of_day": "evening",
                "num_items": (6, 11),
                "add_to_cart_rate": 0.20,
                "behavior": "careful_researcher"
            }
        ]
    },
    {
        "id": "winter_mountaineer_alex",
        "name": "Alex Thompson",
        "avatar_color": "from-blue-500 to-indigo-500",
        "story": "Preparing for winter alpine climbing season",
        "sessions": [
            {
                "goal": "Upgrade 4-season tent for alpine conditions",
                "tags": ["expedition", "4-season"],
                "categories": ["Tents"],
                "days_ago": 7,
                "time_of_day": "evening",
                "num_items": (4, 8),
                "add_to_cart_rate": 0.40,  # Expert buyer, knows what they want
                "behavior": "expert_buyer"
            },
            {
                "goal": "Cold weather sleep system",
                "tags": ["expedition", "4-season"],
                "categories": ["Sleeping Bags", "Pads"],
                "days_ago": 5,
                "time_of_day": "evening",
                "num_items": (5, 9),
                "add_to_cart_rate": 0.35,
                "behavior": "expert_buyer"
            },
            {
                "goal": "Technical climbing gear",
                "tags": ["expedition", "professional"],
                "categories": ["Backpacks", "Accessories"],
                "days_ago": 2,
                "time_of_day": "morning",
                "num_items": (6, 12),
                "add_to_cart_rate": 0.25,
                "behavior": "expert_buyer"
            }
        ]
    },
    {
        "id": "weekend_hiker_emma",
        "name": "Emma Wilson",
        "avatar_color": "from-green-500 to-emerald-500",
        "story": "New to hiking, building out day hike essentials",
        "sessions": [
            {
                "goal": "Day hiking essentials research",
                "tags": ["beginner", "comfort"],
                "categories": ["Backpacks", "Hydration"],
                "days_ago": 4,
                "time_of_day": "afternoon",
                "num_items": (12, 20),  # Lots of browsing, uncertain
                "add_to_cart_rate": 0.05,  # Very low, just learning
                "behavior": "confused_browser"
            },
            {
                "goal": "Revisit favorites from previous session",
                "tags": ["beginner", "comfort"],
                "categories": ["Backpacks", "Water Filters"],
                "days_ago": 1,
                "time_of_day": "evening",
                "num_items": (3, 6),  # Narrowed down
                "add_to_cart_rate": 0.30,  # More confident now
                "behavior": "return_visitor"
            }
        ]
    },
    {
        "id": "car_camper_david",
        "name": "David Park",
        "avatar_color": "from-purple-500 to-pink-500",
        "story": "Car camping enthusiast, prioritizes comfort and luxury",
        "sessions": [
            {
                "goal": "Luxury camping gear upgrade",
                "tags": ["comfort", "premium"],
                "categories": ["Tents", "Sleeping Bags"],
                "days_ago": 6,
                "time_of_day": "weekend",
                "num_items": (5, 9),
                "add_to_cart_rate": 0.45,  # Premium buyer, high conversion
                "behavior": "premium_buyer"
            },
            {
                "goal": "Comfort accessories and amenities",
                "tags": ["comfort", "premium"],
                "categories": ["Accessories", "Cookware"],
                "days_ago": 3,
                "time_of_day": "evening",
                "num_items": (7, 13),
                "add_to_cart_rate": 0.30,
                "behavior": "premium_buyer"
            }
        ]
    },
    {
        "id": "user_new",
        "name": "Guest User",
        "avatar_color": "from-gray-500 to-slate-500",
        "story": "First-time visitor, browsing casually",
        "sessions": []
    },
    {
        "id": "user_member",
        "name": "Alex Hiker",
        "avatar_color": "from-emerald-500 to-teal-500",
        "story": "Experienced hiker with ultralight preferences",
        "sessions": [
            {
                "goal": "Ultralight gear browsing",
                "tags": ["ultralight", "expedition"],
                "categories": ["Backpacks", "Tents"],
                "days_ago": 2,
                "time_of_day": "evening",
                "num_items": (10, 16),
                "add_to_cart_rate": 0.20,
                "behavior": "experienced_buyer"
            }
        ]
    },
    {
        "id": "user_business",
        "name": "Casey Campground",
        "avatar_color": "from-orange-500 to-red-500",
        "story": "Campground owner purchasing bulk equipment",
        "sessions": [
            {
                "goal": "Bulk tent purchases for campground",
                "tags": ["family", "budget"],
                "categories": ["Tents"],
                "days_ago": 4,
                "time_of_day": "morning",
                "num_items": (8, 14),
                "add_to_cart_rate": 0.50,  # Business buyer, high conversion
                "behavior": "bulk_buyer"
            },
            {
                "goal": "Campground amenities and supplies",
                "tags": ["family", "budget"],
                "categories": ["Cookware", "Accessories"],
                "days_ago": 1,
                "time_of_day": "morning",
                "num_items": (6, 11),
                "add_to_cart_rate": 0.40,
                "behavior": "bulk_buyer"
            }
        ]
    }
]


def get_all_products(es: Elasticsearch) -> list:
    """Get all products with full details."""
    response = es.search(
        index="product-catalog",
        query={"match_all": {}},
        size=1000,
        _source=["id", "tags", "category", "subcategory", "title"]
    )
    return [
        {
            "id": hit["_source"]["id"],
            "tags": hit["_source"].get("tags", []),
            "category": hit["_source"].get("category", ""),
            "subcategory": hit["_source"].get("subcategory", ""),
            "title": hit["_source"].get("title", "")
        }
        for hit in response["hits"]["hits"]
    ]


def filter_products_by_tags(products: list, tags: list) -> list:
    """Filter products that match any of the given tags."""
    if not tags:
        return products
    return [
        p for p in products
        if any(tag in p["tags"] for tag in tags)
    ]


def filter_products_by_category(products: list, categories: list) -> list:
    """Filter products by category keywords."""
    if not categories:
        return products
    matching = []
    for p in products:
        cat_lower = p["category"].lower()
        subcat_lower = p["subcategory"].lower()
        title_lower = p["title"].lower()
        for cat in categories:
            if (cat.lower() in cat_lower or 
                cat.lower() in subcat_lower or 
                cat.lower() in title_lower):
                matching.append(p)
                break
    return matching if matching else products


def generate_session_events(
    products: list,
    session_config: dict,
    user_id: str,
    base_time: datetime
) -> list:
    """Generate a coherent shopping session."""
    events = []
    session_id = str(uuid.uuid4())
    
    # Filter products for this session
    session_products = filter_products_by_tags(products, session_config["tags"])
    session_products = filter_products_by_category(session_products, session_config["categories"])
    
    # If no matches, fall back to tag-based filtering only
    if not session_products:
        session_products = filter_products_by_tags(products, session_config["tags"])
    
    # If still no matches, use all products (shouldn't happen but safety)
    if not session_products:
        session_products = products
    
    # Determine session start time
    days_ago = session_config["days_ago"]
    time_of_day = session_config["time_of_day"]
    
    if time_of_day == "morning":
        hour = random.randint(8, 11)
    elif time_of_day == "afternoon":
        hour = random.randint(12, 17)
    elif time_of_day == "evening":
        hour = random.randint(18, 22)
    elif time_of_day == "weekend":
        hour = random.randint(10, 16)
    else:
        hour = random.randint(9, 21)
    
    session_start = base_time - timedelta(days=days_ago)
    session_start = session_start.replace(hour=hour, minute=random.randint(0, 59))
    
    # Generate events for this session
    num_items = random.randint(*session_config["num_items"])
    
    # Sample products for this session (with some repetition for comparison shopping)
    session_product_pool = random.choices(session_products, k=min(num_items * 2, len(session_products)))
    session_product_pool = session_product_pool[:num_items]
    
    for i, product in enumerate(session_product_pool):
        # View event
        view_time = session_start + timedelta(minutes=i * random.randint(1, 4))
        events.append({
            "@timestamp": view_time.isoformat(),
            "user_id": user_id,
            "action": "view_item",
            "product_id": product["id"],
            "meta_tags": product["tags"],
            "session_id": session_id
        })
        
        # Maybe add to cart (based on behavior)
        if random.random() < session_config["add_to_cart_rate"]:
            cart_time = view_time + timedelta(minutes=random.randint(1, 3))
            events.append({
                "@timestamp": cart_time.isoformat(),
                "user_id": user_id,
                "action": "add_to_cart",
                "product_id": product["id"],
                "meta_tags": product["tags"],
                "session_id": session_id
            })
    
    return events


def generate_user_clickstream(persona: dict, products: list, base_time: datetime) -> list:
    """Generate all clickstream events for a user persona."""
    user_id = persona["id"]
    all_events = []
    
    # Generate events for each session
    for session_config in persona.get("sessions", []):
        session_events = generate_session_events(products, session_config, user_id, base_time)
        all_events.extend(session_events)
    
    return all_events


def seed_clickstream():
    """Generate and seed clickstream data for all user personas."""
    print("Generating realistic clickstream data...")
    
    # Get all products first
    products = get_all_products(es)
    if not products:
        print("Error: No products found. Please seed products first.")
        return
    
    print(f"Found {len(products)} products")
    
    # Base time is now
    base_time = datetime.now()
    
    all_events = []
    
    # Generate events for each persona
    for persona in USER_PERSONAS:
        print(f"\nGenerating events for {persona['name']} ({persona['id']})...")
        user_events = generate_user_clickstream(persona, products, base_time)
        print(f"  Generated {len(user_events)} events across {len(persona.get('sessions', []))} sessions")
        all_events.extend(user_events)
    
    # Bulk index events
    def doc_generator():
        for event in all_events:
            yield {
                "_index": "user-clickstream",
                "_source": event
            }
    
    print(f"\nIndexing {len(all_events)} total clickstream events...")
    success, failed = bulk(es, doc_generator(), raise_on_error=False)
    
    if failed:
        print(f"Warning: {len(failed)} events failed to index")
        if len(failed) <= 10:
            for item in failed:
                print(f"  Failed: {item}")
    else:
        print(f"Successfully indexed {success} events")
    
    # Refresh index
    es.indices.refresh(index="user-clickstream")
    print("Index refreshed")
    
    # Save personas metadata to JSON for frontend
    personas_output = []
    for persona in USER_PERSONAS:
        # Calculate stats from generated events
        user_events = [e for e in all_events if e["user_id"] == persona["id"]]
        view_events = [e for e in user_events if e["action"] == "view_item"]
        cart_events = [e for e in user_events if e["action"] == "add_to_cart"]
        
        # Group by session
        sessions_by_id = defaultdict(list)
        for event in user_events:
            session_id = event.get("session_id", "unknown")
            sessions_by_id[session_id].append(event)
        
        # Build session summaries
        session_summaries = []
        for session_id, session_events in sessions_by_id.items():
            if not session_events:
                continue
            
            # Find matching session config
            session_config = None
            for sc in persona.get("sessions", []):
                # Match by approximate time
                event_time = datetime.fromisoformat(session_events[0]["@timestamp"])
                days_ago = (base_time - event_time).days
                if abs(days_ago - sc["days_ago"]) <= 1:
                    session_config = sc
                    break
            
            if session_config:
                view_count = len([e for e in session_events if e["action"] == "view_item"])
                session_summaries.append({
                    "goal": session_config["goal"],
                    "timeframe": f"{session_config['days_ago']} days ago",
                    "item_count": view_count,
                    "categories": session_config["categories"]
                })
        
        personas_output.append({
            "id": persona["id"],
            "name": persona["name"],
            "avatar_color": persona["avatar_color"],
            "story": persona["story"],
            "sessions": session_summaries,
            "total_views": len(view_events),
            "total_cart_adds": len(cart_events)
        })
    
    # Save to file
    output_path = Path("generated_products/user_personas.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(personas_output, f, indent=2)
    
    print(f"\nSaved user personas metadata to {output_path}")


def main():
    seed_clickstream()


if __name__ == "__main__":
    main()

