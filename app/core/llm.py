from openai import OpenAI
import httpx
from app.core.config import settings

# Use a global httpx client with HTTP/2 enabled and larger keepalive settings
# to prevent "peer closed connection" (RemoteProtocolError)
shared_http_client = httpx.Client(
    timeout=httpx.Timeout(settings.OPENAI_TIMEOUT_SECONDS, read=120.0),
    limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
    http2=True,
)

# Global OpenAI client for OpenAI API
openai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    http_client=shared_http_client,
)

# Global OpenAI client for Groq API
groq_client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    http_client=shared_http_client,
)

def get_llm_client(model_name: str) -> OpenAI:
    """Return the appropriate global client based on model name."""
    if "llama" in model_name.lower() or "mixtral" in model_name.lower() or "gemma" in model_name.lower():
        return groq_client
    return openai_client
