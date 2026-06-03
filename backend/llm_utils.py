
import os
import time
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

def get_groq_llm(temperature=0.2, max_tokens=2048):
    """
    Returns a ChatGroq instance configured with the current model and parameters.
    It natively uses max_retries, but we will also wrap invocations for robust rate limit handling.
    """
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        logger.error("langchain_groq is not installed. Please run pip install langchain-groq")
        raise
        
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=5
    )

# Create a retry decorator that waits exponentially between 2 and 60 seconds, up to 6 times.
# We catch Exception because Langchain's Groq wrapper might throw a generic Exception or GroqError on 429.
@retry(
    wait=wait_exponential(multiplier=2, min=2, max=60),
    stop=stop_after_attempt(6),
    reraise=True
)
def safe_invoke(llm, messages):
    """
    Safely invokes the LLM with exponential backoff to handle strict token rate limits (like Groq's 8k/min limit).
    """
    try:
        return llm.invoke(messages)
    except Exception as e:
        err_msg = str(e).lower()
        if "429" in err_msg or "rate limit" in err_msg or "too many requests" in err_msg:
            logger.warning(f"Rate limit hit during LLM invocation, backing off... ({e})")
            raise  # Let tenacity handle the retry
        # If it's not a rate limit error, we might still want to retry if it's a 503, but for now we'll just raise it
        # Actually, let's just let tenacity retry any exception for robustness in background agents.
        logger.warning(f"Error during LLM invocation, retrying... ({e})")
        raise
