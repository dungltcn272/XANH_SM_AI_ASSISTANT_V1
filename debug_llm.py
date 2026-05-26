import sys
import traceback
from openai import OpenAI
from app.config import config

# Force UTF-8
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

print("Starting debug_llm...")
try:
    print("API Key:", config.OPENAI_API_KEY[:15] + "..." if config.OPENAI_API_KEY else "None")
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    print("Calling completions...")
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.2,
    )
    print("SUCCESS!")
except BaseException as e:
    print(f"FAILED with exception: {type(e)}: {e}")
    traceback.print_exc()
