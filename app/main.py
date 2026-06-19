from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.knowledge_seed import seed_knowledge_documents
from app.db.seed import seed_flagship_fragrances
from app.db.session import AsyncSessionLocal, engine, init_db
from app.routers.chat import router as chat_router
from app.routers.orders import router as orders_router
from app.routers.pages import router as pages_router
from app.routers.products import router as products_router
from app.routers.quiz import router as quiz_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_flagship_fragrances(session)
        await seed_knowledge_documents(session)

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend commerce foundation for UNSAID, an ultra-premium "
        "extrait de parfum house."
    ),
    version="0.1.0",
    contact={"name": "UNSAID"},
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=settings.static_dir),
    name="static",
)
app.mount(
    "/img",
    StaticFiles(directory=settings.campaign_img_dir),
    name="campaign_images",
)

app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router)
app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(pages_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    database_status = "healthy"

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"

    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "status": "healthy" if database_status == "healthy" else "degraded",
        "database": database_status,
    }
