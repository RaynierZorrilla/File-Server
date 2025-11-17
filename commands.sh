#!/bin/bash

# =============================================================================
# Comandos útiles para el backend Files Server
# =============================================================================
# Uso: source commands.sh o ./commands.sh [comando]
# =============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Comandos disponibles:${NC}"
    echo ""
    echo -e "${GREEN}Setup:${NC}"
    echo "  setup          - Crear entorno virtual e instalar dependencias"
    echo "  install        - Instalar dependencias"
    echo "  freeze         - Congelar dependencias actuales"
    echo ""
    echo -e "${GREEN}Servidor:${NC}"
    echo "  run            - Ejecutar servidor de desarrollo"
    echo "  run-prod       - Ejecutar servidor en modo producción"
    echo "  run-reload     - Ejecutar servidor con auto-reload"
    echo ""
    echo -e "${GREEN}Tests:${NC}"
    echo "  test           - Ejecutar todos los tests"
    echo "  test-cov       - Ejecutar tests con cobertura"
    echo "  test-watch     - Ejecutar tests en modo watch"
    echo "  test-file FILE - Ejecutar un archivo de test específico"
    echo ""
    echo -e "${GREEN}Linting/Formateo:${NC}"
    echo "  lint           - Ejecutar linter"
    echo "  format         - Formatear código"
    echo "  check          - Verificar formato sin cambiar"
    echo ""
    echo -e "${GREEN}Base de datos:${NC}"
    echo "  db-init        - Inicializar base de datos"
    echo "  db-reset       - Resetear base de datos"
    echo ""
    echo -e "${GREEN}Utilidades:${NC}"
    echo "  clean          - Limpiar archivos temporales (__pycache__, .pyc, etc)"
    echo "  clean-all      - Limpiar todo incluyendo .venv y storage"
    echo "  shell          - Abrir shell de Python con app cargada"
    echo ""
}

# Setup
setup() {
    echo -e "${GREEN}Creando entorno virtual...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}Activando entorno virtual...${NC}"
    source .venv/bin/activate
    echo -e "${GREEN}Instalando dependencias...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Setup completado${NC}"
}

install() {
    echo -e "${GREEN}Instalando dependencias...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencias instaladas${NC}"
}

freeze() {
    echo -e "${GREEN}Congelando dependencias...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    pip freeze > requirements-frozen.txt
    echo -e "${GREEN}✓ Dependencias congeladas en requirements-frozen.txt${NC}"
}

# Servidor
run() {
    echo -e "${GREEN}Iniciando servidor de desarrollo...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    uvicorn app.main:app --host 0.0.0.0 --port 8000
}

run-prod() {
    echo -e "${GREEN}Iniciando servidor en modo producción...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log
}

run-reload() {
    echo -e "${GREEN}Iniciando servidor con auto-reload...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Tests
test() {
    echo -e "${GREEN}Ejecutando tests...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    pytest -v
}

test-cov() {
    echo -e "${GREEN}Ejecutando tests con cobertura...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    pytest --cov=app --cov-report=term-missing --cov-report=html -v
    echo -e "${GREEN}✓ Reporte de cobertura generado en htmlcov/index.html${NC}"
}

test-watch() {
    echo -e "${GREEN}Ejecutando tests en modo watch...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    pytest-watch || pytest --looponfail
}

test-file() {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Especifica un archivo de test${NC}"
        echo "Uso: test-file tests/test_repositories.py"
        return 1
    fi
    echo -e "${GREEN}Ejecutando test: $1${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    pytest -v "$1"
}

# Linting/Formateo
lint() {
    echo -e "${GREEN}Ejecutando linter...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    # Si tienes flake8, pylint, etc.
    if command -v flake8 &> /dev/null; then
        flake8 app tests
    elif command -v pylint &> /dev/null; then
        pylint app tests
    else
        echo -e "${YELLOW}No se encontró linter instalado. Instala flake8 o pylint.${NC}"
    fi
}

format() {
    echo -e "${GREEN}Formateando código...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    # Si tienes black
    if command -v black &> /dev/null; then
        black app tests
        echo -e "${GREEN}✓ Código formateado${NC}"
    else
        echo -e "${YELLOW}Black no está instalado. Instálalo con: pip install black${NC}"
    fi
}

check() {
    echo -e "${GREEN}Verificando formato...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    # Si tienes black
    if command -v black &> /dev/null; then
        black --check app tests
    else
        echo -e "${YELLOW}Black no está instalado. Instálalo con: pip install black${NC}"
    fi
}

# Base de datos
db-init() {
    echo -e "${GREEN}Inicializando base de datos...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
    echo -e "${GREEN}✓ Base de datos inicializada${NC}"
}

db-reset() {
    echo -e "${YELLOW}¿Estás seguro de resetear la base de datos? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${GREEN}Eliminando base de datos...${NC}"
        rm -f storage/meta.db
        db-init
        echo -e "${GREEN}✓ Base de datos reseteada${NC}"
    else
        echo -e "${YELLOW}Operación cancelada${NC}"
    fi
}

# Utilidades
clean() {
    echo -e "${GREEN}Limpiando archivos temporales...${NC}"
    find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete 2>/dev/null
    find . -type f -name "*.pyo" -delete 2>/dev/null
    find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null
    find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null
    find . -type d -name ".coverage" -exec rm -r {} + 2>/dev/null
    find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null
    echo -e "${GREEN}✓ Limpieza completada${NC}"
}

clean-all() {
    echo -e "${YELLOW}¿Estás seguro de limpiar TODO incluyendo .venv y storage? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        clean
        rm -rf .venv
        rm -rf storage/originals/*
        rm -rf storage/thumbs/*
        echo -e "${GREEN}✓ Limpieza completa realizada${NC}"
    else
        echo -e "${YELLOW}Operación cancelada${NC}"
    fi
}

shell() {
    echo -e "${GREEN}Abriendo shell de Python...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    python -i -c "
from app.main import app
from app.database import async_session, init_db
from app.models import File
from app.services import FileService
from app.repositories import FileRepository
print('App cargada. Variables disponibles:')
print('  - app: FastAPI app')
print('  - async_session: Sesión de BD')
print('  - File: Modelo de archivo')
print('  - FileService: Servicio de archivos')
print('  - FileRepository: Repositorio de archivos')
"
}

# Ejecutar comando si se pasa como argumento
if [ $# -gt 0 ]; then
    case "$1" in
        setup|install|freeze|run|run-prod|run-reload|test|test-cov|test-watch|test-file|lint|format|check|db-init|db-reset|clean|clean-all|shell)
            "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Comando desconocido: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
else
    show_help
fi

