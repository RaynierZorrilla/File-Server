from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import files as files_router
from .database import init_db
from .config import settings

app = FastAPI(title=settings.app_name)

cors_origins_list = settings.cors_origins
use_credentials = "*" not in cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=use_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(files_router.router)

@app.get("/")
async def root():
    return {"status": "ok", "name": settings.app_name}