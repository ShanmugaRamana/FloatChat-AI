import httpx
from core import config
import json
import logging
from datetime import datetime # <-- Add this import

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

async def get_llm_response(prompt: str, model_name: str) -> str:
    """
    Calls the OpenRouter API to get a response from a specified LLM.
    """
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=60.0)
        response.raise_for_status() # Will raise an exception for 4xx/5xx errors
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
async def extract_filters_from_query(query: str) -> dict:
    """
    Uses an LLM to extract structured search filters from a natural language query.
    Now includes date/time awareness.
    """
    # Get the current date to provide context for relative time queries
    current_date = datetime.now().strftime('%Y-%m-%d')

    # This enhanced prompt teaches the LLM about dates and the current time
    prompt = f"""
    You are a data extraction tool. Analyze the following user query and extract any specified filters for latitude, longitude, dates, or float WMO ID.
    - The current date is {current_date}.
    - The user may use relative terms like "last year", "last 6 months", "in January", etc. Calculate the absolute dates.
    - The equator is at latitude 0. 'Near the equator' can be considered between -5 and 5 degrees latitude.
    - Return ONLY a valid JSON object with the keys "min_lat", "max_lat", "min_lon", "max_lon", "start_date", "end_date", "float_wmo_id".
    - Dates must be in YYYY-MM-DD format.
    - If no filters are found, return an empty JSON object {{}}.

    User Query: "{query}"

    JSON Output:
    """
    
    # Use a cheap, fast model for this simple extraction task
    model_name = "mistralai/mistral-7b-instruct:free"
    
    try:
        response_str = await get_llm_response(prompt, model_name)
        # Sanitize the response to ensure it's valid JSON
        json_str = response_str.strip().replace("`", "").replace("json", "")
        filters = json.loads(json_str)
        return filters
    except Exception as e:
        logging.error(f"Could not parse LLM filter extraction response: {e}")
        return {} # Return empty filters on failure