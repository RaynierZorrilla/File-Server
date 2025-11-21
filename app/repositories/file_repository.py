from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from ..models import File as FileModel
from sqlalchemy import delete


class FileRepository:
    """Repositorio para acceso a datos de archivos"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, file: FileModel) -> FileModel:
        """Crea un nuevo archivo en la base de datos"""
        self.session.add(file)
        await self.session.commit()
        await self.session.refresh(file)
        return file
    
    async def get_by_id(self, file_id: int) -> Optional[FileModel]:
        """Obtiene un archivo por su ID"""
        return await self.session.get(FileModel, file_id)
    
    async def get_by_uuid(self, uuid: str) -> Optional[FileModel]:
        """Obtiene un archivo por su UUID"""
        stmt = select(FileModel).where(FileModel.uuid == uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(
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
    ) -> List[FileModel]:
        """Lista archivos del usuario con filtros opcionales"""
        stmt = select(FileModel).where(FileModel.user_id == user_id)
        
        if content_type:
            stmt = stmt.where(FileModel.content_type == content_type)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(FileModel.original_name.like(like))
        if min_size is not None:
            stmt = stmt.where(FileModel.size >= min_size)
        if max_size is not None:
            stmt = stmt.where(FileModel.size <= max_size)
        if ext:
            # Normalizar extensiones: puede ser una o múltiples separadas por comas
            ext_list = [e.strip() for e in ext.split(",")]
            # Agregar punto si no lo tiene y convertir a minúsculas
            ext_normalized = []
            for e in ext_list:
                if e:
                    ext_normalized.append(e if e.startswith(".") else f".{e}")
            if ext_normalized:
                # Usar IN para múltiples extensiones
                stmt = stmt.where(FileModel.ext.in_([e.lower() for e in ext_normalized]))
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                stmt = stmt.where(FileModel.created_at >= date_from_obj)
            except ValueError:
                # Si el formato es incorrecto, ignorar el filtro
                pass
        if date_to:
            try:
                # Incluir todo el día (hasta las 23:59:59)
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                # Agregar un día y restar un segundo para incluir todo el día
                from datetime import timedelta
                date_to_obj = date_to_obj + timedelta(days=1) - timedelta(seconds=1)
                stmt = stmt.where(FileModel.created_at <= date_to_obj)
            except ValueError:
                # Si el formato es incorrecto, ignorar el filtro
                pass
        
        stmt = stmt.order_by(FileModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete(self, file: FileModel) -> None:
        """Elimina un archivo de la base de datos"""
        stmt = delete(FileModel).where(FileModel.id == file.id)
        await self.session.execute(stmt)
        await self.session.commit()

