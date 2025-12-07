from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import httpx
import os
import json
from typing import Optional

router = APIRouter()

KIBANA_URL = os.getenv("STANDALONE_KIBANA_URL", os.getenv("KIBANA_URL", "http://kubernetes-vm:30001"))
ELASTICSEARCH_APIKEY = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))


async def stream_agent_response(message: str, user_id: str, agent_id: str = "trip-planner-agent"):
    """
    Proxy SSE stream from Elastic Agent Builder to frontend.
    """
    url = f"{KIBANA_URL}/api/agent_builder/converse/async"
    
    headers = {
        "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
    }
    
    payload = {
        "input": message,
        "agent_id": agent_id,
        "conversation_id": None,  # Start new conversation
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Agent Builder API error: {error_text.decode()}"
                    )
                
                async def event_generator():
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            try:
                                data = json.loads(data_str)
                                yield {
                                    "event": data.get("event", "message"),
                                    "data": json.dumps(data.get("data", {}))
                                }
                            except json.JSONDecodeError:
                                continue
                        elif line.strip():
                            # Handle non-SSE formatted lines
                            yield {
                                "event": "message",
                                "data": json.dumps({"text": line})
                            }
                
                return EventSourceResponse(event_generator())
        
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Connection error: {str(e)}")


from fastapi import Query

@router.post("/chat")
async def chat_endpoint(
    message: str = Query(..., description="The chat message"),
    user_id: Optional[str] = Query("user_new", description="User ID"),
    agent_id: Optional[str] = Query("trip-planner-agent", description="Agent ID")
):
    """
    Chat endpoint that proxies to Elastic Agent Builder streaming API.
    """
    # Prepend user context to message
    contextual_message = f"[User ID: {user_id}] {message}"
    
    return await stream_agent_response(contextual_message, user_id, agent_id)

