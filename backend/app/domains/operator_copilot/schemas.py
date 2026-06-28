from pydantic import BaseModel


class OperatorMetricQuery(BaseModel):
    region: str | None = None
    metric_name: str | None = None
