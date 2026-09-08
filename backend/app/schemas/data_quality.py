from datetime import datetime

from pydantic import BaseModel


class DataAnomalyOut(BaseModel):
    tmdb_id: int
    title: str
    poster_path: str | None = None
    rule_name: str
    severity: str
    detail: str
    ai_explanation: str | None = None
    detected_at: datetime
