import asyncio

from app.db.knowledge_seed import seed_knowledge_documents
from app.db.seed import seed_flagship_fragrances
from app.db.session import AsyncSessionLocal, init_db
from app.main import create_app
from app.services.auth import seed_admin_user

# Vercel's Python runtime imports this ASGI app as the serverless entrypoint.
# Vercel does not reliably run FastAPI lifespan startup for this deployment mode,
# so database setup is performed lazily on the first request in each warm worker.
app = create_app(enable_lifespan=False)

_initialized = False
_init_lock = asyncio.Lock()


async def ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return

    async with _init_lock:
        if _initialized:
            return
        await init_db()
        async with AsyncSessionLocal() as session:
            await seed_flagship_fragrances(session)
            await seed_knowledge_documents(session)
            await seed_admin_user(session)
        _initialized = True


@app.middleware("http")
async def vercel_lazy_startup(request, call_next):
    await ensure_initialized()
    return await call_next(request)
