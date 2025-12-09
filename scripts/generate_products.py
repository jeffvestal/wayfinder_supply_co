#!/usr/bin/env python3
"""
Product generation script for Wayfinder Supply Co.
Generates product metadata using AI and creates product images.
"""

import json
import yaml
import os
import random
import uuid
import warnings
from pathlib import Path
from typing import List, Dict
import argparse

# Suppress Vertex AI deprecation warnings (deprecated until June 2026)
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
except ImportError:
    pass  # python-dotenv not installed, skip

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not available. Install with: pip install google-generativeai")

try:
    import vertexai
    from vertexai.preview.vision_models import ImageGenerationModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    print("Warning: Vertex AI not available. Install with: pip install google-cloud-aiplatform")


def load_config(config_path: str) -> Dict:
    """Load product generation configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def select_brand(brands: List[Dict]) -> str:
    """Select a brand based on weights."""
    total_weight = sum(b["weight"] for b in brands)
    r = random.uniform(0, total_weight)
    cumulative = 0
    for brand in brands:
        cumulative += brand["weight"]
        if r <= cumulative:
            return brand["name"]
    return brands[0]["name"]


def select_tags(tag_config: Dict, num_tags: int = 2) -> List[str]:
    """Select tags based on weights."""
    tags = []
    tag_names = list(tag_config.keys())
    weights = [tag_config[t]["weight"] for t in tag_names]
    
    for _ in range(num_tags):
        tag = random.choices(tag_names, weights=weights)[0]
        if tag not in tags:
            tags.append(tag)
    
    return tags


def calculate_price(base_price: float, tags: List[str], tag_config: Dict) -> float:
    """Calculate final price with tag modifiers."""
    price = base_price
    for tag in tags:
        if tag in tag_config:
            price *= tag_config[tag]["price_modifier"]
    return round(price, 2)


def generate_product_metadata(
    category: str,
    subcategory: str,
    brand: str,
    price_range: Dict,
    tag_config: Dict,
    seasons: List[str],
    use_gemini: bool = True
) -> Dict:
    """Generate product metadata using AI."""
    
    base_price = random.uniform(price_range["min"], price_range["max"])
    tags = select_tags(tag_config)
    price = calculate_price(base_price, tags, tag_config)
    season = random.choice(seasons)
    
    # Generate attributes based on category
    attributes = {}
    if category == "camping":
        if subcategory == "tents":
            attributes = {
                "capacity": random.choice([2, 4, 6, 8]),
                "weight_lb": round(random.uniform(3.0, 12.0), 1),
                "season": season
            }
        elif subcategory == "sleeping_bags":
            temp_rating = random.choice([0, 15, 20, 30, 40])
            attributes = {
                "temp_rating_f": temp_rating,
                "weight_lb": round(random.uniform(1.5, 5.0), 1),
                "season": season
            }
        elif subcategory == "cooking":
            attributes = {
                "weight_lb": round(random.uniform(0.5, 3.0), 1),
                "fuel_type": random.choice(["canister", "liquid", "wood"])
            }
    elif category == "hiking":
        if subcategory == "backpacks":
            attributes = {
                "capacity_l": random.choice([25, 35, 45, 55, 65]),
                "weight_lb": round(random.uniform(2.0, 5.0), 1)
            }
        elif subcategory == "footwear":
            attributes = {
                "weight_lb": round(random.uniform(1.0, 3.0), 1),
                "waterproof": random.choice([True, False])
            }
    elif category == "skiing":
        if subcategory == "skis":
            attributes = {
                "length_cm": random.choice([150, 160, 170, 180]),
                "width_mm": random.choice([80, 90, 100, 110])
            }
        elif subcategory == "outerwear":
            attributes = {
                "temp_rating_f": random.choice([-10, 0, 10, 20]),
                "waterproof": True
            }
    
    # Generate title and description
    if use_gemini and GEMINI_AVAILABLE:
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""Generate a product name and description for a {subcategory} in the {category} category.
Brand: {brand}
Tags: {', '.join(tags)}
Price: ${price}
Attributes: {json.dumps(attributes)}

Return JSON with:
- title: Product name (include brand name)
- description: 2-3 sentence product description highlighting key features

JSON only, no markdown."""
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            ai_data = json.loads(text)
            title = ai_data.get("title", f"{brand} {subcategory.replace('_', ' ').title()}")
            description = ai_data.get("description", f"High-quality {subcategory.replace('_', ' ')} from {brand}.")
        except Exception as e:
            print(f"Warning: AI generation failed ({e}), using fallback")
            title = f"{brand} {subcategory.replace('_', ' ').title()}"
            description = f"High-quality {subcategory.replace('_', ' ')} from {brand}. Perfect for {category} enthusiasts."
    else:
        # Fallback generation
        title = f"{brand} {subcategory.replace('_', ' ').title()}"
        description = f"High-quality {subcategory.replace('_', ' ')} from {brand}. Perfect for {category} enthusiasts."
    
    product_id = f"WF-{category[:3].upper()}-{subcategory[:3].upper()}-{str(uuid.uuid4())[:8].upper()}"
    
    # Generate ratings (weighted toward 3.5-4.9, with most products being 4.0-4.5)
    # Use beta distribution to skew toward higher ratings
    rating_base = random.betavariate(8, 2)  # Skews toward 0.8 (4.0 stars)
    average_rating = round(3.5 + (rating_base * 1.4), 1)  # Range: 3.5-4.9
    
    # Generate review count (5-50, weighted toward lower end)
    review_count = random.choices(
        range(5, 51),
        weights=[10-i for i in range(46)]  # More weight on lower numbers
    )[0]
    
    return {
        "id": product_id,
        "title": title,
        "brand": brand,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "price": price,
        "tags": tags,
        "attributes": attributes,
        "image_url": f"/images/products/{product_id}.jpg",
        "average_rating": average_rating,
        "review_count": review_count
    }


def generate_product_image(
    product: Dict,
    output_path: Path,
    use_vertex: bool = True
) -> bool:
    """Generate product image using AI."""
    if use_vertex and VERTEX_AVAILABLE:
        try:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            
            if not project_id:
                print(f"Skipping image generation for {product['id']}: GOOGLE_CLOUD_PROJECT not set")
                return False
            
            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)
            
            # Use regular Imagen 3 model (not fast)
            model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
            
            prompt = f"""Studio photography of a {product['title']}, {product['description']}, 
white background, soft lighting, 4k, product shot, no text, professional outdoor gear photography"""
            
            images = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                negative_prompt="",
                person_generation="allow_all",
                safety_filter_level="block_few",
                add_watermark=True
            )
            
            # Save image (images is a list, get first one)
            image = images[0]
            with open(output_path, 'wb') as f:
                f.write(image._image_bytes)
            
            print(f"  ✓ Generated image: {output_path.name}")
            return True
        except Exception as e:
            print(f"Warning: Vertex AI image generation failed ({e})")
            return False
    else:
        print(f"Skipping image generation for {product['id']}: Vertex AI not configured")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate products for Wayfinder Supply Co.")
    parser.add_argument(
        "--config",
        default="config/product_generation.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image generation"
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Only generate metadata, skip image generation (same as --skip-images)"
    )
    parser.add_argument(
        "--use-gemini",
        action="store_true",
        default=True,
        help="Use Gemini for metadata generation"
    )
    args = parser.parse_args()
    
    # --metadata-only implies --skip-images
    if args.metadata_only:
        args.skip_images = True
    
    # Load config
    config = load_config(args.config)
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = Path("frontend/public/images/products")
    images_dir.mkdir(parents=True, exist_ok=True)
    
    products = []
    
    # Generate products for each category/subcategory
    for category_config in config["categories"]:
        category = category_config["name"]
        price_range = config["price_ranges"][category]
        
        for subcat_config in category_config["subcategories"]:
            subcategory = subcat_config["name"]
            count = subcat_config["count"]
            
            print(f"Generating {count} {category}/{subcategory} products...")
            
            for i in range(count):
                brand = select_brand(config["brands"])
                product = generate_product_metadata(
                    category=category,
                    subcategory=subcategory,
                    brand=brand,
                    price_range=price_range,
                    tag_config=config["tags"],
                    seasons=config["seasons"],
                    use_gemini=args.use_gemini
                )
                
                # Generate image (skip if --skip-images or --metadata-only)
                if not args.skip_images and not args.metadata_only:
                    image_path = images_dir / f"{product['id']}.jpg"
                    generate_product_image(product, image_path, use_vertex=(config["image_provider"] == "vertex_ai"))
                
                products.append(product)
                print(f"  Generated: {product['title']}")
    
    # Save products JSON
    products_file = output_dir / "products.json"
    with open(products_file, 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"\nGenerated {len(products)} products")
    print(f"Products saved to: {products_file}")
    print(f"Images saved to: {images_dir}")


if __name__ == "__main__":
    main()

