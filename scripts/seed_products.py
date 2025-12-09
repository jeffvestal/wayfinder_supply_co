#!/usr/bin/env python3
"""
Seed products into Elasticsearch product-catalog index.
"""

import json
import os
import sys
from pathlib import Path
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

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


def seed_products(products_file: str):
    """Bulk index products from JSON file."""
    products_path = Path(products_file)
    
    if not products_path.exists():
        print(f"Error: Products file not found: {products_file}")
        sys.exit(1)
    
    with open(products_path, 'r') as f:
        products = json.load(f)
    
    def doc_generator():
        for product in products:
            yield {
                "_index": "product-catalog",
                "_id": product["id"],
                "_source": product
            }
    
    print(f"Indexing {len(products)} products...")
    success, failed = bulk(es, doc_generator(), raise_on_error=False)
    
    if failed:
        print(f"Warning: {len(failed)} documents failed to index")
        for item in failed[:5]:  # Show first 5 failures
            print(f"  Failed: {item}")
    else:
        print(f"Successfully indexed {success} products")
    
    # Refresh index
    es.indices.refresh(index="product-catalog")
    print("Index refreshed")


def seed_reviews(reviews_file: str):
    """Bulk index reviews from JSON file."""
    reviews_path = Path(reviews_file)
    
    if not reviews_path.exists():
        print(f"Error: Reviews file not found: {reviews_file}")
        sys.exit(1)
    
    with open(reviews_path, 'r') as f:
        reviews = json.load(f)
    
    def doc_generator():
        for review in reviews:
            yield {
                "_index": "product-reviews",
                "_id": review["id"],
                "_source": review
            }
    
    print(f"Indexing {len(reviews)} reviews...")
    success, failed = bulk(es, doc_generator(), raise_on_error=False)
    
    if failed:
        print(f"Warning: {len(failed)} documents failed to index")
        for item in failed[:5]:  # Show first 5 failures
            print(f"  Failed: {item}")
    else:
        print(f"Successfully indexed {success} reviews")
    
    # Refresh index
    es.indices.refresh(index="product-reviews")
    print("Reviews index refreshed")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed products into Elasticsearch")
    parser.add_argument(
        "--products",
        default="generated_products/products.json",
        help="Path to products JSON file"
    )
    parser.add_argument(
        "--reviews",
        help="Path to reviews JSON file (optional)"
    )
    args = parser.parse_args()
    
    seed_products(args.products)
    
    if args.reviews:
        seed_reviews(args.reviews)


if __name__ == "__main__":
    main()

