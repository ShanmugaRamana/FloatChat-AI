import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import search as search_schema # <-- Add this import
from db import crud # <-- Add this import
import re # <-- Add this import at the top of the file

from schemas import chat as chat_schema
from services import llm_service
from db import vector_search, database
from core.dependencies import get_search_services, SearchServices

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()
GREETINGS = ["hi", "hello", "hey", "hallo", "greetings"]

# In api/routers/chat.py

def construct_llm_prompt(query: str, context_profiles: list) -> str:
    """
    Constructs a detailed prompt to guide the LLM into producing a high-quality,
    structured text answer.
    """
    if not context_profiles:
        # This helpful response for "no data found" remains the same.
        return f"""
        You are FloatChat, an expert oceanographer AI assistant. You were unable to find specific data points for the user's query. 
        Instead of saying you don't have the data, be a helpful assistant. Suggest a different way the user could ask, or ask for clarification.
        User Question: {query}
        Helpful Response:
        """

    context_lines = []
    for p in context_profiles:
        line = (f"ID: {p.id}, Time: {p.timestamp.strftime('%Y-%m-%d')}, Lat: {p.latitude:.2f}, Lon: {p.longitude:.2f}, Measurements: {p.measurements}")
        context_lines.append(line)
    context_str = "\n".join(context_lines)
    
    # This new prompt gives the LLM a strict template for its text response.
    prompt = f"""
    You are FloatChat, an expert oceanographer AI assistant. Your tone is knowledgeable and concise.
    Your task is to provide a comprehensive answer to the user's question based ONLY on the retrieved data points below.

    **Retrieved Data:**
    {context_str}

    **User Question:** {query}

    ---
    **Response Rules:**
    1.  **Summarize First:** Begin your answer with a one-sentence summary that directly answers the user's question.
    2.  **Provide Key Findings:** After the summary, create a bulleted list (-) of the most important findings.
    3.  **Cite Your Data:** When you mention a specific value, refer to the data point ID it came from (e.g., "The highest salinity of **35.5 PSS-78** was found in profile **ID: 12345**.").
    4.  **Formatting:** Use markdown, especially bolding (`**text**`) for key values and bullet points (`-`).
    5.  **Be Factual:** Do not make assumptions or use information not present in the "Retrieved Data" section.
    ---

    **Formatted Answer:**
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
    if request.query.lower().strip() in GREETINGS:
        answer = "Hello! I am FloatChat, your oceanography AI assistant. How can I help you query the data today?"
        return chat_schema.ChatResponse(answer=answer)
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
        raw_answer = await llm_service.get_llm_response(
            prompt=prompt,
            model_name=request.model
        )
        cleaned_answer = re.sub(r'\n{3,}', '\n\n', raw_answer).strip()

        return chat_schema.ChatResponse(answer=cleaned_answer)

    except Exception as e:
        logging.error(f"Error during chat processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")