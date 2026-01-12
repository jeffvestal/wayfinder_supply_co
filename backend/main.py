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
from routers import chat, products, cart, reviews, orders, users, clickstream, reports, workshop
from middleware.logging import LoggingMiddleware
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
app.include_router(workshop.router, prefix="/api", tags=["workshop"])

# --- Static UI serving (Instruqt unified mode) ---
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# #region agent log
try:
    import json;open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"backend/main.py:69","message":"App startup - checking static dir","data":{"static_dir_exists":STATIC_DIR.exists(),"static_dir_path":str(STATIC_DIR),"index_html_exists":INDEX_HTML.exists(),"index_html_path":str(INDEX_HTML)},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"initial","hypothesisId":"A,B"})+'\n');
except Exception: pass
# #endregion


@app.get("/")
async def root():
    # #region agent log
    try:
        import json;open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"backend/main.py:77","message":"Root route hit - checking index.html","data":{"index_html_exists":INDEX_HTML.exists(),"index_html_path":str(INDEX_HTML),"static_dir_exists":STATIC_DIR.exists()},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"initial","hypothesisId":"A,B,D"})+'\n');
    except Exception: pass
    # #endregion
    
    # Prefer serving the built frontend when present (workshop/unified serving).
    if INDEX_HTML.exists():
        logger.info("Serving UI index.html from backend/static")
        # #region agent log
        try:
            import json;open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"backend/main.py:82","message":"Returning FileResponse for index.html","data":{"file_path":str(INDEX_HTML)},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"initial","hypothesisId":"B,E"})+'\n');
        except Exception: pass
        # #endregion
        return FileResponse(INDEX_HTML)

    # #region agent log
    try:
        import json;open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"backend/main.py:87","message":"Index.html NOT found - returning JSON","data":{"index_html_path":str(INDEX_HTML)},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"initial","hypothesisId":"A,B"})+'\n');
    except Exception: pass
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
    try:
        import json;open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"backend/main.py:95","message":"Mounting StaticFiles","data":{"static_dir":str(STATIC_DIR),"static_dir_exists":True,"route_mount_path":"/"},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"initial","hypothesisId":"C,D"})+'\n');
    except Exception: pass
    # #endregion
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    logger.warning("Not mounting StaticFiles (backend/static missing)")
    # #region agent log
    try:
        import json;open('/Users/jeffvestal/repos/wayfinder_supply_co/.cursor/debug.log','a').write(json.dumps({"location":"backend/main.py:101","message":"NOT mounting StaticFiles - directory missing","data":{"static_dir":str(STATIC_DIR),"static_dir_exists":False},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","runId":"initial","hypothesisId":"A,B"})+'\n');
    except Exception: pass
    # #endregion


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

