from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileOut(BaseModel):
    """Modelo de respuesta para información de archivo"""
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


class FileListQuery(BaseModel):
    """Modelo de query parameters para listar archivos"""
    limit: int = Field(20, ge=1, le=100, description="Número máximo de resultados")
    offset: int = Field(0, ge=0, description="Número de resultados a saltar")
    content_type: Optional[str] = Field(None, description="Filtrar por tipo de contenido")
    q: Optional[str] = Field(None, description="Buscar en nombre de archivo")
    min_size: Optional[int] = Field(None, ge=0, description="Tamaño mínimo en bytes")
    max_size: Optional[int] = Field(None, ge=0, description="Tamaño máximo en bytes")


class ThumbnailQuery(BaseModel):
    """Modelo de query parameters para thumbnails"""
    w: Optional[int] = Field(None, ge=1, le=4000, description="Ancho del thumbnail")
    h: Optional[int] = Field(None, ge=1, le=4000, description="Alto del thumbnail")
    fit: str = Field("contain", pattern="^(contain|crop)$", description="Modo de ajuste: contain o crop")


class DeleteResponse(BaseModel):
    """Modelo de respuesta para eliminación"""
    ok: bool = True

