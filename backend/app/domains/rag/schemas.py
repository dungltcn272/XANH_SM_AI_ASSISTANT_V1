from pydantic import BaseModel


class RagQuery(BaseModel):
    query: str
    persona: str = "customer"
    top_k: int = 8
