from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Files API")
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    allowed_image_exts: set[str] = set(os.getenv("ALLOWED_IMAGE_EXTS", ".jpg,.jpeg,.png,.webp,.gif").split(","))
    allowed_doc_exts: set[str] = set(os.getenv("ALLOWED_DOC_EXTS", ".pdf,.txt,.csv").split(","))
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./storage/meta.db")
    force_https: bool = os.getenv("FORCE_HTTPS", "false").lower() == "true"

settings = Settings()