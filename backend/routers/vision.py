# backend/routers/vision.py
"""
Vision router for image analysis and preview generation.
Endpoints self-gate based on credential availability via CredentialManager.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.credential_manager import get_credential_manager
from services import vision_service
import logging

logger = logging.getLogger("wayfinder.vision")

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request body for image analysis."""
    image_base64: str
    prompt: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response from image analysis."""
    description: str
    success: bool = True


class PreviewRequest(BaseModel):
    """Request body for product-in-scene preview generation."""
    image_base64: str
    product_name: str
    scene_description: str
    product_description: Optional[str] = None
    product_image_url: Optional[str] = None


class PreviewResponse(BaseModel):
    """Response from preview generation."""
    image_base64: str
    prompt: str = ""
    success: bool = True


class GroundRequest(BaseModel):
    """Request body for real-time conditions grounding."""
    location: str
    activity: str


@router.post("/vision/warm")
async def warm_vision():
    """
    Send a lightweight ping to wake the Jina VLM model from cold sleep.
    Returns immediately with the model status: warm, warming, or unavailable.
    """
    status = await vision_service.warm_model()
    return {"status": status}


@router.post("/vision/analyze", response_model=AnalyzeResponse)
async def analyze_image(request: AnalyzeRequest):
    """
    Analyze an uploaded image for terrain, weather, and conditions.
    Requires Jina VLM API key to be configured.
    """
    cm = get_credential_manager()
    if not cm.is_vision_ready():
        raise HTTPException(
            status_code=503,
            detail="Vision analysis not configured. Add Jina API key in Settings.",
        )

    try:
        description = await vision_service.analyze_image(
            image_base64=request.image_base64,
            prompt=request.prompt,
        )
        return AnalyzeResponse(description=description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/vision/preview", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest):
    """
    Generate a product-in-scene preview image using Imagen 3.
    Requires Vertex AI credentials to be configured.
    """
    cm = get_credential_manager()
    if not cm.is_imagen_ready():
        raise HTTPException(
            status_code=503,
            detail="Image generation not configured. Add Vertex AI credentials in Settings.",
        )

    try:
        generated_image, prompt_used = await vision_service.generate_preview(
            original_image_base64=request.image_base64,
            product_name=request.product_name,
            scene_description=request.scene_description,
            product_description=request.product_description,
            product_image_url=request.product_image_url,
        )
        return PreviewResponse(image_base64=generated_image, prompt=prompt_used)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/vision/ground")
async def ground_conditions(request: GroundRequest):
    """
    Get real-time conditions for a location using Vertex AI grounding.
    Requires Vertex AI credentials to be configured.
    """
    cm = get_credential_manager()
    if not cm.is_grounding_ready():
        raise HTTPException(
            status_code=503,
            detail="Grounding not configured. Add Vertex AI credentials in Settings.",
        )

    try:
        conditions = await vision_service.ground_conditions(
            location=request.location,
            activity=request.activity,
        )
        return {"success": True, "conditions": conditions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Grounding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Grounding failed: {str(e)}")
