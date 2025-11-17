from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models import File as FileModel


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
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
        q: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> List[FileModel]:
        """Lista archivos con filtros opcionales"""
        stmt = select(FileModel)
        
        if content_type:
            stmt = stmt.where(FileModel.content_type == content_type)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(FileModel.original_name.like(like))
        if min_size is not None:
            stmt = stmt.where(FileModel.size >= min_size)
        if max_size is not None:
            stmt = stmt.where(FileModel.size <= max_size)
        
        stmt = stmt.order_by(FileModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete(self, file: FileModel) -> None:
        """Elimina un archivo de la base de datos"""
        await self.session.delete(file)
        await self.session.commit()

