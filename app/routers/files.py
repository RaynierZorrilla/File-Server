from fastapi import APIRouter, UploadFile, File as UpFile, HTTPException, Query
from fastapi import Response
from fastapi.responses import FileResponse
from typing import List, Optional
from uuid import uuid4
from pathlib import Path
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import async_session
from ..models import File as FileModel
from ..schemas import FileOut
from ..config import settings
from ..utils import ORIGINALS, THUMBS, sha256sum, image_size, make_thumbnail

router = APIRouter()

ALLOWED_EXTS = settings.allowed_image_exts | settings.allowed_doc_exts | settings.allowed_video_exts

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/upload", response_model=List[FileOut])
async def upload(files: List[UploadFile] = UpFile(...)):
    results: list[FileOut] = []
    for f in files:
        # límite de tamaño: usamos Content-Length si viene en chunks; acá leemos todo a memoria por simplicidad
        blob = await f.read()
        if len(blob) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(413, detail=f"Archivo supera {settings.max_file_size_mb} MB: {f.filename}")

        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(400, detail=f"Extensión no permitida: {ext}")

        csum = sha256sum(blob)
        file_uuid = str(uuid4())
        storage_name = f"{file_uuid}{ext}"
        path = ORIGINALS / storage_name
        path.write_bytes(blob)

        width = height = None
        if f.content_type.startswith("image/"):
            width, height = image_size(path)

        new_file = FileModel(
            uuid=file_uuid,
            original_name=f.filename,
            storage_name=storage_name,
            content_type=f.content_type or "application/octet-stream",
            size=len(blob),
            ext=ext,
            checksum_sha256=csum,
            width=width,
            height=height,
        )
        async with async_session() as session:
            session.add(new_file)
            try:
                await session.commit()
                await session.refresh(new_file)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(409, detail="Conflicto al guardar metadatos")
        results.append(FileOut.model_validate(new_file))
    return results

@router.get("/files", response_model=List[FileOut])
async def list_files(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    content_type: Optional[str] = None,
    q: Optional[str] = None,
    min_size: Optional[int] = Query(None, ge=0),
    max_size: Optional[int] = Query(None, ge=0),
):
    async with async_session() as session:
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
        result = await session.execute(stmt)
        res = result.scalars().all()
        return [FileOut.model_validate(x) for x in res]

@router.get("/files/{file_id}", response_model=FileOut)
async def get_file(file_id: int):
    async with async_session() as session:
        obj = await session.get(FileModel, file_id)
        if not obj:
            raise HTTPException(404, detail="No encontrado")
        return FileOut.model_validate(obj)

 

@router.get("/files/{file_id}/download")
async def download(file_id: int):
    async with async_session() as session:
        obj = await session.get(FileModel, file_id)
        if not obj:
            raise HTTPException(404, detail="No encontrado")
        path = ORIGINALS / obj.storage_name
        if not path.exists():
            raise HTTPException(410, detail="Archivo eliminado")
        return FileResponse(path, media_type=obj.content_type, filename=obj.original_name)

@router.get("/images/{file_id}/thumbnail")
async def thumbnail(
    file_id: int,
    w: Optional[int] = Query(None, ge=1, le=4000),
    h: Optional[int] = Query(None, ge=1, le=4000),
    fit: str = Query("contain", pattern="^(contain|crop)$"),
):
    async with async_session() as session:
        obj = await session.get(FileModel, file_id)
        if not obj:
            raise HTTPException(404, detail="No encontrado")
        if not obj.content_type.startswith("image/"):
            raise HTTPException(400, detail="El archivo no es una imagen")
        src = ORIGINALS / obj.storage_name
        if not src.exists():
            raise HTTPException(410, detail="Archivo eliminado")
        key = f"{obj.uuid}_{w or 'auto'}x{h or 'auto'}_{fit}{obj.ext}"
        dst = THUMBS / key
        if not dst.exists():
            make_thumbnail(src, dst, w, h, fit)
        return FileResponse(dst, media_type=obj.content_type)

@router.delete("/files/{file_id}")
async def delete(file_id: int):
    async with async_session() as session:
        obj = await session.get(FileModel, file_id)
        if not obj:
            raise HTTPException(404, detail="No encontrado")
        # eliminar archivos físicos
        (ORIGINALS / obj.storage_name).unlink(missing_ok=True)
        # thumbs relacionadas
        for p in THUMBS.glob(f"{obj.uuid}_*"):
            p.unlink(missing_ok=True)
        await session.delete(obj)
        await session.commit()
        return {"ok": True}