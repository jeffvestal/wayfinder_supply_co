# backend/routers/settings.py
"""
Settings router for managing API credentials at runtime.
Provides status checks and in-memory credential storage.
Never exposes actual key values.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from services.credential_manager import get_credential_manager
import logging
import httpx

logger = logging.getLogger("wayfinder.settings")

router = APIRouter()


class SettingsUpdate(BaseModel):
    """Request body for updating settings. Only known keys are accepted."""
    JINA_API_KEY: Optional[str] = None
    VERTEX_PROJECT_ID: Optional[str] = None
    VERTEX_LOCATION: Optional[str] = None
    GCP_SERVICE_ACCOUNT_JSON: Optional[str] = None


class SettingsStatusResponse(BaseModel):
    """Response showing configuration status per service."""
    jina_vlm: str
    vertex_ai: str
    imagen: str
    vertex_project_id: Optional[str] = None  # Extracted/configured project ID


@router.get("/settings/status")
async def get_settings_status():
    """
    Get configuration status for all vision services.
    Returns whether each service is configured (via UI, env, or not at all).
    Never returns actual credential values (only project ID is shown).
    """
    cm = get_credential_manager()
    return cm.status()


@router.post("/settings")
async def update_settings(settings: SettingsUpdate):
    """
    Update API credentials at runtime (stored in memory only).
    Credentials are cleared on backend restart.
    """
    cm = get_credential_manager()

    updates = settings.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No settings provided")

    for key, value in updates.items():
        value_stripped = value.strip()
        if not value_stripped:
            cm.clear(key)
            continue

        # Special handling for service account JSON: parse and auto-extract project_id
        if key == "GCP_SERVICE_ACCOUNT_JSON":
            project_id = cm.set_service_account_json(value_stripped)
            if project_id:
                logger.info(f"Auto-extracted project_id from SA JSON: {project_id}")
            else:
                logger.warning("Could not extract project_id from SA JSON")
        else:
            cm.set(key, value_stripped)

    logger.info(f"Settings updated: {list(updates.keys())}")
    return cm.status()


@router.post("/settings/test/jina")
async def test_jina_connection():
    """Test the Jina VLM API connection with current credentials."""
    cm = get_credential_manager()
    api_key = cm.get("JINA_API_KEY")

    if not api_key:
        return {"success": False, "message": "Jina API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api-beta-vlm.jina.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if response.status_code == 200:
                return {"success": True, "message": "Jina VLM API connected successfully"}
            elif response.status_code == 401:
                return {"success": False, "message": "Invalid Jina API key"}
            else:
                return {
                    "success": False,
                    "message": f"Jina API returned status {response.status_code}",
                }
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}


@router.post("/settings/test/vertex")
async def test_vertex_connection():
    """
    Test the Vertex AI connection with current credentials.
    Uses get_vertex_credentials() which handles all auth paths with proper scopes.
    """
    cm = get_credential_manager()

    try:
        credentials, project_id = cm.get_vertex_credentials()
    except ValueError as e:
        return {"success": False, "message": str(e)}

    try:
        from google.auth.transport.requests import Request
        credentials.refresh(Request())
        return {
            "success": True,
            "message": f"Vertex AI connected (project: {project_id})",
        }
    except ImportError:
        return {
            "success": False,
            "message": "google-cloud-aiplatform not installed. Run: pip install google-cloud-aiplatform",
        }
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}
