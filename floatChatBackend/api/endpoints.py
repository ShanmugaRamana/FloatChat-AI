# api/endpoints.py

from fastapi import APIRouter
from schemas.models import QueryRequest, QueryResponse
from core.llm_service import get_llm_response

# Create a new router object
router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    Receives a user's question, gets a response from the LLM,
    and returns the answer.
    """
    # Call the core service function to get the LLM's response
    answer = await get_llm_response(request.question)
    
    # Return the response in the specified format
    return QueryResponse(answer=answer)