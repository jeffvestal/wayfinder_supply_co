#!/usr/bin/env python3
"""
Generate and seed clickstream data for user behavior analysis.
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://kubernetes-vm:30920")
ES_APIKEY = os.getenv("ELASTICSEARCH_APIKEY", "")

if not ES_APIKEY:
    raise ValueError("ELASTICSEARCH_APIKEY environment variable is required")

es = Elasticsearch(
    [ES_URL],
    api_key=ES_APIKEY,
    request_timeout=60
)


def get_product_tags(es: Elasticsearch, product_id: str) -> list:
    """Get tags for a product."""
    try:
        doc = es.get(index="product-catalog", id=product_id)
        return doc["_source"].get("tags", [])
    except:
        return []


def get_all_products(es: Elasticsearch) -> list:
    """Get all product IDs from index."""
    response = es.search(
        index="product-catalog",
        query={"match_all": {}},
        size=1000,
        _source=["id", "tags"]
    )
    return [
        {
            "id": hit["_source"]["id"],
            "tags": hit["_source"].get("tags", [])
        }
        for hit in response["hits"]["hits"]
    ]


def generate_clickstream_data(
    es: Elasticsearch,
    user_id: str,
    num_events: int,
    tag_preferences: list = None
):
    """Generate clickstream events for a user."""
    products = get_all_products(es)
    
    if not products:
        print("Warning: No products found in index")
        return []
    
    events = []
    base_time = datetime.now() - timedelta(days=30)
    
    # Filter products by tag preferences if provided
    if tag_preferences:
        preferred_products = [
            p for p in products
            if any(tag in p["tags"] for tag in tag_preferences)
        ]
        if preferred_products:
            products = preferred_products + random.sample(
                [p for p in products if p not in preferred_products],
                min(10, len(products) - len(preferred_products))
            )
    
    for i in range(num_events):
        product = random.choice(products)
        timestamp = base_time + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        action = random.choices(
            ["view_item", "add_to_cart"],
            weights=[0.8, 0.2]
        )[0]
        
        events.append({
            "@timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "action": action,
            "product_id": product["id"],
            "meta_tags": product["tags"]
        })
    
    return events


def seed_clickstream():
    """Generate and seed clickstream data for all user personas."""
    print("Generating clickstream data...")
    
    # Get all products first
    products = get_all_products(es)
    if not products:
        print("Error: No products found. Please seed products first.")
        return
    
    all_events = []
    
    # user_member: Heavy "ultralight" tag affinity
    print("Generating events for user_member (ultralight preference)...")
    member_events = generate_clickstream_data(
        es, "user_member", 50, tag_preferences=["ultralight"]
    )
    all_events.extend(member_events)
    
    # user_business: "family", "bulk" tag affinity
    print("Generating events for user_business (family/bulk preference)...")
    business_events = generate_clickstream_data(
        es, "user_business", 30, tag_preferences=["family", "budget"]
    )
    all_events.extend(business_events)
    
    # user_new: Random distribution
    print("Generating events for user_new (random)...")
    new_events = generate_clickstream_data(es, "user_new", 20)
    all_events.extend(new_events)
    
    # Bulk index events
    def doc_generator():
        for event in all_events:
            yield {
                "_index": "user-clickstream",
                "_source": event
            }
    
    print(f"Indexing {len(all_events)} clickstream events...")
    success, failed = bulk(es, doc_generator(), raise_on_error=False)
    
    if failed:
        print(f"Warning: {len(failed)} events failed to index")
    else:
        print(f"Successfully indexed {success} events")
    
    # Refresh index
    es.indices.refresh(index="user-clickstream")
    print("Index refreshed")


def main():
    seed_clickstream()


if __name__ == "__main__":
    main()

