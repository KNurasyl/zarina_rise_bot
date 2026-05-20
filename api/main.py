from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.db import init_db
from api.routers import (
    admin,
    compliments,
    dashboard,
    export,
    focus,
    health,
    journal,
    me,
    mood,
    pause,
    progress,
    settings,
    today,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Zarina Rise API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://0.0.0.0",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(today.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(focus.router, prefix="/api")
app.include_router(mood.router, prefix="/api")
app.include_router(journal.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(pause.router, prefix="/api")
app.include_router(compliments.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
