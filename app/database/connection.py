from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..config import settings
# Importar modelos para que SQLModel.metadata los registre
from ..models import File, User  # noqa: F401

# Configuración del engine con parámetros específicos para SQLite async
connect_args = {}
if "sqlite" in settings.database_url:
    # Para aiosqlite, no necesitamos check_same_thread, pero podemos agregar otros parámetros
    connect_args = {"timeout": 20.0}  # Timeout para operaciones de escritura

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verifica que las conexiones estén activas antes de usarlas
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

