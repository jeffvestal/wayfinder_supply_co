# backend/services/vision_service.py
"""
Vision service layer for Jina VLM and Vertex AI Grounding.
Each function is isolated so individual services can be swapped independently.
"""

import asyncio
import base64
import io
import json
import logging
import time
from typing import Optional, Dict, Any

import httpx

from services.credential_manager import get_credential_manager

logger = logging.getLogger("wayfinder.vision")

# Jina VLM endpoint (OpenAI-compatible)
JINA_VLM_URL = "https://api-beta-vlm.jina.ai/v1/chat/completions"

# Shared httpx client for Jina VLM — reuses TCP/TLS connections across requests
_jina_client: Optional[httpx.AsyncClient] = None


def _get_jina_client() -> httpx.AsyncClient:
    """Return a shared httpx.AsyncClient for Jina VLM (connection pooling)."""
    global _jina_client
    if _jina_client is None or _jina_client.is_closed:
        _jina_client = httpx.AsyncClient(timeout=120.0)
    return _jina_client

# Default terrain analysis prompt (used by Trip Planner)
DEFAULT_TERRAIN_PROMPT = (
    "Describe the terrain, weather conditions, elevation, and ground conditions "
    "in this image for outdoor activity planning. Be specific about what gear "
    "would be needed. Mention the likely location type (mountain, desert, forest, "
    "coastal, arctic, etc.), season, and any hazards visible. Be concise."
)

# Structured product analysis prompt — returns JSON for precise search
PRODUCT_STRUCTURED_PROMPT = (
    'Analyze this product image and return a JSON object with the following fields:\n'
    '- "product_type": The SPECIFIC product type (e.g., "hiking boots" not "boots")\n'
    '- "category": One of: Accessories, Apparel, Camping, Climbing, Cycling, '
    'Fishing, Hiking, Tropical & Safari, Water Sports, Winter Sports\n'
    '- "subcategory": A specific subcategory (e.g., "Hiking Boots", "Rain Jackets")\n'
    '- "key_terms": An array of 3-5 specific search terms that distinguish this product\n'
    '- "description": A concise description focusing on materials, style, colors, intended use\n'
    'Return ONLY valid JSON, no other text.'
)

# Max image payload size (4MB base64)
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024

# Minimal 1x1 red PNG for warm-up pings (44 bytes decoded)
_WARMUP_IMAGE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "nGP4z8BQDwAEgAF/pooBPQAAAABJRU5ErkJggg=="
)


async def warm_model() -> str:
    """
    Send a minimal request to Jina VLM to wake the model from cold sleep.
    Returns 'warm' if the model responded, 'warming' if the request timed out
    (model is booting), or 'unavailable' if not configured.
    """
    cm = get_credential_manager()
    api_key = cm.get("JINA_API_KEY")
    if not api_key:
        return "unavailable"

    payload = {
        "model": "jina-vlm",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hi"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{_WARMUP_IMAGE_B64}"
                        },
                    },
                ],
            }
        ],
        "max_tokens": 1,
    }

    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                JINA_VLM_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            elapsed = time.time() - t0
            if response.status_code == 200:
                logger.info(f"Jina VLM warm-up complete ({elapsed:.1f}s)")
                return "warm"
            logger.warning(f"Jina VLM warm-up returned {response.status_code} ({elapsed:.1f}s)")
            return "warming"
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        elapsed = time.time() - t0
        logger.info(f"Jina VLM warm-up timed out ({elapsed:.1f}s, {type(e).__name__}) — model is booting")
        return "warming"
    except Exception as e:
        logger.warning(f"Jina VLM warm-up failed: {e}")
        return "unavailable"


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

    # Retryable HTTP status codes (Jina cold start returns 503)
    RETRYABLE_STATUS_CODES = {502, 503, 429}
    max_attempts = 3
    last_error: Optional[Exception] = None
    t0_total = time.time()

    client = _get_jina_client()

    for attempt in range(1, max_attempts + 1):
        try:
            t0 = time.time()
            logger.info(f"Jina VLM attempt {attempt}/{max_attempts}")
            response = await client.post(
                JINA_VLM_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            elapsed = time.time() - t0

            if response.status_code in RETRYABLE_STATUS_CODES:
                logger.warning(
                    f"Jina VLM attempt {attempt} returned {response.status_code} "
                    f"after {elapsed:.1f}s "
                    f"({'retrying after delay...' if attempt < max_attempts else 'giving up'})"
                )
                last_error = ValueError(f"Jina VLM API error: {response.status_code}")
                if attempt < max_attempts:
                    delay = 15 * attempt
                    logger.info(f"Waiting {delay}s before retry (cold start backoff)...")
                    await asyncio.sleep(delay)
                    continue
                raise last_error

            if response.status_code != 200:
                logger.error(f"Jina VLM error: {response.status_code} after {elapsed:.1f}s - {response.text}")
                raise ValueError(f"Jina VLM API error: {response.status_code}")

            data = response.json()
            description = data["choices"][0]["message"]["content"]
            total_elapsed = time.time() - t0_total
            logger.info(f"Jina VLM analysis complete ({len(description)} chars, {elapsed:.1f}s request, {total_elapsed:.1f}s total)")
            return description

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            elapsed = time.time() - t0 if 't0' in dir() else 0
            last_error = e
            logger.warning(f"Jina VLM attempt {attempt} failed ({type(e).__name__}) after {elapsed:.1f}s, {'retrying...' if attempt < max_attempts else 'giving up'}")
            if attempt < max_attempts:
                await asyncio.sleep(5)
                continue
        except Exception:
            raise

    raise last_error or ValueError("Jina VLM failed after retries")


async def analyze_image_structured(image_base64: str) -> Dict[str, Any]:
    """
    Analyze a product image and return structured JSON for precise search.

    Calls Jina VLM with a structured prompt that requests JSON output including
    product_type, category, subcategory, key_terms, and description.

    Args:
        image_base64: Base64-encoded image (with or without data URI prefix)

    Returns:
        Dict with product_type, category, subcategory, key_terms, description.
        Falls back to {"description": raw_text} if JSON parsing fails.
    """
    raw = await analyze_image(image_base64, prompt=PRODUCT_STRUCTURED_PROMPT)

    # Strip markdown code fences if Jina wraps the JSON in ```json ... ```
    text = raw.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline + 1:]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
        # Ensure expected keys exist with sensible defaults
        return {
            "product_type": data.get("product_type", ""),
            "category": data.get("category", ""),
            "subcategory": data.get("subcategory", ""),
            "key_terms": data.get("key_terms", []),
            "description": data.get("description", ""),
        }
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse structured VLM response as JSON, using raw text. Response: {text[:200]}")
        return {"description": raw, "product_type": "", "category": "", "subcategory": "", "key_terms": []}


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
