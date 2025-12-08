#!/usr/bin/env python3
"""
Setup Elasticsearch indices and inference endpoints for Wayfinder Supply Co.
"""

import os
import json
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


def create_product_catalog_index(force: bool = False):
    """Create product-catalog index with semantic_text mapping."""
    mapping = {
        "properties": {
            "id": {"type": "keyword"},
            "title": {"type": "text"},
            "brand": {"type": "keyword"},
            "description": {
                "type": "text",
                "fields": {
                    "semantic": {
                        "type": "semantic_text",
                        "inference_id": ".elser-2-elastic",
                        "search_inference_id": ".elser-2-elasticsearch",
                        "model_settings": {
                            "service": "elastic",
                            "task_type": "sparse_embedding"
                        }
                    }
                }
            },
            "image_url": {"type": "keyword"},
            "category": {"type": "keyword"},
            "subcategory": {"type": "keyword"},
            "attributes": {
                "properties": {
                    "temp_rating_f": {"type": "integer"},
                    "weight_lb": {"type": "float"},
                    "season": {"type": "keyword"},
                    "capacity": {"type": "integer"},
                    "capacity_l": {"type": "integer"},
                    "fuel_type": {"type": "keyword"},
                    "waterproof": {"type": "boolean"},
                    "length_cm": {"type": "integer"},
                    "width_mm": {"type": "integer"}
                }
            },
            "price": {"type": "float"},
            "tags": {"type": "keyword"}
        }
    }
    
    try:
        if es.indices.exists(index="product-catalog"):
            if force:
                print("Index 'product-catalog' already exists, deleting (--force)...")
                es.indices.delete(index="product-catalog")
            else:
                print("✓ Index 'product-catalog' already exists, skipping")
                return
    except Exception as e:
        print(f"Note: {e}")
    
    es.indices.create(index="product-catalog", mappings=mapping)
    print("✓ Created index: product-catalog")


def create_clickstream_index(force: bool = False):
    """Create user-clickstream index."""
    mapping = {
        "properties": {
            "@timestamp": {"type": "date"},
            "user_id": {"type": "keyword"},
            "action": {"type": "keyword"},
            "product_id": {"type": "keyword"},
            "meta_tags": {"type": "keyword"}
        }
    }
    
    try:
        if es.indices.exists(index="user-clickstream"):
            if force:
                print("Index 'user-clickstream' already exists, deleting (--force)...")
                es.indices.delete(index="user-clickstream")
            else:
                print("✓ Index 'user-clickstream' already exists, skipping")
                return
    except Exception as e:
        print(f"Note: {e}")
    
    es.indices.create(index="user-clickstream", mappings=mapping)
    print("✓ Created index: user-clickstream")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Setup Elasticsearch indices")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate indices if they already exist (WARNING: deletes data!)"
    )
    args = parser.parse_args()
    
    print("Setting up Elasticsearch indices...")
    if args.force:
        print("⚠ Force mode: existing indices will be deleted!")
    create_product_catalog_index(force=args.force)
    create_clickstream_index(force=args.force)
    print("Setup complete!")


if __name__ == "__main__":
    main()

