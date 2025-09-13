from pydantic import BaseModel, Field
from typing import Literal
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    query: str
    model: Literal["mistralai/mistral-7b-instruct:free", "meta-llama/llama-3.3-70b-instruct:free"] = Field(
        default="mistralai/mistral-7b-instruct:free",
        description="The LLM model to use for the answer."
    )

class ChatResponse(BaseModel):
    answer: str
