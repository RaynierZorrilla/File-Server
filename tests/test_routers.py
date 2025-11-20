"""
Tests para la capa de routers/endpoints
"""
import pytest
from httpx import AsyncClient
from io import BytesIO
from PIL import Image
from unittest.mock import AsyncMock

from app.main import app
from app.utils.security import get_current_user, get_db as security_get_db
from app.routers.files import get_db as files_get_db


@pytest.fixture
async def client(test_user, test_db_session):
    """Cliente de prueba asíncrono para FastAPI"""
    # Override get_current_user para usar el usuario de prueba directamente
    async def override_get_current_user():
        return test_user
    
    # Override get_db en security para usar la sesión de prueba
    async def override_security_get_db():
        yield test_db_session
    
    # Override get_db en files para usar la sesión de prueba
    async def override_files_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[security_get_db] = override_security_get_db
    app.dependency_overrides[files_get_db] = override_files_get_db
    
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as ac:
        yield ac
    
    # Limpiar overrides después del test
    app.dependency_overrides.clear()


@pytest.fixture
def image_bytes():
    """Crea bytes de una imagen de prueba"""
    img = Image.new("RGB", (800, 600), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test del endpoint raíz"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "name" in data


@pytest.mark.asyncio
async def test_health_check(client):
    """Test del endpoint de health check"""
    response = await client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_upload_file(client, image_bytes):
    """Test subir un archivo"""
    files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
    response = await client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["original_name"] == "test.jpg"
    assert data[0]["content_type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_upload_multiple_files(client, image_bytes):
    """Test subir múltiples archivos"""
    files = [
        ("files", ("test1.jpg", image_bytes, "image/jpeg")),
        ("files", ("test2.jpg", image_bytes, "image/jpeg")),
    ]
    response = await client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_upload_file_invalid_extension(client):
    """Test subir archivo con extensión no permitida"""
    files = {"files": ("test.exe", b"fake content", "application/x-msdownload")}
    response = await client.post("/upload", files=files)
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_files_empty(client):
    """Test listar archivos cuando no hay ninguno"""
    response = await client.get("/files")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_files_with_data(client, image_bytes):
    """Test listar archivos después de subir algunos"""
    # Subir archivo
    files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
    upload_response = await client.post("/upload", files=files)
    assert upload_response.status_code == 200
    
    # Listar
    response = await client.get("/files")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_files_with_filters(client, image_bytes):
    """Test listar archivos con filtros"""
    # Subir archivo
    files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
    await client.post("/upload", files=files)
    
    # Listar con filtro de content_type
    response = await client.get("/files?content_type=image/jpeg")
    
    assert response.status_code == 200
    data = response.json()
    assert all(item["content_type"] == "image/jpeg" for item in data)


@pytest.mark.asyncio
async def test_get_file_by_id(client, image_bytes):
    """Test obtener archivo por ID"""
    # Subir archivo
    files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
    upload_response = await client.post("/upload", files=files)
    file_id = upload_response.json()[0]["id"]
    
    # Obtener por ID
    response = await client.get(f"/files/{file_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["original_name"] == "test.jpg"


@pytest.mark.asyncio
async def test_get_file_not_found(client):
    """Test obtener archivo inexistente"""
    response = await client.get("/files/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_file(client, image_bytes):
    """Test descargar archivo"""
    # Subir archivo
    files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
    upload_response = await client.post("/upload", files=files)
    file_id = upload_response.json()[0]["id"]
    
    # Descargar
    response = await client.get(f"/files/{file_id}/download")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "test.jpg" in response.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_download_file_not_found(client):
    """Test descargar archivo inexistente"""
    response = await client.get("/files/99999/download")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_thumbnail(client, image_bytes):
    """Test obtener thumbnail"""
    # Subir archivo
    files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
    upload_response = await client.post("/upload", files=files)
    file_id = upload_response.json()[0]["id"]
    
    # Obtener thumbnail
    response = await client.get(f"/images/{file_id}/thumbnail?w=200&h=200")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_get_thumbnail_not_image(client):
    """Test obtener thumbnail de archivo que no es imagen"""
    # Esto requeriría subir un archivo que no sea imagen primero
    # Por ahora solo verificamos el endpoint
    response = await client.get("/images/99999/thumbnail")
    
    # Debería fallar porque el archivo no existe o no es imagen
    assert response.status_code in [400, 404]


@pytest.mark.asyncio
async def test_delete_file(client, image_bytes):
    """Test eliminar archivo"""
    # Subir archivo
    files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
    upload_response = await client.post("/upload", files=files)
    file_id = upload_response.json()[0]["id"]
    
    # Eliminar
    response = await client.delete(f"/files/{file_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    
    # Verificar que fue eliminado
    get_response = await client.get(f"/files/{file_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_file_not_found(client):
    """Test eliminar archivo inexistente"""
    response = await client.delete("/files/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_file_requires_auth(image_bytes):
    """Test que subir archivo requiere autenticación"""
    # Crear un cliente sin override de dependencias
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        files = {"files": ("test.jpg", image_bytes, "image/jpeg")}
        response = await client.post("/upload", files=files)
        
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_files_requires_auth():
    """Test que listar archivos requiere autenticación"""
    # Crear un cliente sin override de dependencias
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/files")
        
        assert response.status_code == 401

