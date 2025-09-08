from pydantic import BaseModel, Field
from typing import Literal

class ChatRequest(BaseModel):
    query: str
    model: Literal["mistralai/mistral-7b-instruct:free", "meta-llama/llama-3.3-8b-instruct:free"] = Field(
        default="meta-llama/llama-3.3-8b-instruct:free",
        description="The LLM model to use for the answer."
    )

class ChatResponse(BaseModel):
    answer: str