# backend/routers/chat.py
"""
Chat router that proxies requests to Elastic Agent Builder with streaming support.
Based on the-price-is-bot implementation for proper SSE handling.
Supports optional image analysis via Jina VLM when vision is configured.
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import os
import json
import logging
import time
from typing import Optional
from services.json_parser import extract_json_from_response
from services.credential_manager import get_credential_manager
from services import vision_service

logger = logging.getLogger("wayfinder.chat")

router = APIRouter()

KIBANA_URL = os.getenv("STANDALONE_KIBANA_URL", os.getenv("KIBANA_URL", "http://kubernetes-vm:30001"))
ELASTICSEARCH_APIKEY = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))

CONNECTOR_FLASH = "Google-Gemini-2-5-Flash"
CONNECTOR_MINI = "OpenAI-GPT-4-1-Mini"

AGENT_CONNECTOR_MAP = {
    "wayfinder-search-agent": CONNECTOR_FLASH,
    "trip-planner-agent": CONNECTOR_FLASH,
    "trip-itinerary-agent": CONNECTOR_FLASH,
    "context-extractor-agent": CONNECTOR_MINI,
    "response-parser-agent": CONNECTOR_MINI,
    "itinerary-extractor-agent": CONNECTOR_MINI,
}


class ChatRequest(BaseModel):
    """Chat request body - supports text and optional image."""
    message: str
    user_id: str = "user_new"
    agent_id: str = "wayfinder-search-agent"
    image_base64: Optional[str] = None
    vision_analysis: Optional[dict] = None


@router.post("/parse-trip-context")
async def parse_trip_context_endpoint(
    message: str = Query(..., description="The user message to parse")
):
    """
    Parse trip context (destination, dates, activity) from user message.
    Calls context-extractor-agent synchronously and returns JSON.
    """
    url = f"{KIBANA_URL}/api/agent_builder/converse/async"
    
    headers = {
        "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
    }
    
    payload = {
        "input": message,
        "agent_id": "context-extractor-agent",
        "connector_id": AGENT_CONNECTOR_MAP.get("context-extractor-agent", CONNECTOR_MINI),
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Agent Builder API error: {error_text.decode() if error_text else 'Unknown error'}"
                    )
                
                # Collect the full response
                full_response = ""
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            raw_data = json.loads(data_str)
                            data = raw_data.get("data", raw_data)
                            
                            # Look for message content
                            if "text_chunk" in data:
                                full_response += data["text_chunk"]
                            elif "message_content" in data:
                                full_response = data["message_content"]
                            elif "round" in data:
                                round_data = data["round"]
                                if "response" in round_data and "message" in round_data["response"]:
                                    full_response = round_data["response"]["message"]
                        except json.JSONDecodeError:
                            continue
                
                # Parse JSON from response using helper
                parsed = extract_json_from_response(
                    full_response,
                    required_fields=["destination", "dates", "activity"],
                    fallback={"destination": None, "dates": None, "activity": None}
                )
                return {
                    "destination": parsed.get("destination"),
                    "dates": parsed.get("dates"),
                    "activity": parsed.get("activity")
                }
                    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/chat")
async def chat_endpoint(
    request: Optional[ChatRequest] = None,
    message: Optional[str] = Query(None, description="The chat message (legacy query param)"),
    user_id: Optional[str] = Query(None, description="User ID (legacy query param)"),
    agent_id: Optional[str] = Query(None, description="Agent ID (legacy query param)"),
):
    """
    Chat endpoint that proxies to Elastic Agent Builder streaming API.
    Returns SSE stream with reasoning, tool_call, tool_result, message_chunk events.

    Accepts either:
    - JSON body: {"message": "...", "user_id": "...", "agent_id": "...", "image_base64": "..."}
    - Query params: ?message=...&user_id=...&agent_id=... (backward compatible)
    """
    if request and (request.message or request.image_base64):
        msg = request.message
        uid = request.user_id
        aid = request.agent_id
        image = request.image_base64
        preanalysis = request.vision_analysis
    elif message:
        msg = message
        uid = user_id or "user_new"
        aid = agent_id or "wayfinder-search-agent"
        image = None
        preanalysis = None
    else:
        raise HTTPException(status_code=400, detail="Message or image is required")

    t_start = time.time()
    logger.warning(f"[PERF] chat_endpoint START: has_image={bool(image)}, has_preanalysis={bool(preanalysis)}, aid={aid}, msg_preview={(msg or '')[:50]}")

    if not msg.strip() and (image or preanalysis):
        msg = "Find products similar to what's shown in this image"

    async def chat_stream():
        """
        SSE generator that streams events immediately.
        Vision analysis runs INSIDE the stream so the first byte reaches
        the frontend in <100ms (with a vision_analyzing progress event).
        """
        vision_context = ""
        vision_description = ""
        vision_structured_data = None
        vision_error = None

        # --- Phase 1: Vision analysis (use pre-analysis if available) ---
        if preanalysis and preanalysis.get("description"):
            vision_structured_data = preanalysis
            vision_description = preanalysis.get("description", "")
            if aid == "wayfinder-search-agent":
                product_type = preanalysis.get("product_type", "")
                category = preanalysis.get("category", "")
                vision_context = (
                    f"[Vision Context: {product_type} - {vision_description}] "
                    f"[Product Category: {category}] "
                )
            else:
                vision_context = f"[Vision Context: {vision_description}] "
            logger.warning("[PERF] vision_analysis: 0.0s (using pre-analysis from frontend)")
        elif preanalysis and preanalysis.get("category"):
            category = preanalysis["category"]
            vision_context = f"[Product Category: {category}] "
            logger.warning("[PERF] vision_analysis: 0.0s (category-only session context)")
        elif image:
            cm = get_credential_manager()
            vision_ready = cm.is_vision_ready()
            if vision_ready:
                yield format_sse_event("vision_analyzing", {
                    "message": "Analyzing your image...",
                    "agent_id": aid,
                })

                t_vision_start = time.time()
                try:
                    if aid == "wayfinder-search-agent":
                        vision_structured_data = await vision_service.analyze_image_structured(image)
                        vision_description = vision_structured_data.get("description", "")
                        product_type = vision_structured_data.get("product_type", "")
                        category = vision_structured_data.get("category", "")
                        vision_context = (
                            f"[Vision Context: {product_type} - {vision_description}] "
                            f"[Product Category: {category}] "
                        )
                        logger.info(f"Structured vision context: product_type={product_type}, category={category}")
                    else:
                        vision_description = await vision_service.analyze_image(image)
                        vision_context = f"[Vision Context: {vision_description}] "
                except Exception as e:
                    vision_error = f"Image analysis unavailable: {type(e).__name__}"
                    if "503" in str(e):
                        vision_error = "Image analysis service is warming up — please try again in 30-60 seconds"
                    logger.warning(f"Vision analysis failed, proceeding without: {type(e).__name__}: {e}")

                t_vision_elapsed = time.time() - t_vision_start
                logger.warning(f"[PERF] vision_analysis: {t_vision_elapsed:.1f}s")
            else:
                logger.info("Image provided but Jina VLM not configured, ignoring image")

        # Emit vision result events
        if vision_description:
            vision_event_data = {"description": vision_description}
            if vision_structured_data:
                vision_event_data.update({
                    "product_type": vision_structured_data.get("product_type", ""),
                    "category": vision_structured_data.get("category", ""),
                    "subcategory": vision_structured_data.get("subcategory", ""),
                    "key_terms": vision_structured_data.get("key_terms", []),
                })
            yield format_sse_event("vision_analysis", vision_event_data)
        elif vision_error:
            yield format_sse_event("vision_error", {"error": vision_error})

        # --- Phase 2: Agent Builder streaming ---
        contextual_message = f"{vision_context}[User ID: {uid}] {msg}"
        t_agent_start = time.time()
        async for chunk in stream_agent_response(contextual_message, aid):
            yield chunk
        t_agent_elapsed = time.time() - t_agent_start
        t_total = time.time() - t_start
        logger.warning(f"[PERF] chat_endpoint DONE: total={t_total:.1f}s, agent={t_agent_elapsed:.1f}s")

    return StreamingResponse(
        chat_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


async def stream_agent_response(message: str, agent_id: str = "wayfinder-search-agent"):
    """
    Proxy SSE stream from Elastic Agent Builder to frontend.
    Parses Agent Builder events and forwards them in a consistent format.
    """
    url = f"{KIBANA_URL}/api/agent_builder/converse/async"
    
    headers = {
        "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
    }
    
    connector_id = AGENT_CONNECTOR_MAP.get(agent_id, CONNECTOR_FLASH)
    payload = {
        "input": message,
        "agent_id": agent_id,
        "connector_id": connector_id,
    }
    logger.info(f"Agent {agent_id} using connector {connector_id}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_chunks = []
                    async for chunk in response.aiter_bytes():
                        error_chunks.append(chunk)
                    error_text = b"".join(error_chunks).decode()
                    yield format_sse_event("error", {"error": f"Agent Builder API error: {error_text}"})
                    return
                
                buffer = ""
                current_event_type = ""
                steps = []
                conversation_id = ""
                
                async for chunk in response.aiter_bytes():
                    buffer += chunk.decode()
                    
                    # Process complete lines
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                        
                        if line.startswith("event: "):
                            current_event_type = line[7:].strip()
                            continue
                        
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                raw_data = json.loads(data_str)
                                
                                # Agent Builder wraps data in {"data": {...}}
                                data = raw_data.get("data", raw_data)
                                
                                # Handle errors from Kibana (e.g., expired API keys, rate limits)
                                if "error" in raw_data:
                                    error_info = raw_data["error"]
                                    error_message = error_info.get("message", "Unknown error") if isinstance(error_info, dict) else str(error_info)
                                    yield format_sse_event("error", {
                                        "error": error_message,
                                        "code": error_info.get("code") if isinstance(error_info, dict) else None
                                    })
                                    continue
                                
                                # Handle conversation_id
                                if "conversation_id" in data:
                                    conversation_id = data["conversation_id"]
                                    yield format_sse_event("conversation_started", {
                                        "conversation_id": conversation_id
                                    })
                                
                                # Handle reasoning events
                                elif "reasoning" in data:
                                    reasoning_text = data["reasoning"]
                                    # Skip transient "Consulting my tools" messages
                                    if not data.get("transient", False):
                                        steps.append({
                                            "type": "reasoning",
                                            "reasoning": reasoning_text
                                        })
                                        yield format_sse_event("reasoning", {
                                            "reasoning": reasoning_text
                                        })
                                
                                # Handle tool results (MUST check before tool_call_id alone!)
                                # Tool result events have both "results" AND "tool_call_id"
                                elif "results" in data and "tool_call_id" in data:
                                    tool_call_id = data["tool_call_id"]
                                    results = data["results"]
                                    
                                    logger.warning(f"[DBG:tool_result] tool_call_id={tool_call_id}, results_type={type(results).__name__}, results_len={len(results) if isinstance(results, list) else 'N/A'}")
                                    if isinstance(results, list):
                                        for idx, item in enumerate(results):
                                            if isinstance(item, dict):
                                                logger.warning(f"[DBG:tool_result] result[{idx}] type={item.get('type')}, keys={list(item.keys())}, sample={json.dumps(item, default=str)[:400]}")
                                            else:
                                                logger.warning(f"[DBG:tool_result] result[{idx}] raw_type={type(item).__name__}")
                                    
                                    # Update the corresponding step
                                    for step in steps:
                                        if step.get("tool_call_id") == tool_call_id:
                                            step["results"] = results
                                            break
                                    
                                    yield format_sse_event("tool_result", {
                                        "tool_call_id": tool_call_id,
                                        "results": results
                                    })
                                
                                elif "tool_call_id" in data:
                                    tool_call_id = data.get("tool_call_id")
                                    tool_id = data.get("tool_id")
                                    params = data.get("params", {})
                                    
                                    if not tool_id:
                                        continue
                                    
                                    logger.warning(f"[DBG:tool_call] id={tool_call_id}, tool={tool_id}, has_params={bool(params)}")
                                    
                                    # Check if we already have this tool call
                                    existing_step = None
                                    for step in steps:
                                        if step.get("tool_call_id") == tool_call_id:
                                            existing_step = step
                                            break
                                    
                                    if existing_step:
                                        if params:
                                            existing_step["params"] = params
                                    else:
                                        tool_step = {
                                            "type": "tool_call",
                                            "tool_call_id": tool_call_id,
                                            "tool_id": tool_id,
                                            "params": params,
                                            "results": []
                                        }
                                        steps.append(tool_step)
                                        yield format_sse_event("tool_call", {
                                            "tool_call_id": tool_call_id,
                                            "tool_id": tool_id,
                                            "params": params
                                        })
                                
                                # Handle text chunks (message content)
                                elif "text_chunk" in data:
                                    yield format_sse_event("message_chunk", {
                                        "text_chunk": data["text_chunk"]
                                    })
                                
                                # Handle complete message
                                elif "message_content" in data:
                                    yield format_sse_event("message_complete", {
                                        "message_content": data["message_content"]
                                    })
                                
                                # Handle round completion (contains full response)
                                elif "round" in data:
                                    round_data = data["round"]
                                    if "response" in round_data and "message" in round_data["response"]:
                                        yield format_sse_event("message_complete", {
                                            "message_content": round_data["response"]["message"]
                                        })
                                
                            except json.JSONDecodeError:
                                continue
                
                # Send completion event
                yield format_sse_event("completion", {
                    "conversation_id": conversation_id,
                    "steps": steps
                })
                
        except httpx.TimeoutException:
            yield format_sse_event("error", {"error": "Request timeout"})
        except httpx.RequestError as e:
            yield format_sse_event("error", {"error": f"Connection error: {str(e)}"})
        except Exception as e:
            yield format_sse_event("error", {"error": f"Unexpected error: {str(e)}"})


def format_sse_event(event_type: str, data: dict) -> str:
    """Format data as an SSE event string."""
    return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"


@router.get("/agent-status/{agent_id}")
async def check_agent_status(agent_id: str):
    """Check if an agent exists and is accessible."""
    url = f"{KIBANA_URL}/api/agent_builder/agents/{agent_id}"
    headers = {
        "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
        "kbn-xsrf": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            return {"exists": response.status_code == 200, "agent_id": agent_id}
    except Exception as e:
        return {"exists": False, "agent_id": agent_id, "error": str(e)}


@router.post("/extract-itinerary")
async def extract_itinerary_endpoint(
    trip_plan: str = Query(..., description="The trip plan text to extract itinerary from")
):
    """
    Extract structured day-by-day itinerary from a trip plan.
    Calls itinerary-extractor-agent synchronously and returns JSON.
    """
    url = f"{KIBANA_URL}/api/agent_builder/converse/async"
    
    headers = {
        "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
    }
    
    payload = {
        "input": trip_plan,
        "agent_id": "itinerary-extractor-agent",
        "connector_id": AGENT_CONNECTOR_MAP.get("itinerary-extractor-agent", CONNECTOR_MINI),
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Agent Builder API error: {error_text.decode() if error_text else 'Unknown error'}"
                    )
                
                # Collect the full response
                full_response = ""
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            raw_data = json.loads(data_str)
                            data = raw_data.get("data", raw_data)
                            
                            # Look for message content
                            if "text_chunk" in data:
                                full_response += data["text_chunk"]
                            elif "message_content" in data:
                                full_response = data["message_content"]
                            elif "round" in data:
                                round_data = data["round"]
                                if "response" in round_data and "message" in round_data["response"]:
                                    full_response = round_data["response"]["message"]
                        except json.JSONDecodeError:
                            continue
                
                # Parse JSON from response using helper
                parsed = extract_json_from_response(
                    full_response,
                    required_fields=["days"],
                    fallback={"days": []}
                )
                return {"days": parsed.get("days", [])}
                    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/extract-trip-entities")
async def extract_trip_entities_endpoint(
    trip_plan: str = Query(..., description="The trip plan text to extract entities from")
):
    """
    Extract structured entities (products, itinerary, safety notes) from a trip plan.
    Calls response-parser-agent via workflow (or directly if workflow unavailable).
    Returns structured JSON for populating sidebar panels.
    """
    # First try to call the workflow
    workflow_url = f"{KIBANA_URL}/api/workflows/run"
    headers = {
        "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "kibana",
    }
    
    workflow_payload = {
        "workflow_name": "extract_trip_entities",
        "inputs": {
            "trip_plan_text": trip_plan
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Try workflow first
            workflow_response = await client.post(workflow_url, headers=headers, json=workflow_payload)
            
            if workflow_response.status_code == 200:
                # Parse workflow response
                result = workflow_response.json()
                # Extract the agent's response from workflow output
                # The workflow returns the parser agent's JSON response
                return parse_extraction_result(result)
            
            # Workflow failed, fall back to direct agent call
            agent_url = f"{KIBANA_URL}/api/agent_builder/converse/async"
            agent_headers = {
                "Authorization": f"ApiKey {ELASTICSEARCH_APIKEY}",
                "Content-Type": "application/json",
                "kbn-xsrf": "true",
            }
            agent_payload = {
                "input": trip_plan,
                "agent_id": "response-parser-agent",
                "connector_id": AGENT_CONNECTOR_MAP.get("response-parser-agent", CONNECTOR_MINI),
            }
            
            async with client.stream("POST", agent_url, headers=agent_headers, json=agent_payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Agent error: {error_text.decode()}"
                    )
                
                # Collect the full response
                full_response = ""
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            raw_data = json.loads(data_str)
                            data = raw_data.get("data", raw_data)
                            
                            if "text_chunk" in data:
                                full_response += data["text_chunk"]
                            elif "message_content" in data:
                                full_response = data["message_content"]
                            elif "round" in data:
                                round_data = data["round"]
                                if "response" in round_data and "message" in round_data["response"]:
                                    full_response = round_data["response"]["message"]
                        except json.JSONDecodeError:
                            continue
                
                return parse_extraction_result({"response": full_response})
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def parse_extraction_result(result: dict) -> dict:
    """Parse the extraction result from workflow or agent response."""
    # Get the response text
    response_text = ""
    if isinstance(result, dict):
        if "response" in result:
            response_text = result["response"]
        elif "output" in result:
            output = result["output"]
            if isinstance(output, dict) and "response" in output:
                response_text = output["response"].get("message", "")
            else:
                response_text = str(output)
        else:
            response_text = str(result)
    else:
        response_text = str(result)
    
    # Use helper to extract JSON
    parsed = extract_json_from_response(
        response_text,
        required_fields=["products"],
        fallback={
            "products": [],
            "itinerary": [],
            "safety_notes": [],
            "weather": None
        }
    )
    
    # Ensure we have the expected structure
    return {
        "products": parsed.get("products", []),
        "itinerary": parsed.get("itinerary", []),
        "safety_notes": parsed.get("safety_notes", []),
        "weather": parsed.get("weather", None)
    }
