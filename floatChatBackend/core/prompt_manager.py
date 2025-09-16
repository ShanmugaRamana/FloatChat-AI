# core/prompt_manager.py

def create_prompt(question: str) -> str:
    """
    Creates a structured prompt with system instructions for the LLM.
    """
    
    # This is a basic prompt template. You can make it much more complex.
    prompt_template = f"""
You are an expert oceanography AI assistant named floatChat.
Your primary function is to answer questions about ocean data, ARGO floats, and related scientific concepts.
Provide answers that are accurate, concise, and easy to understand for a scientific audience.

Based on the user's question below, generate a helpful response.

---
User Question: "{question}"
---
"""
    return prompt_template.strip()