from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import json
import os
import logging
from tools.weather_service import get_trip_conditions
from tools.crm_service import get_customer_profile

logger = logging.getLogger("wayfinder.mcp")

app = FastAPI(title="Wayfinder Supply Co. MCP Server")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Validate X-Api-Key header against WAYFINDER_API_KEY env var."""

    async def dispatch(self, request: Request, call_next):
        expected_key = os.getenv("WAYFINDER_API_KEY")
        # No key configured → skip auth (local dev mode)
        if not expected_key:
            return await call_next(request)
        # Exempt health checks
        if request.url.path == "/health":
            return await call_next(request)
        provided_key = request.headers.get("X-Api-Key", "")
        if provided_key != expected_key:
            logger.warning(f"Rejected request to {request.url.path}: invalid or missing API key")
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
        return await call_next(request)


# API key auth middleware (skipped when WAYFINDER_API_KEY is unset)
app.add_middleware(ApiKeyMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load CRM mock data
CRM_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "crm_mock.json")


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict
    id: str


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: dict = None
    error: dict = None
    id: str


@app.post("/mcp")
async def handle_mcp_request(request: JSONRPCRequest):
    """
    Handle MCP JSON-RPC requests.
    """
    try:
        if request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            if tool_name == "get_trip_conditions_tool":
                result = get_trip_conditions(
                    arguments.get("location", ""),
                    arguments.get("dates", "")
                )
            elif tool_name == "get_customer_profile_tool":
                result = get_customer_profile(
                    arguments.get("user_id", ""),
                    CRM_DATA_PATH
                )
            else:
                return JSONRPCResponse(
                    jsonrpc="2.0",
                    error={
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    },
                    id=request.id
                )
            
            return JSONRPCResponse(
                jsonrpc="2.0",
                result=result,
                id=request.id
            )
        else:
            return JSONRPCResponse(
                jsonrpc="2.0",
                error={
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                },
                id=request.id
            )
    except Exception as e:
        return JSONRPCResponse(
            jsonrpc="2.0",
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            id=request.id
        )


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("MCP_SERVER_PORT", "8001")))
    uvicorn.run(app, host="0.0.0.0", port=port)

