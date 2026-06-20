from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def _sync_sqlite_schema(connection) -> None:
    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    product_columns = await connection.execute(text("PRAGMA table_info(products)"))
    existing_columns = {row[1] for row in product_columns}
    missing_product_columns = {
        "compare_at_price": "NUMERIC(10, 2)",
        "is_active": "BOOLEAN NOT NULL DEFAULT 1",
        "meta_title": "VARCHAR(160) NOT NULL DEFAULT ''",
        "meta_description": "VARCHAR(320) NOT NULL DEFAULT ''",
        "gallery_images": "JSON NOT NULL DEFAULT '[]'",
    }

    for column_name, column_definition in missing_product_columns.items():
        if column_name not in existing_columns:
            await connection.execute(
                text(f"ALTER TABLE products ADD COLUMN {column_name} {column_definition}")
            )

    await connection.execute(
        text("CREATE INDEX IF NOT EXISTS ix_products_is_active ON products(is_active)")
    )
    await connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS product_options (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id),
                volume VARCHAR(20) NOT NULL,
                price NUMERIC(10,2) NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                is_default BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
            """
        )
    )
    await connection.execute(
        text("CREATE INDEX IF NOT EXISTS ix_product_options_id ON product_options(id)")
    )
    await connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_product_options_product_id "
            "ON product_options(product_id)"
        )
    )


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await _sync_sqlite_schema(connection)
