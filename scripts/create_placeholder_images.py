#!/usr/bin/env python3
"""
Create placeholder product images using PIL/Pillow.
"""

from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path
import os

def create_placeholder_image(product_id: str, title: str, output_path: Path):
    """Create a simple placeholder image for a product."""
    # Create image
    img = Image.new('RGB', (400, 400), color='#374151')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([10, 10, 390, 390], outline='#16a34a', width=3)
    
    # Draw text (simple, centered)
    try:
        # Try to use a nicer font
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
    
    # Split title into lines if too long
    words = title.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] < 350:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw lines centered
    y_start = 200 - (len(lines) * 30) // 2
    for i, line in enumerate(lines[:3]):  # Max 3 lines
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (400 - text_width) // 2
        y = y_start + (i * 30)
        draw.text((x, y), line, fill='#ffffff', font=font)
    
    # Save
    img.save(output_path, 'JPEG', quality=85)
    print(f"Created placeholder: {output_path.name}")


def main():
    products_file = Path("generated_products/products.json")
    images_dir = Path("frontend/public/images/products")
    images_dir.mkdir(parents=True, exist_ok=True)
    
    if not products_file.exists():
        print(f"Products file not found: {products_file}")
        print("Run 'python scripts/generate_sample_data.py' first")
        return
    
    with open(products_file, 'r') as f:
        products = json.load(f)
    
    print(f"Creating placeholder images for {len(products)} products...")
    
    for product in products:
        image_path = images_dir / f"{product['id']}.jpg"
        if not image_path.exists():
            create_placeholder_image(
                product['id'],
                product['title'],
                image_path
            )
    
    print(f"✓ Created {len(products)} placeholder images")


if __name__ == "__main__":
    main()


