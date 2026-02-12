# backend/services/vision_service.py
"""
Vision service layer for Jina VLM, Vertex AI Grounding, and Imagen 3.
Each function is isolated so individual services can be swapped independently.
"""

import base64
import io
import json
import logging
from typing import Optional, Dict, Any

import httpx

from services.credential_manager import get_credential_manager

logger = logging.getLogger("wayfinder.vision")

# Jina VLM endpoint (OpenAI-compatible)
JINA_VLM_URL = "https://api-beta-vlm.jina.ai/v1/chat/completions"

# Default terrain analysis prompt
DEFAULT_TERRAIN_PROMPT = (
    "Describe the terrain, weather conditions, elevation, and ground conditions "
    "in this image for outdoor activity planning. Be specific about what gear "
    "would be needed. Mention the likely location type (mountain, desert, forest, "
    "coastal, arctic, etc.), season, and any hazards visible. Be concise."
)

# Max image payload size (4MB base64)
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024


def _validate_image(image_base64: str) -> str:
    """Validate and clean base64 image data. Returns clean base64 string."""
    # Strip data URI prefix if present
    if image_base64.startswith("data:"):
        # Extract base64 part after comma
        _, image_base64 = image_base64.split(",", 1)

    # Check size
    decoded_size = len(image_base64) * 3 / 4  # Approximate decoded size
    if decoded_size > MAX_IMAGE_SIZE_BYTES:
        raise ValueError(
            f"Image too large ({decoded_size / 1024 / 1024:.1f}MB). "
            f"Maximum is {MAX_IMAGE_SIZE_BYTES / 1024 / 1024:.0f}MB."
        )

    return image_base64


async def analyze_image(image_base64: str, prompt: Optional[str] = None) -> str:
    """
    Analyze an image using Jina VLM for terrain/conditions description.

    Args:
        image_base64: Base64-encoded image (with or without data URI prefix)
        prompt: Optional custom prompt (defaults to terrain analysis)

    Returns:
        Text description of the terrain and conditions
    """
    cm = get_credential_manager()
    api_key = cm.get("JINA_API_KEY")
    if not api_key:
        raise ValueError("Jina API key not configured")

    clean_b64 = _validate_image(image_base64)
    analysis_prompt = prompt or DEFAULT_TERRAIN_PROMPT

    # Build OpenAI-compatible request with image
    payload = {
        "model": "jina-vlm",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{clean_b64}"
                        },
                    },
                ],
            }
        ],
        "max_tokens": 500,
    }

    max_attempts = 2
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"Jina VLM attempt {attempt}/{max_attempts}")
                response = await client.post(
                    JINA_VLM_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(f"Jina VLM error: {response.status_code} - {response.text}")
                    raise ValueError(f"Jina VLM API error: {response.status_code}")

                data = response.json()
                description = data["choices"][0]["message"]["content"]
                logger.info(f"Jina VLM analysis complete ({len(description)} chars)")
                return description

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e
            logger.warning(f"Jina VLM attempt {attempt} failed ({type(e).__name__}), {'retrying...' if attempt < max_attempts else 'giving up'}")
            if attempt < max_attempts:
                continue
        except Exception:
            raise  # Don't retry non-transient errors

    raise last_error or ValueError("Jina VLM failed after retries")


async def ground_conditions(location: str, activity: str) -> Dict[str, Any]:
    """
    Validate real-time conditions for a location using Vertex AI Gemini with Google Search grounding.

    Uses the google-genai SDK with the googleSearch tool (the older google_search_retrieval
    approach was deprecated and returns 400 errors as of early 2026).

    Args:
        location: The destination location
        activity: The planned activity

    Returns:
        Dict with weather, conditions, and safety information
    """
    cm = get_credential_manager()
    credentials, project_id = cm.get_vertex_credentials()
    region = cm.get("VERTEX_LOCATION") or "us-central1"

    try:
        from google import genai
        from google.genai.types import (
            GenerateContentConfig,
            GoogleSearch,
            HttpOptions,
            Tool,
        )

        # Initialize client with Vertex AI backend and explicit credentials
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=region,
            credentials=credentials,
            http_options=HttpOptions(api_version="v1"),
        )

        prompt = (
            f"What are the current weather and trail conditions for {activity} "
            f"at {location}? Include: temperature, precipitation, wind, trail status, "
            f"and any safety advisories. Return as JSON with keys: "
            f"temperature_f, conditions, wind_mph, trail_status, safety_notes."
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
            ),
        )

        # Try to parse as JSON, fall back to text
        text = response.text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "conditions_text": text,
                "location": location,
                "activity": activity,
            }

    except ImportError:
        raise ValueError(
            "google-genai not installed. Run: pip install google-genai"
        )


async def generate_preview(
    original_image_base64: str,
    product_name: str,
    scene_description: str,
    product_description: Optional[str] = None,
    product_image_url: Optional[str] = None,
) -> tuple[str, str]:
    """
    Generate a preview image of a product in scene using a two-pass Imagen 3 pipeline.

    Pass 1 (Scene Generation): Uses text-to-image to create a realistic, human-scale
    outdoor scene from the Jina VLM description — no product yet.

    Pass 2 (Product Insertion): Uses edit_image inpainting to insert the product into
    the generated scene. If a product_image_url is provided, it is passed as a
    StyleReferenceImage to guide the visual appearance. If product_description is
    provided, it enriches the insertion prompt with specific visual attributes.

    Falls back gracefully:
      - If style ref + inpainting fails → retry inpainting without style ref
      - If inpainting fails entirely → single-pass text-to-image with product in prompt

    Args:
        original_image_base64: Base64-encoded original scene image (user's photo)
        product_name: Name of the product to place in scene
        scene_description: Description of the scene (from Jina VLM)
        product_description: Optional full product description from catalog
        product_image_url: Optional URL to product catalog image (for style reference)

    Returns:
        Tuple of (base64-encoded generated image, combined prompt description)
    """
    cm = get_credential_manager()
    credentials, project_id = cm.get_vertex_credentials()
    region = cm.get("VERTEX_LOCATION") or "us-central1"

    try:
        from google import genai
        from google.genai.types import (
            EditImageConfig,
            GenerateImagesConfig,
            HttpOptions,
            Image,
            StyleReferenceConfig,
            StyleReferenceImage,
        )

        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=region,
            credentials=credentials,
            http_options=HttpOptions(api_version="v1"),
        )

        # ── Pass 1: Generate a realistic scene background ──────────────
        scene_prompt = (
            f"A photorealistic outdoor scene: {scene_description}. "
            f"Show a natural campsite or trail setting at ground level with "
            f"realistic human-scale perspective. Leave clear space in the "
            f"foreground for gear placement. "
            f"Professional outdoor photography, 16:9 aspect ratio."
        )

        logger.info("Imagen 3 Pass 1: generating scene background")
        scene_result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=scene_prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                person_generation="ALLOW_ADULT",
            ),
        )

        if not scene_result.generated_images:
            raise ValueError("Imagen 3 Pass 1 returned no images for scene generation")

        scene_image = scene_result.generated_images[0].image
        logger.info("Imagen 3 Pass 1: scene background generated successfully")

        # ── Generate final image: scene + product in a single prompt ──
        # Note: Inpainting (MASK_MODE_FOREGROUND) does not work on AI-generated
        # landscapes because there is no existing foreground object to detect.
        # Instead, we generate a single composite image that includes both the
        # scene and the product in the prompt for reliable, high-quality results.

        # Detect wearable products (jackets, boots, gloves, etc.) to prompt differently
        name_lower = product_name.lower()
        desc_lower = (product_description or '').lower()
        wearable_keywords = ['jacket', 'coat', 'vest', 'shirt', 'pants', 'shorts',
                             'boot', 'shoe', 'glove', 'hat', 'beanie', 'gaiter',
                             'sock', 'layer', 'fleece', 'hoodie', 'parka', 'shell']
        is_wearable = any(kw in name_lower or kw in desc_lower for kw in wearable_keywords)

        if is_wearable:
            # Wearable items look better worn by a person in context
            product_detail = product_description if product_description else product_name
            composite_prompt = (
                f"A photorealistic outdoor photograph: {scene_description}. "
                f"A hiker wearing {product_detail}. "
                f"The person is shown from mid-thigh up, facing the camera on a trail, "
                f"with the landscape visible behind them. "
                f"Natural lighting, professional outdoor photography, 16:9 aspect ratio."
            )
        elif product_description:
            composite_prompt = (
                f"A photorealistic outdoor photograph: {scene_description}. "
                f"In the foreground at ground level, prominently feature: {product_description}. "
                f"The product is set up and ready to use at a natural campsite. "
                f"Realistic scale, natural lighting, professional outdoor photography, 16:9 aspect ratio."
            )
        else:
            composite_prompt = (
                f"A photorealistic outdoor photograph: {scene_description}. "
                f"In the foreground at ground level, prominently feature a {product_name} "
                f"set up and ready to use at a natural campsite. "
                f"Realistic scale, natural lighting, professional outdoor photography, 16:9 aspect ratio."
            )

        combined_prompt = (
            f"[Scene context] {scene_prompt}\n"
            f"[Product + Scene] {composite_prompt}"
        )

        # Optionally fetch product catalog image for style reference
        style_ref = None
        if product_image_url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    img_resp = await http_client.get(product_image_url)
                    if img_resp.status_code == 200:
                        style_ref = StyleReferenceImage(
                            reference_id=0,
                            reference_image=Image(image_bytes=img_resp.content),
                            config=StyleReferenceConfig(
                                style_description=f"The visual appearance, color, and design of {product_name}",
                            ),
                        )
                        logger.info(f"Imagen 3: fetched product style image ({len(img_resp.content)} bytes)")
                    else:
                        logger.warning(f"Imagen 3: failed to fetch product image (HTTP {img_resp.status_code})")
            except Exception as fetch_err:
                logger.warning(f"Imagen 3: could not fetch product image ({fetch_err})")

        # Attempt 1: Generate with style reference (product catalog image)
        if style_ref:
            try:
                logger.info("Imagen 3: generating composite image with style reference")
                style_result = client.models.edit_image(
                    model="imagen-3.0-capability-001",
                    prompt=composite_prompt,
                    reference_images=[style_ref],
                    config=EditImageConfig(
                        edit_mode="EDIT_MODE_DEFAULT",
                        number_of_images=1,
                        safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                        person_generation="ALLOW_ADULT",
                    ),
                )
                if style_result.generated_images:
                    image_bytes = style_result.generated_images[0].image.image_bytes
                    logger.info("Imagen 3: composite with style ref succeeded")
                    combined_prompt += "\n[Style Reference] Product catalog image used"
                    return base64.b64encode(image_bytes).decode("utf-8"), combined_prompt
                else:
                    logger.warning("Imagen 3: style ref returned no images, trying without")
            except Exception as style_err:
                logger.warning(f"Imagen 3: style ref failed ({style_err}), trying without")

        # Attempt 2: Generate without style reference (enhanced prompt only)
        logger.info("Imagen 3: generating composite image (text-to-image)")
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=composite_prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                person_generation="ALLOW_ADULT",
            ),
        )

        if result.generated_images:
            image_bytes = result.generated_images[0].image.image_bytes
            logger.info("Imagen 3: composite text-to-image succeeded")
            return base64.b64encode(image_bytes).decode("utf-8"), combined_prompt
        else:
            raise ValueError("Imagen 3 returned no images")

    except ImportError:
        raise ValueError(
            "google-genai not installed. Run: pip install google-genai"
        )
