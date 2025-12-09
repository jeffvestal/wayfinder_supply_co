#!/usr/bin/env python3
"""
Generate product reviews using AI.
Reads products.json and generates reviews matching each product's average rating.
"""

import json
import os
import random
import uuid
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
import argparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not available. Install with: pip install google-generativeai")


# Sample review titles by rating
REVIEW_TITLES = {
    5: ["Perfect!", "Excellent quality", "Highly recommend", "Best purchase", "Love it!", "Exactly as described"],
    4: ["Great product", "Very satisfied", "Good value", "Works well", "Happy with purchase", "Solid choice"],
    3: ["Okay, but...", "Decent", "Average", "It's fine", "Could be better", "Not bad"],
    2: ["Disappointed", "Not what I expected", "Poor quality", "Wouldn't recommend", "Issues with"],
    1: ["Terrible", "Waste of money", "Broken", "Do not buy", "Very disappointed"]
}

# Sample user names for reviews
SAMPLE_USERS = [
    "AdventureSeeker", "MountainLover", "TrailBlazer", "WildernessExplorer", "OutdoorEnthusiast",
    "CampingPro", "HikingHero", "NatureFan", "GearGuru", "AdventureAce", "SummitSeeker",
    "TrailRunner", "Backpacker", "CampMaster", "OutdoorPro", "GearHead", "AdventureAddict"
]


def generate_reviews_batch(product: Dict, ratings: List[int], use_gemini: bool = True) -> List[str]:
    """Generate all review texts for a product in a single API call."""
    if use_gemini and GEMINI_AVAILABLE:
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Build rating distribution summary
            rating_counts = {}
            for r in ratings:
                rating_counts[r] = rating_counts.get(r, 0) + 1
            
            rating_dist = ", ".join([f"{count} {stars}-star" for stars, count in sorted(rating_counts.items(), reverse=True)])
            
            prompt = f"""Generate {len(ratings)} short product reviews (2-3 sentences each) for: {product['title']}

Product description: {product['description']}
Category: {product.get('category', 'outdoor gear')}

Rating distribution needed:
{rating_dist}

Guidelines:
- Each review should be authentic and conversational
- Match the star rating (1=terrible, 2=disappointing, 3=okay, 4=good, 5=excellent)
- Mention specific features, use cases, or experiences
- Vary the perspective (beginner, expert, casual user, etc.)
- Keep each review 2-3 sentences max
- Make them sound like real customers with different priorities

Return ONLY a JSON array of review texts in the same order as the ratings: {ratings}
Format: ["review 1 text", "review 2 text", ...]
No markdown, no code blocks, just the JSON array."""
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up markdown formatting if present
            if text.startswith("```"):
                lines = text.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```"):
                        if in_json:
                            break
                        in_json = True
                        continue
                    if in_json:
                        json_lines.append(line)
                text = "\n".join(json_lines)
            
            # Parse JSON response
            try:
                review_texts = json.loads(text)
                if isinstance(review_texts, list) and len(review_texts) == len(ratings):
                    # Clean up each review text
                    return [t.strip().strip('"').strip("'") for t in review_texts]
                else:
                    print(f"Warning: Got {len(review_texts)} reviews but expected {len(ratings)}, using fallback")
            except json.JSONDecodeError as je:
                print(f"Warning: Failed to parse JSON response ({je}), using fallback")
                
        except Exception as e:
            print(f"Warning: Batch AI generation failed ({e}), using fallback")
    
    # Fallback: generate simple reviews based on ratings
    fallback_reviews = []
    for rating in ratings:
        if rating >= 4:
            text = f"Great {product['title'].lower()}! Works exactly as expected. Very happy with this purchase."
        elif rating == 3:
            text = f"The {product['title'].lower()} is okay. It does what it's supposed to, but could be better quality."
        else:
            text = f"Disappointed with the {product['title'].lower()}. Had some issues and didn't meet expectations."
        fallback_reviews.append(text)
    
    return fallback_reviews


def generate_reviews_for_product(product: Dict, num_reviews: int, use_gemini: bool = True) -> List[Dict]:
    """Generate reviews for a single product."""
    reviews = []
    average_rating = product.get("average_rating", 4.0)
    
    # Generate ratings that average to the product's average_rating
    # Use normal distribution centered on average_rating
    ratings = []
    while len(ratings) < num_reviews:
        # Generate rating with normal distribution
        rating = round(random.normalvariate(average_rating, 0.8))
        rating = max(1, min(5, int(rating)))  # Clamp to 1-5
        ratings.append(rating)
    
    # Adjust to ensure average matches (approximately)
    current_avg = sum(ratings) / len(ratings)
    if abs(current_avg - average_rating) > 0.2:
        # Adjust some ratings to get closer to target
        diff = average_rating - current_avg
        for i in range(int(abs(diff) * len(ratings))):
            idx = random.randint(0, len(ratings) - 1)
            if diff > 0 and ratings[idx] < 5:
                ratings[idx] += 1
            elif diff < 0 and ratings[idx] > 1:
                ratings[idx] -= 1
    
    # Generate all review texts in a single batch API call
    review_texts = generate_reviews_batch(product, ratings, use_gemini)
    
    # Build review objects
    base_date = datetime.now() - timedelta(days=365)  # Reviews from last year
    
    for i, (rating, text) in enumerate(zip(ratings, review_texts)):
        review_date = base_date + timedelta(days=random.randint(0, 365))
        
        title = random.choice(REVIEW_TITLES[rating])
        user_name = random.choice(SAMPLE_USERS) + str(random.randint(1, 999))
        
        review = {
            "id": str(uuid.uuid4()),
            "product_id": product["id"],
            "user_id": user_name,
            "rating": rating,
            "title": title,
            "text": text,
            "timestamp": review_date.isoformat(),
            "verified_purchase": random.choice([True, True, True, False])  # 75% verified
        }
        reviews.append(review)
    
    return reviews


def main():
    parser = argparse.ArgumentParser(description="Generate product reviews")
    parser.add_argument(
        "--products",
        default="generated_products/products.json",
        help="Path to products.json file"
    )
    parser.add_argument(
        "--output",
        default="generated_products/reviews.json",
        help="Output path for reviews.json"
    )
    parser.add_argument(
        "--min-reviews",
        type=int,
        default=5,
        help="Minimum reviews per product"
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=30,
        help="Maximum reviews per product"
    )
    parser.add_argument(
        "--use-gemini",
        action="store_true",
        default=True,
        help="Use Gemini for review text generation"
    )
    args = parser.parse_args()
    
    # Load products
    products_path = Path(args.products)
    if not products_path.exists():
        print(f"Error: Products file not found: {products_path}")
        return
    
    with open(products_path, 'r') as f:
        products = json.load(f)
    
    print(f"Loaded {len(products)} products")
    print(f"Generating reviews (min: {args.min_reviews}, max: {args.max_reviews} per product)...")
    
    all_reviews = []
    
    for product in products:
        # Determine number of reviews for this product
        # Products with higher ratings get more reviews
        rating_factor = product.get("average_rating", 4.0) / 5.0
        num_reviews = int(args.min_reviews + (args.max_reviews - args.min_reviews) * rating_factor)
        num_reviews = max(args.min_reviews, min(args.max_reviews, num_reviews))
        
        reviews = generate_reviews_for_product(product, num_reviews, args.use_gemini)
        all_reviews.extend(reviews)
        
        print(f"  Generated {len(reviews)} reviews for {product['title']}")
    
    # Save reviews
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(all_reviews, f, indent=2)
    
    print(f"\nGenerated {len(all_reviews)} total reviews")
    print(f"Reviews saved to: {output_path}")


if __name__ == "__main__":
    main()

