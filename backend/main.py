from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from routers import chat, products, cart, reviews, orders, users, clickstream, reports
from middleware.logging import LoggingMiddleware
from services.error_handler import global_exception_handler, http_exception_handler
import os
import logging
import json
from pathlib import Path
from datetime import datetime

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

# Logging middleware
app.add_middleware(LoggingMiddleware)

# CORS middleware - allow all origins for workshop/Instruqt environments
# Instruqt URLs are dynamic: https://host-1-3000-{participant_id}.env.play.instruqt.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

# --- Static UI serving (Instruqt unified mode) ---
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# #region agent log
def _debug_log(payload: dict) -> None:
    """Write a single NDJSON debug line (best-effort)."""
    try:
        log_path = Path(".cursor") / "debug.log"
        payload.setdefault("timestamp", int(datetime.utcnow().timestamp() * 1000))
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# #endregion


@app.get("/")
async def root():
    # Prefer serving the built frontend when present (workshop/unified serving).
    if INDEX_HTML.exists():
        logger.info("Serving UI index.html from backend/static")
        # #region agent log
        _debug_log({
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": "A",
            "location": "backend/main.py:root",
            "message": "Serving UI index.html from backend/static",
            "data": {"indexExists": True, "indexPath": str(INDEX_HTML)},
        })
        # #endregion
        return FileResponse(INDEX_HTML)

    # #region agent log
    _debug_log({
        "sessionId": "debug-session",
        "runId": "pre-fix",
        "hypothesisId": "A",
        "location": "backend/main.py:root",
        "message": "Serving API JSON at / (index.html missing)",
        "data": {"indexExists": False, "staticDirExists": STATIC_DIR.exists()},
    })
    # #endregion
    return JSONResponse({"message": "Wayfinder Supply Co. Backend API", "status": "running"})


@app.get("/health")
async def health():
    return {"status": "healthy"}

# Mount static files AFTER API routes so /api/* keeps working.
# `html=True` enables SPA-style behavior for directory indexes (serves index.html).
if STATIC_DIR.exists():
    logger.info("Mounting StaticFiles at / (backend/static)")
    # #region agent log
    _debug_log({
        "sessionId": "debug-session",
        "runId": "pre-fix",
        "hypothesisId": "B",
        "location": "backend/main.py:mount",
        "message": "Mounting StaticFiles at /",
        "data": {"staticDir": str(STATIC_DIR), "indexExists": INDEX_HTML.exists()},
    })
    # #endregion
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    logger.warning("Not mounting StaticFiles (backend/static missing)")
    # #region agent log
    _debug_log({
        "sessionId": "debug-session",
        "runId": "pre-fix",
        "hypothesisId": "B",
        "location": "backend/main.py:mount",
        "message": "Not mounting StaticFiles (static dir missing)",
        "data": {"staticDir": str(STATIC_DIR)},
    })
    # #endregion


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

