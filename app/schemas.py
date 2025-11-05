from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileOut(BaseModel):
    id: int
    uuid: str
    original_name: str
    content_type: str
    size: int
    ext: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True