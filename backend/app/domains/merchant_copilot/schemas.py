from pydantic import BaseModel


class MerchantCopilotContext(BaseModel):
    merchant_id: str
    period: str = "week"
