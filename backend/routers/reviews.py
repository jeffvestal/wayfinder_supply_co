from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from services.elastic_client import get_elastic_client
from datetime import datetime
import uuid

router = APIRouter()


class ReviewCreate(BaseModel):
    rating: int
    title: str
    text: str


@router.get("/products/{product_id}/reviews")
async def get_product_reviews(
    product_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    Get reviews for a product.
    """
    es = get_elastic_client()
    
    try:
        response = es.search(
            index="product-reviews",
            query={"term": {"product_id": product_id}},
            size=limit,
            from_=offset,
            sort=[{"timestamp": {"order": "desc"}}]
        )
        
        reviews = []
        for hit in response["hits"]["hits"]:
            review = hit["_source"]
            review["id"] = hit["_id"]
            reviews.append(review)
        
        return {
            "reviews": reviews,
            "total": response["hits"]["total"]["value"],
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")


@router.post("/products/{product_id}/reviews")
async def submit_review(
    product_id: str,
    review: ReviewCreate,
    user_id: str
):
    """
    Submit a new review for a product.
    """
    es = get_elastic_client()
    
    # Validate rating
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Check if product exists
    try:
        product = es.get(index="product-catalog", id=product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Create review document
    review_id = str(uuid.uuid4())
    review_doc = {
        "product_id": product_id,
        "user_id": user_id,
        "rating": review.rating,
        "title": review.title,
        "text": review.text,
        "timestamp": datetime.now().isoformat(),
        "verified_purchase": True  # Assume verified for workshop
    }
    
    try:
        # Index the review
        es.index(index="product-reviews", id=review_id, document=review_doc)
        
        # Update product's average rating and review count
        # Get all reviews for this product
        all_reviews_response = es.search(
            index="product-reviews",
            query={"term": {"product_id": product_id}},
            size=10000  # Get all reviews
        )
        
        reviews = [hit["_source"] for hit in all_reviews_response["hits"]["hits"]]
        if reviews:
            total_rating = sum(r["rating"] for r in reviews)
            average_rating = round(total_rating / len(reviews), 1)
            review_count = len(reviews)
            
            # Update product document
            es.update(
                index="product-catalog",
                id=product_id,
                doc={
                    "average_rating": average_rating,
                    "review_count": review_count
                }
            )
        
        return {"message": "Review submitted", "review_id": review_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting review: {str(e)}")


