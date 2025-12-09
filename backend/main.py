from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from routers import chat, products, cart, reviews, orders, users, clickstream
from middleware.logging import LoggingMiddleware
from services.error_handler import global_exception_handler, http_exception_handler
import os
import logging

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


@app.get("/")
async def root():
    return {"message": "Wayfinder Supply Co. Backend API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

