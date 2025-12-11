from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services.elastic_client import get_elastic_client

router = APIRouter()


def get_user_preferences(user_id: Optional[str], es) -> dict:
    """
    Get user preferences (tags and categories) from clickstream data.
    Returns dict with 'tags' and 'categories' lists.
    """
    if not user_id:
        return {"tags": [], "categories": []}
    
    try:
        # Get top tags from clickstream
        tag_response = es.search(
            index="user-clickstream",
            query={
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {"exists": {"field": "meta_tags"}}
                    ]
                }
            },
            size=0,
            aggs={
                "top_tags": {
                    "terms": {
                        "field": "meta_tags",
                        "size": 5
                    }
                }
            }
        )
        tags = [bucket["key"] for bucket in tag_response.get("aggregations", {}).get("top_tags", {}).get("buckets", [])]
        
        # Get top categories by looking at products user viewed
        category_response = es.search(
            index="user-clickstream",
            query={
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {"term": {"action": "view_item"}}
                    ]
                }
            },
            size=0,
            aggs={
                "product_ids": {
                    "terms": {
                        "field": "product_id",
                        "size": 50
                    }
                }
            }
        )
        product_ids = [bucket["key"] for bucket in category_response.get("aggregations", {}).get("product_ids", {}).get("buckets", [])]
        
        categories = []
        if product_ids:
            # Get categories from products
            products_response = es.mget(index="product-catalog", ids=product_ids[:20])
            for doc in products_response.get("docs", []):
                if doc.get("found") and "_source" in doc:
                    cat = doc["_source"].get("category")
                    if cat and cat not in categories:
                        categories.append(cat)
        
        return {"tags": tags, "categories": categories}
    except Exception as e:
        # If anything fails, return empty preferences
        print(f"Warning: Could not get user preferences: {e}")
        return {"tags": [], "categories": []}


@router.get("/products")
async def list_products(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    List products from Elasticsearch.
    """
    es = get_elastic_client()
    
    query = {"match_all": {}}
    if category:
        query = {"term": {"category": category}}
    
    try:
        response = es.search(
            index="product-catalog",
            query=query,
            size=limit,
            from_=offset,
            sort=[{"_score": {"order": "desc"}}]
        )
        
        products = []
        for hit in response["hits"]["hits"]:
            product = hit["_source"]
            product["id"] = hit["_id"]
            products.append(product)
        
        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")


@router.get("/products/search")
async def search_products(
    q: str,
    limit: int = 20
):
    """
    Semantic search for products.
    NOTE: This route MUST come before /products/{product_id} to avoid matching "search" as a product_id
    """
    es = get_elastic_client()
    
    try:
        response = es.search(
            index="product-catalog",
            query={
                "multi_match": {
                    "query": q,
                    "fields": ["title^3", "description", "category^2", "brand"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            size=limit
        )
        
        products = []
        for hit in response["hits"]["hits"]:
            product = hit["_source"]
            product["id"] = hit["_id"]
            product["_score"] = hit["_score"]
            products.append(product)
        
        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "query": q
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/products/search/lexical")
async def lexical_search(
    q: str,
    limit: int = 20,
    user_id: Optional[str] = Query(None, description="User ID for personalization")
):
    """
    Pure BM25 keyword search - no semantic matching.
    Uses simple match query for basic keyword-based search.
    """
    es = get_elastic_client()
    
    try:
        # Base lexical query
        base_query = {
            "match": {
                "title": {
                    "query": q,
                    "fuzziness": "AUTO"
                }
            }
        }
        
        # Add personalization if user_id provided
        query = base_query
        if user_id:
            prefs = get_user_preferences(user_id, es)
            if prefs["tags"] or prefs["categories"]:
                query = {
                    "function_score": {
                        "query": base_query,
                        "functions": [
                            {
                                "filter": {"terms": {"tags": prefs["tags"]}},
                                "weight": 1.5
                            },
                            {
                                "filter": {"terms": {"category": prefs["categories"]}},
                                "weight": 1.3
                            }
                        ],
                        "boost_mode": "multiply",
                        "score_mode": "sum"
                    }
                }
        
        response = es.search(
            index="product-catalog",
            query=query,
            highlight={
                "fields": {
                    "title": {},
                    "description": {}
                }
            },
            size=limit
        )
        
        products = []
        raw_hits = []
        for hit in response["hits"]["hits"]:
            product = hit["_source"]
            product["id"] = hit["_id"]
            product["_score"] = hit["_score"]
            product["_highlight"] = hit.get("highlight", {})
            products.append(product)
            # Store raw hit for query viewer (top 3 only)
            if len(raw_hits) < 3:
                raw_hits.append({
                    "_id": hit["_id"],
                    "_score": hit["_score"],
                    "_source": hit["_source"],
                    "highlight": hit.get("highlight", {})
                })
        
        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "query": q,
            "es_query": query,  # The actual Elasticsearch query
            "raw_hits": raw_hits,  # Top 3 raw response documents
            "search_type": "lexical",
            "personalized": user_id is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lexical search error: {str(e)}")


@router.get("/products/search/hybrid")
async def hybrid_search(
    q: str,
    limit: int = 20,
    user_id: Optional[str] = Query(None, description="User ID for personalization")
):
    """
    Real hybrid search combining semantic (ELSER) and lexical (BM25) using retrievers with RRF.
    """
    es = get_elastic_client()
    
    try:
        # Build base query with retrievers
        # Using RRF (Reciprocal Rank Fusion) to combine semantic and lexical results
        base_query = {
            "retriever": {
                "rrf": {
                    "retrievers": [
                        {
                            "standard": {
                                "query": {
                                    "multi_match": {
                                        "query": q,
                                        "fields": ["title^3", "description^2", "category^2", "brand", "tags"],
                                        "type": "best_fields",
                                        "fuzziness": "AUTO"
                                    }
                                }
                            }
                        },
                        {
                            "standard": {
                                "query": {
                                    "semantic": {
                                        "field": "description.semantic",
                                        "query": q
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        # Add personalization if user_id provided
        query = base_query
        if user_id:
            prefs = get_user_preferences(user_id, es)
            if prefs["tags"] or prefs["categories"]:
                # Wrap in function_score for boosting
                query = {
                    "function_score": {
                        "query": base_query,
                        "functions": [
                            {
                                "filter": {"terms": {"tags": prefs["tags"]}},
                                "weight": 1.5
                            },
                            {
                                "filter": {"terms": {"category": prefs["categories"]}},
                                "weight": 1.3
                            }
                        ],
                        "boost_mode": "multiply",
                        "score_mode": "sum"
                    }
                }
        
        response = es.search(
            index="product-catalog",
            query=query,
            highlight={
                "fields": {
                    "title": {},
                    "description": {}
                }
            },
            size=limit
        )
        
        products = []
        raw_hits = []
        for hit in response["hits"]["hits"]:
            product = hit["_source"]
            product["id"] = hit["_id"]
            product["_score"] = hit["_score"]
            product["_highlight"] = hit.get("highlight", {})
            products.append(product)
            # Store raw hit for query viewer (top 3 only)
            if len(raw_hits) < 3:
                raw_hits.append({
                    "_id": hit["_id"],
                    "_score": hit["_score"],
                    "_source": hit["_source"],
                    "highlight": hit.get("highlight", {})
                })
        
        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "query": q,
            "es_query": query,  # The actual Elasticsearch query
            "raw_hits": raw_hits,  # Top 3 raw response documents
            "search_type": "hybrid",
            "personalized": user_id is not None
        }
    except Exception as e:
        # Fallback to multi_match if retrievers fail (e.g., semantic_text field not available)
        print(f"Warning: Hybrid search with retrievers failed, falling back: {e}")
        try:
            response = es.search(
                index="product-catalog",
                query={
                    "multi_match": {
                        "query": q,
                        "fields": ["title^3", "description^2", "category^2", "brand", "tags"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                highlight={
                    "fields": {
                        "title": {},
                        "description": {}
                    }
                },
                size=limit
            )
            
            products = []
            raw_hits = []
            for hit in response["hits"]["hits"]:
                product = hit["_source"]
                product["id"] = hit["_id"]
                product["_score"] = hit["_score"]
                product["_highlight"] = hit.get("highlight", {})
                products.append(product)
                # Store raw hit for query viewer (top 3 only)
                if len(raw_hits) < 3:
                    raw_hits.append({
                        "_id": hit["_id"],
                        "_score": hit["_score"],
                        "_source": hit["_source"],
                        "highlight": hit.get("highlight", {})
                    })
            
            return {
                "products": products,
                "total": response["hits"]["total"]["value"],
                "query": q,
                "es_query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["title^3", "description^2", "category^2", "brand", "tags"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "raw_hits": raw_hits,
                "search_type": "hybrid_fallback",
                "personalized": False
            }
        except Exception as fallback_error:
            raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(fallback_error)}")


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    """
    Get a single product by ID.
    """
    es = get_elastic_client()
    
    try:
        response = es.get(index="product-catalog", id=product_id)
        product = response["_source"]
        product["id"] = response["_id"]
        return product
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Product not found: {str(e)}")


