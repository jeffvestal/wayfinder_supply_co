from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
from services.elastic_client import get_elastic_client

router = APIRouter()


class ClickEvent(BaseModel):
    user_id: str
    action: str  # "view_item", "add_to_cart", "click_tag"
    product_id: Optional[str] = None
    tag: Optional[str] = None


@router.post("/clickstream")
async def track_event(event: ClickEvent):
    """
    Track a clickstream event for a user.
    Only tracks for guest user (user_new) to preserve pre-generated persona data.
    """
    es = get_elastic_client()
    
    # Build event document
    event_doc = {
        "@timestamp": datetime.now().isoformat(),
        "user_id": event.user_id,
        "action": event.action,
        "product_id": event.product_id,
        "meta_tags": [event.tag] if event.tag else [],
        "session_id": str(uuid.uuid4())  # Generate new session ID for each event
    }
    
    try:
        # Index event to Elasticsearch
        es.index(index="user-clickstream", document=event_doc)
        return {"status": "success", "message": "Event tracked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking event: {str(e)}")


@router.delete("/clickstream/{user_id}")
async def clear_user_history(user_id: str):
    """
    Clear all clickstream events for a user.
    """
    es = get_elastic_client()
    
    try:
        # Delete all events for this user
        result = es.delete_by_query(
            index="user-clickstream",
            query={"term": {"user_id": user_id}}
        )
        
        # Refresh index to make changes visible
        es.indices.refresh(index="user-clickstream")
        
        return {
            "status": "success",
            "message": f"Cleared {result.get('deleted', 0)} events for user {user_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")


@router.get("/clickstream/{user_id}/stats")
async def get_user_stats(user_id: str):
    """
    Get live statistics for a user from their clickstream events.
    Uses aggregations for efficient counting without fetching documents.
    """
    es = get_elastic_client()
    
    try:
        # Use aggregations to count events by action type without fetching documents
        response = es.search(
            index="user-clickstream",
            query={"term": {"user_id": user_id}},
            size=0,  # Don't fetch documents, only aggregations
            aggs={
                "by_action": {
                    "terms": {"field": "action"}
                }
            }
        )
        
        # Extract counts from aggregation buckets
        buckets = response.get("aggregations", {}).get("by_action", {}).get("buckets", [])
        action_counts = {bucket["key"]: bucket["doc_count"] for bucket in buckets}
        
        total_views = action_counts.get("view_item", 0)
        total_cart_adds = action_counts.get("add_to_cart", 0)
        total_events = sum(action_counts.values())
        
        return {
            "user_id": user_id,
            "total_views": total_views,
            "total_cart_adds": total_cart_adds,
            "total_events": total_events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.get("/clickstream/{user_id}/events")
async def get_user_events(user_id: str, action: str = "view_item"):
    """
    Get detailed event list for a user, filtered by action type.
    """
    es = get_elastic_client()
    
    try:
        response = es.search(
            index="user-clickstream",
            query={
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {"term": {"action": action}}
                    ]
                }
            },
            size=100,
            sort=[{"@timestamp": {"order": "desc"}}]
        )
        
        # Collect all product IDs and batch fetch product names
        hits = response["hits"]["hits"]
        product_ids = [hit["_source"].get("product_id") for hit in hits]
        product_ids = [pid for pid in product_ids if pid]  # Filter out None/null
        
        # Batch fetch all products at once using mget
        product_names = {}
        if product_ids:
            try:
                products_response = es.mget(index="product-catalog", ids=product_ids)
                product_names = {
                    doc["_id"]: doc["_source"].get("title", "Unknown Product")
                    for doc in products_response["docs"]
                    if doc.get("found")
                }
            except Exception:
                # If mget fails, fall back to empty dict (will use "Unknown Product")
                product_names = {}
        
        # Build events using cached product names
        events = []
        for hit in hits:
            source = hit["_source"]
            product_id = source.get("product_id")
            product_name = product_names.get(product_id, "Unknown Product") if product_id else "Unknown Product"
            
            events.append({
                "product_id": product_id,
                "product_name": product_name,
                "timestamp": source.get("@timestamp"),
                "action": source.get("action")
            })
        
        return {
            "user_id": user_id,
            "action": action,
            "events": events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

