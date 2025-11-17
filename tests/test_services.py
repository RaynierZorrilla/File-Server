"""
Tests para la capa de services
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile, HTTPException
from io import BytesIO
from PIL import Image

from app.services import FileService
from app.models import File


@pytest.fixture
def mock_upload_file():
    """Crea un mock de UploadFile"""
    def _create_mock(filename: str, content: bytes, content_type: str = "image/jpeg"):
        file = MagicMock(spec=UploadFile)
        file.filename = filename
        file.content_type = content_type
        file.read = AsyncMock(return_value=content)
        return file
    return _create_mock


@pytest.fixture
def image_bytes():
    """Crea bytes de una imagen de prueba"""
    img = Image.new("RGB", (800, 600), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_upload_file_success(test_db_session, temp_storage, mock_upload_file, image_bytes):
    """Test subir archivo exitosamente"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        with patch("app.services.file_service.THUMBS", temp_storage["thumbs"]):
            service = FileService(test_db_session)
            
            file = mock_upload_file("test.jpg", image_bytes, "image/jpeg")
            result = await service.upload_file(file)
            
            assert result.original_name == "test.jpg"
            assert result.content_type == "image/jpeg"
            assert result.size == len(image_bytes)
            assert result.width == 800
            assert result.height == 600
            assert result.uuid is not None


@pytest.mark.asyncio
async def test_upload_file_too_large(test_db_session, temp_storage, mock_upload_file):
    """Test subir archivo que excede el tamaño máximo"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        with patch("app.services.file_service.settings") as mock_settings:
            mock_settings.max_file_size_mb = 1
            mock_settings.allowed_image_exts = {".jpg"}
            mock_settings.allowed_doc_exts = set()
            mock_settings.allowed_video_exts = set()
            
            service = FileService(test_db_session)
            
            # Crear archivo grande (2MB)
            large_content = b"x" * (2 * 1024 * 1024)
            file = mock_upload_file("large.jpg", large_content)
            
            with pytest.raises(HTTPException) as exc_info:
                await service.upload_file(file)
            
            assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_upload_file_invalid_extension(test_db_session, temp_storage, mock_upload_file, image_bytes):
    """Test subir archivo con extensión no permitida"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        service = FileService(test_db_session)
        
        file = mock_upload_file("test.exe", image_bytes)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_file(file)
        
        assert exc_info.value.status_code == 400
        assert "no permitida" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_upload_files_multiple(test_db_session, temp_storage, mock_upload_file, image_bytes):
    """Test subir múltiples archivos"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        with patch("app.services.file_service.THUMBS", temp_storage["thumbs"]):
            service = FileService(test_db_session)
            
            files = [
                mock_upload_file("test1.jpg", image_bytes),
                mock_upload_file("test2.jpg", image_bytes),
            ]
            
            results = await service.upload_files(files)
            
            assert len(results) == 2
            assert results[0].original_name == "test1.jpg"
            assert results[1].original_name == "test2.jpg"


@pytest.mark.asyncio
async def test_list_files(test_db_session, sample_file_data):
    """Test listar archivos"""
    service = FileService(test_db_session)
    
    # Crear archivos de prueba
    from app.repositories import FileRepository
    repository = FileRepository(test_db_session)
    
    for i in range(3):
        data = sample_file_data.copy()
        data["uuid"] = f"test-uuid-{i}"
        data["original_name"] = f"test_{i}.jpg"
        file = File(**data)
        await repository.create(file)
    
    # Listar
    results = await service.list_files(limit=10)
    
    assert len(results) == 3


@pytest.mark.asyncio
async def test_get_file_success(test_db_session, sample_file_data):
    """Test obtener archivo existente"""
    service = FileService(test_db_session)
    
    # Crear archivo
    from app.repositories import FileRepository
    repository = FileRepository(test_db_session)
    file = File(**sample_file_data)
    created = await repository.create(file)
    
    # Obtener
    result = await service.get_file(created.id)
    
    assert result.id == created.id
    assert result.uuid == sample_file_data["uuid"]


@pytest.mark.asyncio
async def test_get_file_not_found(test_db_session):
    """Test obtener archivo inexistente"""
    service = FileService(test_db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        await service.get_file(999)
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_file_path_success(test_db_session, temp_storage, sample_file_data, image_bytes):
    """Test obtener ruta de archivo"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        service = FileService(test_db_session)
        
        # Crear archivo en BD
        from app.repositories import FileRepository
        repository = FileRepository(test_db_session)
        file = File(**sample_file_data)
        created = await repository.create(file)
        
        # Crear archivo físico
        file_path = temp_storage["originals"] / created.storage_name
        file_path.write_bytes(image_bytes)
        
        # Obtener ruta
        path, content_type, original_name = await service.get_file_path(created.id)
        
        assert path == file_path
        assert content_type == sample_file_data["content_type"]
        assert original_name == sample_file_data["original_name"]


@pytest.mark.asyncio
async def test_get_file_path_not_found(test_db_session):
    """Test obtener ruta de archivo inexistente"""
    service = FileService(test_db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        await service.get_file_path(999)
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_file_path_file_deleted(test_db_session, temp_storage, sample_file_data):
    """Test obtener ruta de archivo eliminado físicamente"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        service = FileService(test_db_session)
        
        # Crear archivo en BD pero no físicamente
        from app.repositories import FileRepository
        repository = FileRepository(test_db_session)
        file = File(**sample_file_data)
        created = await repository.create(file)
        
        # Intentar obtener ruta
        with pytest.raises(HTTPException) as exc_info:
            await service.get_file_path(created.id)
        
        assert exc_info.value.status_code == 410


@pytest.mark.asyncio
async def test_get_thumbnail_path_success(test_db_session, temp_storage, sample_file_data, image_bytes):
    """Test obtener/generar thumbnail"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        with patch("app.services.file_service.THUMBS", temp_storage["thumbs"]):
            service = FileService(test_db_session)
            
            # Crear archivo en BD
            from app.repositories import FileRepository
            repository = FileRepository(test_db_session)
            file = File(**sample_file_data)
            created = await repository.create(file)
            
            # Crear archivo físico
            file_path = temp_storage["originals"] / created.storage_name
            file_path.write_bytes(image_bytes)
            
            # Obtener thumbnail
            thumb_path, content_type = await service.get_thumbnail_path(created.id, w=200, h=200)
            
            assert thumb_path.exists()
            assert content_type == sample_file_data["content_type"]


@pytest.mark.asyncio
async def test_get_thumbnail_path_not_image(test_db_session, sample_file_data):
    """Test obtener thumbnail de archivo que no es imagen"""
    service = FileService(test_db_session)
    
    # Crear archivo que no es imagen
    from app.repositories import FileRepository
    repository = FileRepository(test_db_session)
    data = sample_file_data.copy()
    data["content_type"] = "application/pdf"
    file = File(**data)
    created = await repository.create(file)
    
    with pytest.raises(HTTPException) as exc_info:
        await service.get_thumbnail_path(created.id)
    
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_file_success(test_db_session, temp_storage, sample_file_data, image_bytes):
    """Test eliminar archivo"""
    with patch("app.services.file_service.ORIGINALS", temp_storage["originals"]):
        with patch("app.services.file_service.THUMBS", temp_storage["thumbs"]):
            service = FileService(test_db_session)
            
            # Crear archivo en BD
            from app.repositories import FileRepository
            repository = FileRepository(test_db_session)
            file = File(**sample_file_data)
            created = await repository.create(file)
            
            # Crear archivo físico
            file_path = temp_storage["originals"] / created.storage_name
            file_path.write_bytes(image_bytes)
            
            # Crear thumbnail
            thumb_path = temp_storage["thumbs"] / f"{created.uuid}_200x200_contain.jpg"
            thumb_path.write_bytes(image_bytes)
            
            # Eliminar
            await service.delete_file(created.id)
            
            # Verificar que fue eliminado de BD
            deleted = await repository.get_by_id(created.id)
            assert deleted is None
            
            # Verificar que archivo físico fue eliminado
            assert not file_path.exists()
            
            # Verificar que thumbnail fue eliminado
            assert not thumb_path.exists()

