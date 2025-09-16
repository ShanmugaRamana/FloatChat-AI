# core/llm_service.py

import httpx
from config.settings import settings
from core.prompt_manager import create_prompt

async def get_llm_response(question: str) -> str:
    """
    Sends a question to the OpenRouter API and returns the response.
    """
    # Create the full prompt using the prompt manager
    full_prompt = create_prompt(question)

    # Prepare the API request headers and body
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": settings.APP_SITE_URL, 
        "X-Title": "floatChat", 
    }
    
    body = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": full_prompt},
        ]
    }
    
    api_url = f"{settings.OPENROUTER_API_BASE}/chat/completions"

    try:
        # Use an async client to make the API call
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=body)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            data = response.json()
            return data['choices'][0]['message']['content']

    except httpx.HTTPStatusError as e:
        print(f"API request failed with status {e.response.status_code}: {e.response.text}")
        return f"Sorry, there was an error with the API request (Status {e.response.status_code})."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "Sorry, an unexpected error occurred while contacting the language model."