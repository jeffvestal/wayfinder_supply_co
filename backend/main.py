# Load environment variables FIRST, before any other imports that use os.getenv()
import os
from pathlib import Path
from dotenv import load_dotenv

# Only load .env in standalone/local mode, NOT in Instruqt
# Instruqt sets INSTRUQT=true environment variable
if not os.getenv("INSTRUQT"):
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

# Now import everything else (routers will see the loaded env vars)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from routers import chat, products, cart, reviews, orders, users, clickstream, reports, workshop, settings, vision
from middleware.logging import LoggingMiddleware
from middleware.auth import ApiKeyMiddleware
from services.error_handler import global_exception_handler, http_exception_handler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wayfinder.backend")

app = FastAPI(
    title="Wayfinder Supply Co. Backend API",
    version="1.0.0",
    description="Backend API for Wayfinder Supply Co. workshop"
)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# API key authentication middleware (skipped when WAYFINDER_API_KEY is unset)
app.add_middleware(ApiKeyMiddleware)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# CORS middleware - allow all origins for workshop/Instruqt environments
# Instruqt URLs are dynamic: https://host-1-3000-{participant_id}.env.play.instruqt.com
# Note: allow_credentials=True is removed because Instruqt proxy often adds its own,
# leading to "true,true" which causes browser errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(cart.router, prefix="/api", tags=["cart"])
app.include_router(reviews.router, prefix="/api", tags=["reviews"])
app.include_router(orders.router, prefix="/api", tags=["orders"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(clickstream.router, prefix="/api", tags=["clickstream"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(workshop.router, prefix="/api", tags=["workshop"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(vision.router, prefix="/api", tags=["vision"])

# --- Static UI serving (Instruqt unified mode) ---
# In Cloud Run / standalone deployments the frontend is a separate service,
# so static serving should be disabled via DISABLE_STATIC_SERVING=true.
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"
STATIC_SERVING_DISABLED = os.getenv("DISABLE_STATIC_SERVING", "").lower() in ("true", "1", "yes")

logger.info(f"Checking for static files in: {STATIC_DIR}")
logger.info(f"index.html exists: {INDEX_HTML.exists()}")
if STATIC_SERVING_DISABLED:
    logger.info("Static file serving disabled (DISABLE_STATIC_SERVING is set)")

@app.get("/")
async def root():
    # Prefer serving the built frontend when present (workshop/unified serving).
    if INDEX_HTML.exists() and not STATIC_SERVING_DISABLED:
        logger.info(f"Serving UI index.html from {INDEX_HTML}")
        return FileResponse(INDEX_HTML)

    return JSONResponse({"message": "Wayfinder Supply Co. Backend API", "status": "running"})


@app.get("/health")
async def health():
    return {"status": "healthy"}

# Mount static files AFTER API routes so /api/* keeps working.
# `html=True` enables SPA-style behavior for directory indexes (serves index.html).
if STATIC_DIR.exists() and not STATIC_SERVING_DISABLED:
    logger.info("Mounting StaticFiles at / (backend/static)")
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    logger.info("Not mounting StaticFiles (missing or disabled)")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

