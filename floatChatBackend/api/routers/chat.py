import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import search as search_schema # <-- Add this import
from db import crud # <-- Add this import

from schemas import chat as chat_schema
from services import llm_service
from db import vector_search, database
from core.dependencies import get_search_services, SearchServices

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()

def construct_llm_prompt(query: str, context_profiles: list) -> str:
    """Constructs the prompt for the LLM with retrieved context."""
    if not context_profiles:
        return f"""
        You are an expert oceanographer AI. You were unable to find any relevant data. 
        Please inform the user that no specific data could be found to answer their question.
        User Question: {query}
        Answer:
        """

    # FIX: Create a more detailed context string that includes lat, lon, and time.
    context_lines = []
    for p in context_profiles:
        line = (
            f"ID: {p.id}, "
            f"Time: {p.timestamp.strftime('%Y-%m-%d')}, "
            f"Lat: {p.latitude:.2f}, "
            f"Lon: {p.longitude:.2f}, "
            f"Measurements: {p.measurements}"
        )
        context_lines.append(line)
    context_str = "\n".join(context_lines)
    
    prompt = f"""
    Context: You are an expert oceanographer AI. Based ONLY on the following retrieved data points, please answer the user's question. Do not use any prior knowledge. If the data is insufficient, say so.

    Retrieved Data:
    {context_str}

    User Question: {query}
    
    Answer:
    """
    return prompt

@router.post(
    "/",
    response_model=chat_schema.ChatResponse,
    summary="Get an AI-generated answer to a query about ocean data"
)
async def handle_chat_query(
    request: chat_schema.ChatRequest,
    db: Session = Depends(database.get_db_session),
    search_services: SearchServices = Depends(get_search_services)
):
    """
    This endpoint now uses a Hybrid Search pattern:
    1.  **Extract**: Use an LLM to find filters (e.g., location) in the query.
    2.  **Filter**: Use SQL to get a candidate set of data matching the filters.
    3.  **Retrieve**: Perform a vector search on the candidate set to find the most relevant items.
    4.  **Generate**: Use an LLM to generate an answer based on the retrieved items.
    """
    try:
        # 1. Extract structured filters from the query
        logging.info(f"Extracting filters from query: '{request.query}'")
        extracted_filters = await llm_service.extract_filters_from_query(request.query)
        logging.info(f"Extracted filters: {extracted_filters}")

        candidate_ids = None
        if extracted_filters:
            # 2. Pre-filter with SQL to get a candidate set of IDs
            filter_model = search_schema.FilterRequest(**extracted_filters)
            candidate_profiles = crud.search_profiles(db=db, filters=filter_model, limit=1000)
            candidate_ids = [p.id for p in candidate_profiles]
            logging.info(f"Found {len(candidate_ids)} candidates via SQL pre-filter.")

        # 3. Retrieve relevant data using vector search (on the candidate set if available)
        relevant_profiles = await vector_search.find_similar_profiles(
            query=request.query,
            db=db,
            chroma_collection=search_services.chroma_collection,
            embedding_model=search_services.embedding_model,
            top_k=5,
            filter_ids=candidate_ids # Pass the candidate IDs to the vector search
        )

        # 4. Augment the prompt and Generate a response from the LLM
        logging.info(f"Constructing prompt with {len(relevant_profiles)} context profiles.")
        prompt = construct_llm_prompt(request.query, relevant_profiles)
        
        logging.info(f"Sending prompt to LLM model: {request.model}")
        answer = await llm_service.get_llm_response(
            prompt=prompt,
            model_name=request.model
        )
        
        return chat_schema.ChatResponse(answer=answer)

    except Exception as e:
        logging.error(f"Error during chat processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")