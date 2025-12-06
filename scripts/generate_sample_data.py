#!/usr/bin/env python3
"""
Generate sample product data for testing (without AI generation).
"""

import json
import random
import uuid
from pathlib import Path

PRODUCTS = [
    {
        "title": "Wayfinder Inferno 0° Sleeping Bag",
        "brand": "Wayfinder Supply",
        "description": "Ultralight down sleeping bag rated for 0°F. Perfect for winter camping and alpine adventures. Features premium 800-fill down and water-resistant shell.",
        "category": "camping",
        "subcategory": "sleeping_bags",
        "price": 349.99,
        "tags": ["ultralight", "expedition"],
        "attributes": {"temp_rating_f": 0, "weight_lb": 2.1, "season": "4-season"}
    },
    {
        "title": "Wayfinder Pro Tire Chains",
        "brand": "Wayfinder Supply",
        "description": "Heavy-duty tire chains for winter driving. Meets traction law requirements for mountain passes. Easy installation with self-tensioning design.",
        "category": "camping",
        "subcategory": "accessories",
        "price": 149.99,
        "tags": ["safety", "winter"],
        "attributes": {"weight_lb": 8.5}
    },
    {
        "title": "Summit Pro 65L Backpack",
        "brand": "Summit Pro",
        "description": "Lightweight backpacking pack with excellent weight distribution. Features adjustable suspension and multiple access points.",
        "category": "hiking",
        "subcategory": "backpacks",
        "price": 289.99,
        "tags": ["ultralight"],
        "attributes": {"capacity_l": 65, "weight_lb": 3.2}
    },
    {
        "title": "TrailBlazer 3-Season Tent",
        "brand": "TrailBlazer",
        "description": "Spacious 4-person tent perfect for family camping. Easy setup with color-coded poles and full rainfly coverage.",
        "category": "camping",
        "subcategory": "tents",
        "price": 249.99,
        "tags": ["family", "budget"],
        "attributes": {"capacity": 4, "weight_lb": 8.5, "season": "3-season"}
    },
    {
        "title": "PocketRocket Deluxe Stove",
        "brand": "Wayfinder Supply",
        "description": "Compact canister stove with precise flame control. Boils water quickly and efficiently. Perfect for backpacking.",
        "category": "camping",
        "subcategory": "cooking",
        "price": 74.99,
        "tags": ["ultralight"],
        "attributes": {"weight_lb": 0.8, "fuel_type": "canister"}
    },
    {
        "title": "Alpine Edge Hiking Boots",
        "brand": "Alpine Edge",
        "description": "Waterproof hiking boots with excellent ankle support. Vibram sole provides superior traction on all terrain.",
        "category": "hiking",
        "subcategory": "footwear",
        "price": 199.99,
        "tags": ["expedition"],
        "attributes": {"weight_lb": 2.5, "waterproof": True}
    },
    {
        "title": "Wayfinder Comfort Sleep Bag 40°F",
        "brand": "Wayfinder Supply",
        "description": "Affordable sleeping bag for summer camping. Synthetic insulation stays warm even when wet. Great for families.",
        "category": "camping",
        "subcategory": "sleeping_bags",
        "price": 79.99,
        "tags": ["budget", "family"],
        "attributes": {"temp_rating_f": 40, "weight_lb": 3.8, "season": "summer"}
    },
    {
        "title": "Summit Pro Trekking Poles",
        "brand": "Summit Pro",
        "description": "Lightweight carbon fiber trekking poles. Adjustable length with ergonomic grips. Reduces strain on knees and improves balance.",
        "category": "hiking",
        "subcategory": "trekking_poles",
        "price": 129.99,
        "tags": ["ultralight"],
        "attributes": {"weight_lb": 0.9}
    },
    {
        "title": "Wayfinder Family Dome Tent 6P",
        "brand": "Wayfinder Supply",
        "description": "Large family tent sleeps 6 comfortably. Stand-up height and room divider included. Perfect for car camping.",
        "category": "camping",
        "subcategory": "tents",
        "price": 299.99,
        "tags": ["family", "budget"],
        "attributes": {"capacity": 6, "weight_lb": 15.2, "season": "3-season"}
    },
    {
        "title": "TrailBlazer GPS Navigator",
        "brand": "TrailBlazer",
        "description": "Handheld GPS device with preloaded topo maps. Long battery life and weather-resistant design. Essential for backcountry navigation.",
        "category": "hiking",
        "subcategory": "navigation",
        "price": 249.99,
        "tags": ["expedition"],
        "attributes": {"weight_lb": 0.6}
    }
]


def generate_products(output_file: str = "generated_products/products.json"):
    """Generate products JSON file."""
    products = []
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for product_template in PRODUCTS:
        product_id = f"WF-{product_template['category'][:3].upper()}-{product_template['subcategory'][:3].upper()}-{str(uuid.uuid4())[:8].upper()}"
        
        product = {
            "id": product_id,
            "title": product_template["title"],
            "brand": product_template["brand"],
            "description": product_template["description"],
            "category": product_template["category"],
            "subcategory": product_template["subcategory"],
            "price": product_template["price"],
            "tags": product_template["tags"],
            "attributes": product_template["attributes"],
            "image_url": f"/images/products/{product_id}.jpg"
        }
        
        products.append(product)
    
    with open(output_path, 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"Generated {len(products)} products")
    print(f"Saved to: {output_path}")
    
    return products


if __name__ == "__main__":
    import sys
    output_file = sys.argv[1] if len(sys.argv) > 1 else "generated_products/products.json"
    generate_products(output_file)

