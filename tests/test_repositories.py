"""
Tests para la capa de repositories
"""
import pytest
from app.repositories import FileRepository
from app.models import File


@pytest.mark.asyncio
async def test_create_file(test_db_session, sample_file_data):
    """Test crear un archivo"""
    repository = FileRepository(test_db_session)
    
    file = File(**sample_file_data)
    created_file = await repository.create(file)
    
    assert created_file.id is not None
    assert created_file.uuid == sample_file_data["uuid"]
    assert created_file.original_name == sample_file_data["original_name"]


@pytest.mark.asyncio
async def test_get_by_id(test_db_session, sample_file_data):
    """Test obtener archivo por ID"""
    repository = FileRepository(test_db_session)
    
    # Crear archivo
    file = File(**sample_file_data)
    created_file = await repository.create(file)
    
    # Obtener por ID
    retrieved_file = await repository.get_by_id(created_file.id)
    
    assert retrieved_file is not None
    assert retrieved_file.id == created_file.id
    assert retrieved_file.uuid == sample_file_data["uuid"]


@pytest.mark.asyncio
async def test_get_by_id_not_found(test_db_session):
    """Test obtener archivo inexistente"""
    repository = FileRepository(test_db_session)
    
    result = await repository.get_by_id(999)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_by_uuid(test_db_session, sample_file_data):
    """Test obtener archivo por UUID"""
    repository = FileRepository(test_db_session)
    
    # Crear archivo
    file = File(**sample_file_data)
    created_file = await repository.create(file)
    
    # Obtener por UUID
    retrieved_file = await repository.get_by_uuid(sample_file_data["uuid"])
    
    assert retrieved_file is not None
    assert retrieved_file.uuid == sample_file_data["uuid"]


@pytest.mark.asyncio
async def test_list_files(test_db_session, sample_file_data, test_user_id):
    """Test listar archivos"""
    repository = FileRepository(test_db_session)
    
    # Crear múltiples archivos
    for i in range(5):
        data = sample_file_data.copy()
        data["uuid"] = f"test-uuid-{i}"
        data["original_name"] = f"test_{i}.jpg"
        file = File(**data)
        await repository.create(file)
    
    # Listar todos
    files = await repository.list(user_id=test_user_id, limit=10)
    
    assert len(files) == 5


@pytest.mark.asyncio
async def test_list_files_with_limit(test_db_session, sample_file_data, test_user_id):
    """Test listar archivos con límite"""
    repository = FileRepository(test_db_session)
    
    # Crear múltiples archivos
    for i in range(5):
        data = sample_file_data.copy()
        data["uuid"] = f"test-uuid-{i}"
        file = File(**data)
        await repository.create(file)
    
    # Listar con límite
    files = await repository.list(user_id=test_user_id, limit=3)
    
    assert len(files) == 3


@pytest.mark.asyncio
async def test_list_files_with_offset(test_db_session, sample_file_data, test_user_id):
    """Test listar archivos con offset"""
    repository = FileRepository(test_db_session)
    
    # Crear múltiples archivos
    for i in range(5):
        data = sample_file_data.copy()
        data["uuid"] = f"test-uuid-{i}"
        file = File(**data)
        await repository.create(file)
    
    # Listar con offset
    files = await repository.list(user_id=test_user_id, limit=10, offset=2)
    
    assert len(files) == 3


@pytest.mark.asyncio
async def test_list_files_filter_by_content_type(test_db_session, sample_file_data, test_user_id):
    """Test filtrar archivos por content_type"""
    repository = FileRepository(test_db_session)
    
    # Crear archivos con diferentes content_types
    data1 = sample_file_data.copy()
    data1["uuid"] = "test-1"
    data1["content_type"] = "image/jpeg"
    file1 = File(**data1)
    await repository.create(file1)
    
    data2 = sample_file_data.copy()
    data2["uuid"] = "test-2"
    data2["content_type"] = "application/pdf"
    file2 = File(**data2)
    await repository.create(file2)
    
    # Filtrar por content_type
    files = await repository.list(user_id=test_user_id, content_type="image/jpeg")
    
    assert len(files) == 1
    assert files[0].content_type == "image/jpeg"


@pytest.mark.asyncio
async def test_list_files_search_by_name(test_db_session, sample_file_data, test_user_id):
    """Test buscar archivos por nombre"""
    repository = FileRepository(test_db_session)
    
    # Crear archivos con diferentes nombres
    data1 = sample_file_data.copy()
    data1["uuid"] = "test-1"
    data1["original_name"] = "photo.jpg"
    file1 = File(**data1)
    await repository.create(file1)
    
    data2 = sample_file_data.copy()
    data2["uuid"] = "test-2"
    data2["original_name"] = "document.pdf"
    file2 = File(**data2)
    await repository.create(file2)
    
    # Buscar por nombre
    files = await repository.list(user_id=test_user_id, q="photo")
    
    assert len(files) == 1
    assert "photo" in files[0].original_name.lower()


@pytest.mark.asyncio
async def test_list_files_filter_by_size(test_db_session, sample_file_data, test_user_id):
    """Test filtrar archivos por tamaño"""
    repository = FileRepository(test_db_session)
    
    # Crear archivos con diferentes tamaños
    for size in [100, 500, 1000, 2000]:
        data = sample_file_data.copy()
        data["uuid"] = f"test-{size}"
        data["size"] = size
        file = File(**data)
        await repository.create(file)
    
    # Filtrar por tamaño mínimo
    files = await repository.list(user_id=test_user_id, min_size=1000)
    assert len(files) == 2
    
    # Filtrar por tamaño máximo
    files = await repository.list(user_id=test_user_id, max_size=500)
    assert len(files) == 2
    
    # Filtrar por rango
    files = await repository.list(user_id=test_user_id, min_size=500, max_size=1500)
    assert len(files) == 2


@pytest.mark.asyncio
async def test_delete_file(test_db_session, sample_file_data):
    """Test eliminar archivo"""
    repository = FileRepository(test_db_session)
    
    # Crear archivo
    file = File(**sample_file_data)
    created_file = await repository.create(file)
    file_id = created_file.id
    
    # Eliminar
    await repository.delete(created_file)
    
    # Verificar que fue eliminado
    deleted_file = await repository.get_by_id(file_id)
    assert deleted_file is None

