# Tests

Este proyecto usa `pytest` para testing. La estructura de tests está organizada por capas.

## Estructura

```
tests/
├── __init__.py
├── conftest.py              # Configuración global y fixtures
├── test_repositories.py     # Tests de la capa de acceso a datos
├── test_services.py         # Tests de la capa de lógica de negocio
├── test_routers.py          # Tests de endpoints HTTP
└── test_utils.py            # Tests de utilidades
```

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con cobertura
pytest --cov=app --cov-report=html

# Ejecutar un archivo específico
pytest tests/test_repositories.py

# Ejecutar un test específico
pytest tests/test_repositories.py::test_create_file

# Ejecutar con verbose
pytest -v
```

## Configuración

La configuración de pytest está en `pytest.ini`:
- Tests asíncronos configurados automáticamente
- Cobertura de código habilitada
- Reportes en terminal y HTML

## Fixtures disponibles

- `test_db_session`: Sesión de base de datos en memoria para tests
- `temp_storage`: Directorios temporales para almacenamiento
- `sample_file_data`: Datos de ejemplo para archivos
- `client`: Cliente HTTP asíncrono para tests de endpoints
- `image_bytes`: Bytes de una imagen de prueba

## Escribir nuevos tests

1. **Tests de Repository**: Usar `test_db_session` fixture
2. **Tests de Service**: Usar `test_db_session` y `temp_storage` fixtures
3. **Tests de Router**: Usar `client` fixture (async)
4. **Tests de Utils**: Usar `tmp_path` fixture de pytest

Ejemplo:

```python
@pytest.mark.asyncio
async def test_my_feature(test_db_session):
    # Tu test aquí
    pass
```

