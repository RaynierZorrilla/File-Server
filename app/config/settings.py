from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Files API")
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    allowed_image_exts: set[str] = set(os.getenv("ALLOWED_IMAGE_EXTS", ".jpg,.jpeg,.png,.webp,.gif").split(","))
    allowed_doc_exts: set[str] = set(os.getenv("ALLOWED_DOC_EXTS", ".pdf,.txt,.csv").split(","))
    allowed_video_exts: set[str] = set(os.getenv("ALLOWED_VIDEO_EXTS", ".mp4,.webm,.mov,.avi,.mkv,.flv,.wmv,.m4v").split(","))
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./storage/meta.db")
    force_https: bool = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "56f84346dd43250488c446dadce037b8e853cbfa56bef456759815370c4dc9c7")


settings = Settings()

