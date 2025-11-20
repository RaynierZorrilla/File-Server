from fastapi import APIRouter, UploadFile, File as UpFile, Query, Depends
from fastapi.responses import FileResponse
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..services import FileService
from ..schemas import FileOut
from ..models import User
from ..utils.security import get_current_user

router = APIRouter()


async def get_db() -> AsyncSession:
    """Dependency para obtener sesión de base de datos"""
    async with async_session() as session:
        yield session


def get_file_service(session: AsyncSession = Depends(get_db)) -> FileService:
    """Dependency para obtener el servicio de archivos"""
    return FileService(session)


@router.post("/upload", response_model=List[FileOut])
async def upload(
    files: List[UploadFile] = UpFile(...),
    service: FileService = Depends(get_file_service),
    user: User = Depends(get_current_user),
):
    """Endpoint para subir uno o más archivos"""
    return await service.upload_files(files)


@router.get("/files", response_model=List[FileOut])
async def list_files(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    content_type: Optional[str] = None,
    q: Optional[str] = None,
    min_size: Optional[int] = Query(None, ge=0),
    max_size: Optional[int] = Query(None, ge=0),
    service: FileService = Depends(get_file_service),
    user: User = Depends(get_current_user),
):
    """Endpoint para listar archivos con filtros opcionales"""
    return await service.list_files(
        limit=limit,
        offset=offset,
        content_type=content_type,
        q=q,
        min_size=min_size,
        max_size=max_size,
    )


@router.get("/files/{file_id}", response_model=FileOut)
async def get_file(
    file_id: int,
    service: FileService = Depends(get_file_service),
    user: User = Depends(get_current_user),
):
    """Endpoint para obtener un archivo por ID"""
    return await service.get_file(file_id)


@router.get("/files/{file_id}/download")
async def download(
    file_id: int,
    service: FileService = Depends(get_file_service),
    user: User = Depends(get_current_user),
):
    """Endpoint para descargar un archivo"""
    path, content_type, original_name = await service.get_file_path(file_id)
    return FileResponse(
        path,
        media_type=content_type,
        filename=original_name
    )


@router.get("/images/{file_id}/thumbnail")
async def thumbnail(
    file_id: int,
    w: Optional[int] = Query(None, ge=1, le=4000),
    h: Optional[int] = Query(None, ge=1, le=4000),
    fit: str = Query("contain", pattern="^(contain|crop)$"),
    service: FileService = Depends(get_file_service),
    user: User = Depends(get_current_user),
):
    """Endpoint para obtener o generar un thumbnail de una imagen"""
    path, content_type = await service.get_thumbnail_path(file_id, w, h, fit)
    return FileResponse(path, media_type=content_type)


@router.delete("/files/{file_id}")
async def delete(
    file_id: int,
    service: FileService = Depends(get_file_service),
    user: User = Depends(get_current_user),
):
    """Endpoint para eliminar un archivo"""
    await service.delete_file(file_id)
    return {"ok": True}