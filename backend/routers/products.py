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


@router.get("/products/search")
async def search_products(
    q: str,
    limit: int = 20
):
    """
    Semantic search for products.
    """
    es = get_elastic_client()
    
    try:
        response = es.search(
            index="product-catalog",
            query={
                "multi_match": {
                    "query": q,
                    "fields": ["title^2", "description", "description.semantic"],
                    "type": "best_fields"
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


