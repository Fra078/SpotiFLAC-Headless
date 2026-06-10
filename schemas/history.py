from pydantic import BaseModel
from typing import Optional

class HistoryItem(BaseModel):
    url: str
    label: str
    cover: Optional[str] = ""
    track_count: int = 0
    url_type: Optional[str] = ""
    artist: Optional[str] = ""
    at: int
