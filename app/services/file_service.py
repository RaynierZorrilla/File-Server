from fastapi import UploadFile, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple
from uuid import uuid4
from pathlib import Path

from ..models import File as FileModel
from ..schemas import FileOut
from ..repositories import FileRepository
from ..config import settings
from ..utils import ORIGINALS, THUMBS, sha256sum, image_size, make_thumbnail


class FileService:
    """Servicio para lógica de negocio de archivos"""
    
    def __init__(self, session: AsyncSession):
        self.repository = FileRepository(session)
        self.allowed_exts = settings.allowed_image_exts | settings.allowed_doc_exts | settings.allowed_video_exts
    
    async def upload_file(self, file: UploadFile, user_id: str) -> FileOut:
        """Sube un archivo y guarda sus metadatos"""
        # Validar tamaño
        blob = await file.read()
        if len(blob) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                413, 
                detail=f"Archivo supera {settings.max_file_size_mb} MB: {file.filename}"
            )
        
        # Validar extensión
        ext = Path(file.filename).suffix.lower()
        if ext not in self.allowed_exts:
            raise HTTPException(400, detail=f"Extensión no permitida: {ext}")
        
        # Calcular checksum
        csum = sha256sum(blob)
        
        # Generar UUID y nombre de almacenamiento
        file_uuid = str(uuid4())
        storage_name = f"{file_uuid}{ext}"
        path = ORIGINALS / storage_name
        
        # Guardar archivo físico
        path.write_bytes(blob)
        
        # Obtener dimensiones si es imagen
        width = height = None
        if file.content_type and file.content_type.startswith("image/"):
            width, height = image_size(path)
        
        # Crear modelo de base de datos
        new_file = FileModel(
            uuid=file_uuid,
            original_name=file.filename,
            storage_name=storage_name,
            content_type=file.content_type or "application/octet-stream",
            size=len(blob),
            ext=ext,
            checksum_sha256=csum,
            width=width,
            height=height,
            user_id=user_id,
        )
        
        # Guardar en base de datos
        try:
            created_file = await self.repository.create(new_file)
        except IntegrityError:
            # Si hay conflicto, eliminar archivo físico
            path.unlink(missing_ok=True)
            raise HTTPException(409, detail="Conflicto al guardar metadatos")
        
        return FileOut.model_validate(created_file)
    
    async def upload_files(self, files: List[UploadFile], user_id: str) -> List[FileOut]:
        """Sube múltiples archivos"""
        results = []
        for file in files:
            result = await self.upload_file(file, user_id)
            results.append(result)
        return results
    
    async def list_files(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
        q: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        ext: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[FileOut]:
        """Lista archivos del usuario con filtros"""
        files = await self.repository.list(
            user_id=user_id,
            limit=limit,
            offset=offset,
            content_type=content_type,
            q=q,
            min_size=min_size,
            max_size=max_size,
            ext=ext,
            date_from=date_from,
            date_to=date_to,
        )
        return [FileOut.model_validate(f) for f in files]
    
    async def get_file(self, file_id: int, user_id: str) -> FileOut:
        """Obtiene un archivo por ID del usuario"""
        file = await self.repository.get_by_id(file_id)
        if not file:
            raise HTTPException(404, detail="No encontrado")
        if file.user_id != user_id:
            raise HTTPException(403, detail="No tienes permiso para acceder a este archivo")
        return FileOut.model_validate(file)
    
    async def get_file_path(self, file_id: int, user_id: str) -> Tuple[Path, str, str]:
        """Obtiene la ruta del archivo físico, content type y nombre original"""
        file = await self.repository.get_by_id(file_id)
        if not file:
            raise HTTPException(404, detail="No encontrado")
        if file.user_id != user_id:
            raise HTTPException(403, detail="No tienes permiso para acceder a este archivo")
        
        path = ORIGINALS / file.storage_name
        if not path.exists():
            raise HTTPException(410, detail="Archivo eliminado")
        
        return path, file.content_type, file.original_name
    
    async def get_thumbnail_path(
        self,
        file_id: int,
        user_id: str,
        w: Optional[int] = None,
        h: Optional[int] = None,
        fit: str = "contain",
    ) -> Tuple[Path, str]:
        """Obtiene o genera la ruta del thumbnail"""
        file = await self.repository.get_by_id(file_id)
        if not file:
            raise HTTPException(404, detail="No encontrado")
        if file.user_id != user_id:
            raise HTTPException(403, detail="No tienes permiso para acceder a este archivo")
        
        if not file.content_type.startswith("image/"):
            raise HTTPException(400, detail="El archivo no es una imagen")
        
        src = ORIGINALS / file.storage_name
        if not src.exists():
            raise HTTPException(410, detail="Archivo eliminado")
        
        # Generar nombre del thumbnail
        key = f"{file.uuid}_{w or 'auto'}x{h or 'auto'}_{fit}{file.ext}"
        dst = THUMBS / key
        
        # Generar thumbnail si no existe
        if not dst.exists():
            make_thumbnail(src, dst, w, h, fit)
        
        return dst, file.content_type
    
    async def delete_file(self, file_id: int, user_id: str) -> None:
        """Elimina un archivo y sus thumbnails"""
        file = await self.repository.get_by_id(file_id)
        if not file:
            raise HTTPException(404, detail="No encontrado")
        if file.user_id != user_id:
            raise HTTPException(403, detail="No tienes permiso para eliminar este archivo")
        
        # Eliminar archivo físico
        (ORIGINALS / file.storage_name).unlink(missing_ok=True)
        
        # Eliminar thumbnails relacionados
        for p in THUMBS.glob(f"{file.uuid}_*"):
            p.unlink(missing_ok=True)
        
        # Eliminar de base de datos
        await self.repository.delete(file)

