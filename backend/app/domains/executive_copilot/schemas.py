from pydantic import BaseModel


class ExecutiveInsightQuery(BaseModel):
    region: str | None = None
    question: str
