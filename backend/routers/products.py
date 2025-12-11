from fastapi import APIRouter, HTTPException
from typing import List, Optional
from services.elastic_client import get_elastic_client

router = APIRouter()


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
    limit: int = 20
):
    """
    Pure BM25 keyword search - no semantic matching.
    Uses simple match query for basic keyword-based search.
    """
    es = get_elastic_client()
    
    try:
        response = es.search(
            index="product-catalog",
            query={
                "match": {
                    "title": {
                        "query": q,
                        "fuzziness": "AUTO"
                    }
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
        for hit in response["hits"]["hits"]:
            product = hit["_source"]
            product["id"] = hit["_id"]
            product["_score"] = hit["_score"]
            product["_highlight"] = hit.get("highlight", {})
            products.append(product)
        
        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "query": q,
            "search_type": "lexical"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lexical search error: {str(e)}")


@router.get("/products/search/hybrid")
async def hybrid_search(
    q: str,
    limit: int = 20
):
    """
    Hybrid search combining semantic and lexical matching.
    Uses multi_match with best_fields for combined scoring.
    """
    es = get_elastic_client()
    
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
        for hit in response["hits"]["hits"]:
            product = hit["_source"]
            product["id"] = hit["_id"]
            product["_score"] = hit["_score"]
            product["_highlight"] = hit.get("highlight", {})
            products.append(product)
        
        return {
            "products": products,
            "total": response["hits"]["total"]["value"],
            "query": q,
            "search_type": "hybrid"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")


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


