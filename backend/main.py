from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import chat, products, cart, reviews, orders, users, clickstream
from middleware.logging import LoggingMiddleware
from services.error_handler import global_exception_handler, http_exception_handler
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Wayfinder Supply Co. Backend API",
    version="1.0.0",
    description="Backend API for Wayfinder Supply Co. workshop"
)

# Static files directory (frontend build)
STATIC_DIR = Path(__file__).parent / "static"

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


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount static files if the directory exists (frontend build)
# This must be after API routes so they take precedence
if STATIC_DIR.exists():
    # Serve static assets (js, css, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="static-assets")
    
    # Catch-all route for SPA - serve index.html for any non-API route
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA frontend for any non-API route."""
        # If it's an API route, this won't match (API routes are registered first)
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not built. Run: cd frontend && npm run build"}
    
    @app.get("/")
    async def root():
        """Serve the SPA frontend index."""
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not built. Run: cd frontend && npm run build"}
else:
    @app.get("/")
    async def root():
        return {"message": "Wayfinder Supply Co. Backend API", "status": "running", "note": "Frontend not available - static/ directory not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

