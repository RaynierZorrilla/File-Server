"""
Configuración global de pytest y fixtures compartidas
"""
import pytest
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.models import File
from app.config import Settings


# Configuración de pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Crea un event loop para toda la sesión de tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Configuración de prueba"""
    return Settings(
        app_name="Test Files API",
        max_file_size_mb=10,
        allowed_image_exts={".jpg", ".jpeg", ".png", ".webp", ".gif"},
        allowed_doc_exts={".pdf", ".txt", ".csv"},
        allowed_video_exts={".mp4", ".webm"},
        database_url="sqlite+aiosqlite:///:memory:",
        force_https=False,
        cors_origins=["*"],
    )


@pytest.fixture
async def test_db_session(test_settings):
    """Crea una sesión de base de datos en memoria para tests"""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        future=True
    )
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Crear sesión
    async with async_session() as session:
        yield session
    
    # Limpiar
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def temp_storage(tmp_path):
    """Crea directorios temporales para almacenamiento"""
    originals = tmp_path / "originals"
    thumbs = tmp_path / "thumbs"
    originals.mkdir(parents=True, exist_ok=True)
    thumbs.mkdir(parents=True, exist_ok=True)
    return {
        "originals": originals,
        "thumbs": thumbs,
        "storage": tmp_path,
    }


@pytest.fixture
def sample_file_data():
    """Datos de ejemplo para un archivo"""
    return {
        "uuid": "test-uuid-123",
        "original_name": "test.jpg",
        "storage_name": "test-uuid-123.jpg",
        "content_type": "image/jpeg",
        "size": 1024,
        "ext": ".jpg",
        "checksum_sha256": "a" * 64,
        "width": 800,
        "height": 600,
    }

