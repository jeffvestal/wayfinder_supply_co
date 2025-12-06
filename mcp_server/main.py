from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from tools.weather_service import get_trip_conditions
from tools.crm_service import get_customer_profile

app = FastAPI(title="Wayfinder Supply Co. MCP Server")

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
    port = int(os.getenv("MCP_SERVER_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

