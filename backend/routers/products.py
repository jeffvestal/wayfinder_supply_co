from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services.elastic_client import get_elastic_client
import logging

logger = logging.getLogger("wayfinder.backend")

router = APIRouter()


def get_user_preferences(user_id: Optional[str], es) -> dict:
    """
    Get user preferences (tags and categories) from clickstream data.
    Returns dict with 'tags' and 'categories' lists.
    """
    if not user_id:
        return {"tags": [], "categories": []}
    
    try:
        # #region agent log
        try:
            import json, time; open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"products.py:get_user_prefs","message":"Entry","data":{"user_id":user_id},"timestamp":time.time()*1000,"sessionId":"wow-debug","runId":"run1","hypothesisId":"H2"})+'\n')
        except Exception: pass
        # #endregion

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
        
        # #region agent log
        try:
            import json, time; open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"products.py:get_user_prefs","message":"Tag response","data":{"hits":tag_response.get("hits",{}).get("total",{}),"aggs":tag_response.get("aggregations",{})},"timestamp":time.time()*1000,"sessionId":"wow-debug","runId":"run1","hypothesisId":"H3"})+'\n')
        except Exception: pass
        # #endregion

        tags = [bucket["key"] for bucket in tag_response.get("aggregations", {}).get("top_tags", {}).get("buckets", [])]
        
        # Get top categories by looking at products user viewed
        category_query = {
            "bool": {
                "must": [
                    {"term": {"user_id": user_id}},
                    {"term": {"action": "view_item"}}
                ]
            }
        }
        
        # #region agent log
        try:
            import json, time; open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"products.py:get_user_prefs","message":"Category query","data":{"query":category_query},"timestamp":time.time()*1000,"sessionId":"wow-debug","runId":"run1","hypothesisId":"H4"})+'\n')
        except Exception: pass
        # #endregion

        category_response = es.search(
            index="user-clickstream",
            query=category_query,
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

        # #region agent log
        try:
            import json, time; open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"products.py:get_user_prefs","message":"Category response","data":{"hits":category_response.get("hits",{}).get("total",{}),"aggs":category_response.get("aggregations",{})},"timestamp":time.time()*1000,"sessionId":"wow-debug","runId":"run1","hypothesisId":"H1"})+'\n')
        except Exception: pass
        # #endregion

        product_ids = [bucket["key"] for bucket in category_response.get("aggregations", {}).get("product_ids", {}).get("buckets", [])]
        
        categories = []
        if product_ids:
            # Get categories from products
            products_response = es.mget(index="product-catalog", ids=product_ids[:20])
            # #region agent log
            try:
                import json, time; open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"products.py:get_user_prefs","message":"Mget products","data":{"ids":product_ids[:20],"found":[d.get("found") for d in products_response.get("docs",[])]},"timestamp":time.time()*1000,"sessionId":"wow-debug","runId":"run1","hypothesisId":"H5"})+'\n')
            except Exception: pass
            # #endregion
            for doc in products_response.get("docs", []):
                if doc.get("found") and "_source" in doc:
                    cat = doc["_source"].get("category")
                    if cat and cat not in categories:
                        categories.append(cat)
        
        # #region agent log
        try:
            import json, time; open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"products.py:get_user_prefs","message":"Final result","data":{"tags":tags,"categories":categories},"timestamp":time.time()*1000,"sessionId":"wow-debug","runId":"run1","hypothesisId":"H1"})+'\n')
        except Exception: pass
        # #endregion
        
        logger.info(f"User preferences for {user_id}: tags={tags}, categories={categories}")
        return {"tags": tags, "categories": categories}
    except Exception as e:
        # If anything fails, return empty preferences
        logger.error(f"Error getting user preferences for {user_id}: {str(e)}")
        return {"tags": [], "categories": []}


@router.get("/products/debug/clickstream/{user_id}")
async def debug_clickstream(user_id: str):
    """Debug endpoint to check clickstream data for a user."""
    es = get_elastic_client()
    try:
        # Check if index exists
        exists = es.indices.exists(index="user-clickstream")
        
        # Search for raw documents for this user
        raw_docs = es.search(
            index="user-clickstream",
            query={"term": {"user_id": user_id}},
            size=5
        )
        
        # Get global stats for the index
        global_stats = es.count(index="user-clickstream")
        
        # Get a sample of ANY documents to see what user_ids exist
        sample_any = es.search(
            index="user-clickstream",
            query={"match_all": {}},
            size=5
        )
        
        # Check for tags aggregation for this user
        tag_aggs = es.search(
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
        
        return {
            "index_exists": exists,
            "user_id": user_id,
            "total_docs_in_index": global_stats["count"],
            "user_hits": raw_docs["hits"]["total"]["value"],
            "sample_user_docs": raw_docs["hits"]["hits"],
            "sample_any_docs": sample_any["hits"]["hits"],
            "tag_aggs": tag_aggs.get("aggregations", {})
        }
    except Exception as e:
        return {"error": str(e)}


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
        
        # #region agent log
        # #endregion
        
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
        
        user_prefs = None
        if user_id:
            user_prefs = get_user_preferences(user_id, es)

        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "query": q,
            "es_query": query,  # The actual Elasticsearch query
            "user_prefs": user_prefs,
            "raw_hits": raw_hits,
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
    Real hybrid search combining semantic (ELSER) and lexical (BM25) using linear combination.
    Uses weighted linear combination to merge results from both search types.
    """
    es = get_elastic_client()
    
    # Build retriever config for Linear combination (weighted)
    lexical_query = {
        "multi_match": {
            "query": q,
            "fields": ["title^3", "description^2", "category^2", "brand", "tags"],
            "type": "best_fields",
            "fuzziness": "AUTO"
        }
    }

    # Add personalization if user_id provided
    personalized = False
    if user_id:
        prefs = get_user_preferences(user_id, es)
        if prefs["tags"] or prefs["categories"]:
            personalized = True
            logger.info(f"Applying STRONG personalization for {user_id} in hybrid search")
            lexical_query = {
                "function_score": {
                    "query": lexical_query,
                    "functions": [
                        {
                            "filter": {"terms": {"tags": prefs["tags"]}},
                            "weight": 10.0
                        },
                        {
                            "filter": {"terms": {"category": prefs["categories"]}},
                            "weight": 5.0
                        }
                    ],
                    "boost_mode": "multiply",
                    "score_mode": "sum"
                }
            }

    retriever_config = {
        "linear": {
            "retrievers": [
                # Semantic retriever (ELSER via semantic_text) - higher weight for meaning
                {
                    "retriever": {
                        "standard": {
                            "query": {
                                "semantic": {
                                    "field": "description.semantic",
                                    "query": q
                                }
                            }
                        }
                    },
                    "weight": 0.7  # Semantic gets higher weight
                },
                # Lexical retriever (BM25) - for exact matches
                {
                    "retriever": {
                        "standard": {
                            "query": lexical_query
                        }
                    },
                    "weight": 0.3  # Lexical for keyword boost
                }
            ]
        }
    }
    
    # Build the es_query representation for display
    es_query_display = {
        "retriever": retriever_config,
        "highlight": {"fields": {"title": {}, "description": {}}}
    }
    
    user_prefs = None
    if user_id:
        user_prefs = get_user_preferences(user_id, es)

    try:
        # Use retriever as top-level parameter (correct syntax for ES Python client)
        response = es.search(
            index="product-catalog",
            retriever=retriever_config,
            highlight={
                "fields": {
                    "title": {},
                    "description": {}
                }
            },
            size=limit
        )
        
        # #region agent log
        # #endregion
        
        products = []
        raw_hits = []
        
        for hit in response["hits"]["hits"]:
            product = hit["_source"]
            product["id"] = hit["_id"]
            product["_score"] = hit.get("_score")
            product["_highlight"] = hit.get("highlight", {})
            products.append(product)
            # Store raw hit for query viewer (top 3 only)
            if len(raw_hits) < 3:
                raw_hits.append({
                    "_id": hit["_id"],
                    "_score": hit.get("_score"),
                    "_source": hit["_source"],
                    "highlight": hit.get("highlight", {})
                })
        
        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "query": q,
            "es_query": es_query_display,
            "user_prefs": user_prefs,
            "raw_hits": raw_hits,
            "search_type": "hybrid_linear",
            "personalized": personalized
        }
    except Exception as e:
        # Don't silently fallback - fail clearly so we know there's an issue
        error_msg = str(e)
        print(f"ERROR: Hybrid search failed: {error_msg}")
        
        # Check if it's a semantic field issue
        if "semantic" in error_msg.lower() or "inference" in error_msg.lower():
            raise HTTPException(
                status_code=500, 
                detail=f"Hybrid search requires semantic_text field 'description.semantic'. Error: {error_msg}"
            )
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {error_msg}")


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


