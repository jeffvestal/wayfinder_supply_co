"""
Helper functions for extracting JSON from agent responses.
Handles markdown code blocks, fallback patterns, and structured extraction.
"""

import json
import re
from typing import Optional, Dict, Any


def strip_markdown_code_blocks(text: str) -> str:
    """Remove markdown code blocks (```json ... ``` or ``` ... ```) from text."""
    if not text or "```" not in text:
        return text.strip()
    
    lines = text.split("\n")
    json_lines = []
    in_json = False
    
    for line in lines:
        if line.strip().startswith("```"):
            if in_json:
                break  # End of code block
            in_json = True
            continue
        if in_json:
            json_lines.append(line)
    
    if json_lines:
        return "\n".join(json_lines).strip()
    
    return text.strip()


def extract_json_from_response(
    response_text: str,
    required_fields: Optional[list[str]] = None,
    fallback: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract JSON from agent response with markdown handling.
    
    Args:
        response_text: Raw response that may contain markdown code blocks
        required_fields: If provided, try regex fallback to find JSON containing these fields
        fallback: Default dict to return on failure (if None, returns empty dict)
    
    Returns:
        Parsed JSON dict, or fallback if parsing fails
    """
    if not response_text:
        return fallback or {}
    
    # Strip markdown code blocks
    cleaned_text = strip_markdown_code_blocks(response_text)
    
    # Try to parse as JSON directly
    try:
        parsed = json.loads(cleaned_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # If required_fields provided, try regex fallback
    if required_fields:
        # Build regex pattern to find JSON object containing required fields
        # Example: r'\{[^{}]*"destination"[^{}]*\}'
        field_pattern = '|'.join(f'"{field}"' for field in required_fields)
        json_pattern = rf'\{{[^{{}}]*({field_pattern})[^{{}}]*\}}'
        
        json_match = re.search(json_pattern, cleaned_text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, AttributeError):
                pass
    
    # Return fallback or empty dict
    return fallback or {}

