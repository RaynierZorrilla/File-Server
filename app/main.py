from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import files as files_router
from .db import init_db
from .config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(files_router.router)

@app.get("/")
async def root():
    return {"status": "ok", "name": settings.app_name}