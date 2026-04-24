from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any

class Event(BaseModel):
    topic: str = Field(..., min_length=1, description="Topic of the event")
    event_id: str = Field(..., min_length=1, description="Unique identifier for the event")
    timestamp: datetime
    source: str
    payload: Dict[str, Any]
