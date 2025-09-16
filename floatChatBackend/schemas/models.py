# schemas/models.py

from pydantic import BaseModel

class QueryRequest(BaseModel):
    """
    Defines the shape of an incoming request.
    The user must provide a 'question' string.
    """
    question: str

class QueryResponse(BaseModel):
    """
    Defines the shape of the outgoing response.
    The API will return the 'answer' from the LLM.
    """
    answer: str