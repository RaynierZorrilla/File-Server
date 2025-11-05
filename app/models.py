from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str
    original_name: str
    storage_name: str
    content_type: str
    size: int
    ext: str
    checksum_sha256: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)