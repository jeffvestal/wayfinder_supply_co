#!/usr/bin/env python3
"""
Upload product images to GCS and update product data with public URLs.

Usage:
    python scripts/upload_images_to_gcs.py
    
    # Or with custom paths:
    python scripts/upload_images_to_gcs.py --images-dir generated_products --products generated_products/products.json
"""

import os
import json
import argparse
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

try:
    from google.cloud import storage
except ImportError:
    print("ERROR: google-cloud-storage not installed. Run: pip install google-cloud-storage")
    exit(1)

# Configuration - read from env with defaults
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "wayfinder_supply_co")
GCS_PREFIX = os.getenv("GCS_PREFIX", "products/")
DEFAULT_IMAGES_DIR = "frontend/public/images/products"
DEFAULT_PRODUCTS_JSON = "generated_products/products.json"
SERVICE_ACCOUNT_KEY = os.path.expanduser(
    os.getenv("GCS_SERVICE_ACCOUNT_KEY", "~/wayfinder_supply_co_bucket_key.json")
)


def upload_images(images_dir: Path, bucket_name: str, gcs_prefix: str) -> dict:
    """
    Upload all images to GCS and return mapping of filename to public URL.
    
    Returns:
        dict: Mapping of filename to public URL
    """
    # Initialize client with service account
    if not os.path.exists(SERVICE_ACCOUNT_KEY):
        print(f"ERROR: Service account key not found at {SERVICE_ACCOUNT_KEY}")
        return {}
    
    client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_KEY)
    bucket = client.bucket(bucket_name)
    
    if not images_dir.exists():
        print(f"ERROR: Images directory not found: {images_dir}")
        return {}
    
    # Find all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif']
    image_files = []
    for ext in image_extensions:
        image_files.extend(images_dir.glob(ext))
    
    if not image_files:
        print(f"WARNING: No images found in {images_dir}")
        return {}
    
    print(f"Found {len(image_files)} images to upload")
    print(f"Uploading to gs://{bucket_name}/{gcs_prefix}")
    print("=" * 60)
    
    url_mapping = {}
    
    for image_file in sorted(image_files):
        blob_name = f"{gcs_prefix}{image_file.name}"
        blob = bucket.blob(blob_name)
        
        print(f"Uploading {image_file.name}...", end=" ")
        
        # Set content type based on extension
        content_type = "image/jpeg"
        if image_file.suffix.lower() == ".png":
            content_type = "image/png"
        elif image_file.suffix.lower() == ".webp":
            content_type = "image/webp"
        elif image_file.suffix.lower() == ".gif":
            content_type = "image/gif"
        
        blob.upload_from_filename(str(image_file), content_type=content_type)
        
        # Note: For uniform bucket-level access, set bucket to public instead of per-object ACLs
        # gsutil iam ch allUsers:objectViewer gs://wayfinder_supply_co
        
        public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
        url_mapping[image_file.name] = public_url
        print(f"✓")
    
    print("=" * 60)
    print(f"✓ Uploaded {len(url_mapping)} images")
    
    return url_mapping


def update_product_urls(products_path: Path, url_mapping: dict, bucket_name: str, gcs_prefix: str) -> int:
    """
    Update product JSON to use GCS URLs.
    
    Args:
        products_path: Path to products.json file
        url_mapping: Dict mapping filename to public URL
        bucket_name: GCS bucket name for fallback URL generation
        gcs_prefix: GCS prefix for fallback URL generation
    
    Returns:
        int: Number of products updated
    """
    if not products_path.exists():
        print(f"WARNING: Products file not found: {products_path}")
        return 0
    
    with open(products_path, 'r') as f:
        products = json.load(f)
    
    updated_count = 0
    
    for product in products:
        # Check both 'image' and 'image_url' fields
        image_field = 'image_url' if 'image_url' in product else 'image'
        
        if image_field in product and product[image_field]:
            # Extract filename from the path
            old_path = product[image_field]
            filename = Path(old_path).name
            
            if filename in url_mapping:
                product[image_field] = url_mapping[filename]
                updated_count += 1
            else:
                # Generate expected GCS URL even if we didn't upload
                product[image_field] = f"https://storage.googleapis.com/{bucket_name}/{gcs_prefix}{filename}"
                updated_count += 1
    
    with open(products_path, 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"✓ Updated {updated_count} products with GCS URLs in {products_path}")
    
    return updated_count


def main():
    parser = argparse.ArgumentParser(description="Upload product images to GCS")
    parser.add_argument(
        "--images-dir",
        default=DEFAULT_IMAGES_DIR,
        help=f"Directory containing images (default: {DEFAULT_IMAGES_DIR})"
    )
    parser.add_argument(
        "--products",
        default=DEFAULT_PRODUCTS_JSON,
        help=f"Path to products.json (default: {DEFAULT_PRODUCTS_JSON})"
    )
    parser.add_argument(
        "--bucket",
        default=BUCKET_NAME,
        help=f"GCS bucket name (default: {BUCKET_NAME})"
    )
    parser.add_argument(
        "--prefix",
        default=GCS_PREFIX,
        help=f"GCS prefix/folder (default: {GCS_PREFIX})"
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip upload, just update product URLs"
    )
    
    args = parser.parse_args()
    
    images_dir = Path(args.images_dir)
    products_path = Path(args.products)
    
    print("=" * 60)
    print("Wayfinder Supply Co. - Image Upload to GCS")
    print("=" * 60)
    print(f"Bucket: {args.bucket}")
    print(f"Prefix: {args.prefix}")
    print(f"Images: {images_dir}")
    print(f"Products: {products_path}")
    print("=" * 60)
    
    if args.skip_upload:
        print("Skipping upload, updating URLs only...")
        url_mapping = {}
    else:
        url_mapping = upload_images(images_dir, args.bucket, args.prefix)
    
    if products_path.exists():
        update_product_urls(products_path, url_mapping, args.bucket, args.prefix)
    
    print("\nDone!")
    print(f"Images available at: https://storage.googleapis.com/{args.bucket}/{args.prefix}")


if __name__ == "__main__":
    main()
