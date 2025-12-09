#!/usr/bin/env python3
"""
Update products.json with actual review statistics from reviews.json
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    # Load reviews
    reviews_path = Path("generated_products/reviews.json")
    with open(reviews_path, 'r') as f:
        reviews = json.load(f)
    
    # Calculate stats per product
    product_stats = defaultdict(lambda: {"ratings": [], "count": 0})
    
    for review in reviews:
        product_id = review["product_id"]
        product_stats[product_id]["ratings"].append(review["rating"])
        product_stats[product_id]["count"] += 1
    
    # Calculate averages
    for product_id in product_stats:
        ratings = product_stats[product_id]["ratings"]
        product_stats[product_id]["average_rating"] = round(sum(ratings) / len(ratings), 1)
        product_stats[product_id]["review_count"] = len(ratings)
    
    # Load products
    products_path = Path("generated_products/products.json")
    with open(products_path, 'r') as f:
        products = json.load(f)
    
    # Update products with stats
    updated_count = 0
    for product in products:
        product_id = product["id"]
        if product_id in product_stats:
            product["average_rating"] = product_stats[product_id]["average_rating"]
            product["review_count"] = product_stats[product_id]["review_count"]
            updated_count += 1
        else:
            # No reviews yet
            product["average_rating"] = 0.0
            product["review_count"] = 0
    
    # Save updated products
    with open(products_path, 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"✓ Updated {updated_count} products with review statistics")
    print(f"  Total products: {len(products)}")
    print(f"  Products with reviews: {len(product_stats)}")

if __name__ == "__main__":
    main()

