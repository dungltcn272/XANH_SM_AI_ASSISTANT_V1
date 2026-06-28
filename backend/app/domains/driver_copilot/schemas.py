from pydantic import BaseModel


class DriverCopilotContext(BaseModel):
    driver_id: str | None = None
    region: str | None = None
