#!/usr/bin/env python3
"""Index OTel trace JSONL files into Elasticsearch with explicit mapping."""

import argparse
import json
import os
import sys

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

INDEX_NAME = "otel-traces-wayfinder"
BATCH_SIZE = 500

INDEX_CONFIG = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
    },
    "mappings": {
        "dynamic": False,
        "properties": {
            "@timestamp": {"type": "date_nanos"},
            "trace": {
                "properties": {
                    "id": {"type": "keyword", "ignore_above": 256},
                }
            },
            "span": {
                "properties": {
                    "id": {"type": "keyword", "ignore_above": 256},
                    "name": {"type": "keyword", "ignore_above": 1024},
                    "type": {"type": "keyword"},
                    "subtype": {"type": "keyword"},
                    "action": {"type": "keyword"},
                    "duration": {
                        "properties": {
                            "us": {"type": "long"},
                        }
                    },
                }
            },
            "parent": {
                "properties": {
                    "id": {"type": "keyword", "ignore_above": 256},
                }
            },
            "service": {
                "properties": {
                    "name": {"type": "keyword"},
                }
            },
            "http": {
                "properties": {
                    "route": {"type": "keyword"},
                    "response": {
                        "properties": {
                            "status_code": {"type": "integer"},
                        }
                    },
                }
            },
            "db": {
                "properties": {
                    "statement": {"type": "text"},
                    "statement_semantic": {"type": "semantic_text"},
                    "type": {"type": "keyword"},
                    "system": {"type": "keyword"},
                    "lock": {
                        "properties": {
                            "acquired": {"type": "boolean"},
                            "timeout_us": {"type": "long"},
                        }
                    },
                }
            },
            "inventory": {
                "properties": {
                    "quantity_requested": {"type": "integer"},
                    "quantity_available": {"type": "integer"},
                }
            },
            "status": {
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "text"},
                }
            },
            "error": {
                "properties": {
                    "message": {"type": "text"},
                }
            },
            "transaction": {
                "properties": {
                    "id": {"type": "keyword", "ignore_above": 256},
                    "type": {"type": "keyword"},
                }
            },
        },
    },
}


def get_client():
    url = os.environ.get("ELASTIC_URL")
    api_key = os.environ.get("ELASTIC_API_KEY")
    if not url:
        sys.exit("ERROR: ELASTIC_URL env var is required")
    if not api_key:
        sys.exit("ERROR: ELASTIC_API_KEY env var is required")
    return Elasticsearch(url, api_key=api_key)


def ensure_index(es, recreate=False):
    exists = es.indices.exists(index=INDEX_NAME).body
    if exists and recreate:
        es.indices.delete(index=INDEX_NAME)
        print(f"Deleted existing index: {INDEX_NAME}")
        exists = False
    if not exists:
        es.indices.create(index=INDEX_NAME, **INDEX_CONFIG)
        print(f"Created index: {INDEX_NAME}")
    else:
        print(f"Index {INDEX_NAME} exists — appending docs")


def iter_actions(jsonl_path):
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            yield {"_index": INDEX_NAME, "_source": doc}


def main():
    p = argparse.ArgumentParser(description="Bulk-index OTel trace JSONL into Elasticsearch")
    p.add_argument("files", nargs="+", help="JSONL files to index")
    p.add_argument("--recreate", action="store_true", help="Delete and recreate index before indexing")
    args = p.parse_args()

    es = get_client()
    ensure_index(es, recreate=args.recreate)

    total_indexed = 0
    total_errors = 0

    for path in args.files:
        print(f"Indexing {path} ...")
        success, errors = bulk(
            es,
            iter_actions(path),
            chunk_size=BATCH_SIZE,
            raise_on_error=False,
        )
        total_indexed += success
        error_count = len(errors) if isinstance(errors, list) else int(errors)
        total_errors += error_count
        print(f"  {success:,} docs indexed, {error_count} errors")
        if errors and isinstance(errors, list):
            for err in errors[:5]:
                print(f"    {err}")

    print(f"\nTotal: {total_indexed:,} docs indexed, {total_errors} errors")
    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
