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

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://kubernetes-vm:30920")
ES_APIKEY = os.getenv("ELASTICSEARCH_APIKEY", "")

if not ES_APIKEY:
    raise ValueError("ELASTICSEARCH_APIKEY environment variable is required")

es = Elasticsearch(
    [ES_URL],
    api_key=ES_APIKEY,
    request_timeout=60
)


def create_product_catalog_index():
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
            print("Index 'product-catalog' already exists, deleting...")
            es.indices.delete(index="product-catalog")
    except Exception as e:
        print(f"Note: {e}")
    
    es.indices.create(index="product-catalog", mappings=mapping)
    print("Created index: product-catalog")


def create_clickstream_index():
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
            print("Index 'user-clickstream' already exists, deleting...")
            es.indices.delete(index="user-clickstream")
    except Exception as e:
        print(f"Note: {e}")
    
    es.indices.create(index="user-clickstream", mappings=mapping)
    print("Created index: user-clickstream")


def main():
    print("Setting up Elasticsearch indices...")
    create_product_catalog_index()
    create_clickstream_index()
    print("Setup complete!")


if __name__ == "__main__":
    main()

