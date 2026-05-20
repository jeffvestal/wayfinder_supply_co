"""
Credential Manager - resolves API keys from UI settings (in-memory) or environment variables.

Priority order:
1. UI Settings page (stored in memory, resets on restart)
2. Environment variables (.env file or Docker env)

Never persists secrets to disk permanently. Never exposes actual key values via API.
"""

import json
import os
import logging
import tempfile
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("wayfinder.credentials")

# OAuth scopes required for Vertex AI (Gemini, Imagen, Grounding)
VERTEX_AI_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Mapping of service keys to their environment variable names
SERVICE_ENV_VARS = {
    "JINA_API_KEY": "JINA_API_KEY",
    "VERTEX_PROJECT_ID": "VERTEX_PROJECT_ID",
    "VERTEX_LOCATION": "VERTEX_LOCATION",
    "GOOGLE_APPLICATION_CREDENTIALS": "GOOGLE_APPLICATION_CREDENTIALS",
    "GCP_SERVICE_ACCOUNT_JSON": "GCP_SERVICE_ACCOUNT_JSON",
}

# Which keys each service requires
# Vertex/Imagen: either pasted JSON (auto-extracts project_id) or project_id + ADC
SERVICE_REQUIREMENTS = {
    "jina_vlm": ["JINA_API_KEY"],
    "vertex_ai": [],  # checked via _is_vertex_configured()
    "imagen": [],     # checked via _is_vertex_configured()
}


class CredentialManager:
    """Singleton credential manager with in-memory override support."""

    def __init__(self):
        self._overrides: Dict[str, str] = {}
        self._cached_credentials: Any = None  # Cached google credentials object
        self._cached_project: Optional[str] = None

    def get(self, key: str) -> Optional[str]:
        """Get a credential value. Checks in-memory overrides first, then environment."""
        if key in self._overrides:
            return self._overrides[key]
        env_var = SERVICE_ENV_VARS.get(key, key)
        return os.getenv(env_var)

    def set(self, key: str, value: str) -> None:
        """Store a credential in memory (runtime override). Does not persist to disk."""
        if key not in SERVICE_ENV_VARS:
            logger.warning(f"Unknown credential key: {key}")
            return
        self._overrides[key] = value
        # Invalidate cached credentials when GCP settings change
        if key in ("GCP_SERVICE_ACCOUNT_JSON", "GOOGLE_APPLICATION_CREDENTIALS", "VERTEX_PROJECT_ID"):
            self._cached_credentials = None
            self._cached_project = None
        logger.info(f"Credential '{key}' set via UI settings")

    def set_service_account_json(self, json_content: str) -> Optional[str]:
        """
        Store service account JSON and auto-extract project_id.
        Returns the extracted project_id, or None if JSON is invalid.
        """
        try:
            info = json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid service account JSON: {e}")
            return None

        # Validate it looks like a service account
        if info.get("type") != "service_account":
            logger.warning(f"JSON 'type' is '{info.get('type')}', expected 'service_account'")

        # Store the raw JSON
        self._overrides["GCP_SERVICE_ACCOUNT_JSON"] = json_content
        self._cached_credentials = None
        self._cached_project = None

        # Auto-extract and set project_id
        project_id = info.get("project_id")
        if project_id:
            self._overrides["VERTEX_PROJECT_ID"] = project_id
            logger.info(f"Auto-extracted project_id: {project_id}")

        logger.info("GCP service account JSON stored via UI settings")
        return project_id

    def clear(self, key: str) -> None:
        """Remove an in-memory override, falling back to environment."""
        self._overrides.pop(key, None)
        if key in ("GCP_SERVICE_ACCOUNT_JSON", "GOOGLE_APPLICATION_CREDENTIALS", "VERTEX_PROJECT_ID"):
            self._cached_credentials = None
            self._cached_project = None
        logger.info(f"Credential '{key}' cleared from UI settings")

    def _get_key_status(self, key: str) -> str:
        """Get status for a single credential key."""
        if key in self._overrides:
            return "configured_ui"
        env_var = SERVICE_ENV_VARS.get(key, key)
        if os.getenv(env_var):
            return "configured_env"
        return "not_configured"

    def _is_vertex_configured(self) -> bool:
        """Check if Vertex AI credentials are available via any path."""
        # Path A: Pasted service account JSON (includes project_id)
        if self.get("GCP_SERVICE_ACCOUNT_JSON"):
            return True
        # Path B: Project ID + ADC or file-based credentials
        if self.get("VERTEX_PROJECT_ID") and self.get("GOOGLE_APPLICATION_CREDENTIALS"):
            return True
        # Path C: Just project ID (user may have ADC configured on host)
        if self.get("VERTEX_PROJECT_ID"):
            return True
        return False

    def _vertex_status(self) -> str:
        """Get configuration status for Vertex AI."""
        json_status = self._get_key_status("GCP_SERVICE_ACCOUNT_JSON")
        if json_status != "not_configured":
            return json_status
        file_status = self._get_key_status("GOOGLE_APPLICATION_CREDENTIALS")
        pid_status = self._get_key_status("VERTEX_PROJECT_ID")
        if file_status != "not_configured" and pid_status != "not_configured":
            if "configured_ui" in (file_status, pid_status):
                return "configured_ui"
            return "configured_env"
        if pid_status != "not_configured":
            return pid_status
        return "not_configured"

    def _is_service_configured(self, service: str) -> bool:
        """Check if all required keys for a service are available."""
        if service in ("vertex_ai", "imagen"):
            return self._is_vertex_configured()
        required_keys = SERVICE_REQUIREMENTS.get(service, [])
        return all(self.get(key) for key in required_keys)

    def service_status(self, service: str) -> str:
        """Get configuration status for a service."""
        if service in ("vertex_ai", "imagen"):
            return self._vertex_status()
        required_keys = SERVICE_REQUIREMENTS.get(service, [])
        if not required_keys:
            return "not_configured"
        statuses = [self._get_key_status(key) for key in required_keys]
        if all(s != "not_configured" for s in statuses):
            if any(s == "configured_ui" for s in statuses):
                return "configured_ui"
            return "configured_env"
        return "not_configured"

    def status(self) -> Dict[str, str]:
        """Get configuration status for all services. Never returns actual key values."""
        result = {
            service: self.service_status(service)
            for service in SERVICE_REQUIREMENTS
        }
        # Include extracted project_id so frontend can display it
        project_id = self.get("VERTEX_PROJECT_ID")
        if project_id:
            result["vertex_project_id"] = project_id
        return result

    def get_vertex_credentials(self) -> Tuple[Any, str]:
        """
        Get properly-scoped credentials for Vertex AI.

        Returns (credentials, project_id) tuple.
        Uses service account JSON if available, otherwise falls back to ADC.
        Caches credentials in memory for reuse.
        """
        if self._cached_credentials and self._cached_project:
            return self._cached_credentials, self._cached_project

        project_id = self.get("VERTEX_PROJECT_ID")

        # Path A: Service account JSON pasted via UI
        sa_json = self.get("GCP_SERVICE_ACCOUNT_JSON")
        if sa_json:
            try:
                from google.oauth2 import service_account
                info = json.loads(sa_json)
                credentials = service_account.Credentials.from_service_account_info(
                    info, scopes=VERTEX_AI_SCOPES
                )
                resolved_project = project_id or info.get("project_id", "")
                self._cached_credentials = credentials
                self._cached_project = resolved_project
                logger.info(f"Vertex credentials from pasted JSON (project: {resolved_project})")
                return credentials, resolved_project
            except Exception as e:
                logger.error(f"Failed to create credentials from pasted JSON: {e}")
                raise ValueError(f"Invalid service account JSON: {e}")

        # Path B: File-based credentials (Docker volume or local file)
        creds_file = self.get("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_file and os.path.isfile(creds_file):
            try:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    creds_file, scopes=VERTEX_AI_SCOPES
                )
                resolved_project = project_id or ""
                self._cached_credentials = credentials
                self._cached_project = resolved_project
                logger.info(f"Vertex credentials from file (project: {resolved_project})")
                return credentials, resolved_project
            except Exception as e:
                logger.error(f"Failed to load credentials from file: {e}")
                raise ValueError(f"Invalid credentials file: {e}")

        # Path C: Application Default Credentials (gcloud auth, metadata server, etc.)
        if project_id:
            try:
                import google.auth
                credentials, discovered_project = google.auth.default(scopes=VERTEX_AI_SCOPES)
                resolved_project = project_id or discovered_project or ""
                self._cached_credentials = credentials
                self._cached_project = resolved_project
                logger.info(f"Vertex credentials from ADC (project: {resolved_project})")
                return credentials, resolved_project
            except Exception as e:
                logger.error(f"Failed to get ADC credentials: {e}")
                raise ValueError(f"No GCP credentials found: {e}")

        raise ValueError(
            "Vertex AI not configured. Paste your service account JSON in Settings, "
            "or set VERTEX_PROJECT_ID + GOOGLE_APPLICATION_CREDENTIALS in .env"
        )

    def ensure_gcp_credentials_file(self) -> Optional[str]:
        """
        Ensure GCP credentials are available as a file (for libraries that need a file path).
        Returns the file path, or None if not configured.
        """
        sa_json = self.get("GCP_SERVICE_ACCOUNT_JSON")
        if sa_json:
            try:
                json.loads(sa_json)  # validate
                tmp = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", prefix="gcp_sa_", delete=False
                )
                tmp.write(sa_json)
                tmp.close()
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
                logger.info(f"GCP SA JSON written to temp file: {tmp.name}")
                return tmp.name
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to write GCP credentials: {e}")
                return None
        return self.get("GOOGLE_APPLICATION_CREDENTIALS")

    def is_vision_ready(self) -> bool:
        """Check if minimum vision features are available (Jina VLM)."""
        return self._is_service_configured("jina_vlm")

    def is_imagen_ready(self) -> bool:
        """Check if image generation is available (Vertex AI)."""
        return self._is_service_configured("imagen")

    def is_grounding_ready(self) -> bool:
        """Check if Vertex AI grounding is available."""
        return self._is_service_configured("vertex_ai")


# Singleton instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get or create the singleton CredentialManager instance."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager
