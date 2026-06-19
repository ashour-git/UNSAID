from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    """Catalog product for UNSAID flagship fragrances."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(180), nullable=False)
    concentration: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="Extrait de Parfum",
    )
    volume: Mapped[str] = mapped_column(String(20), nullable=False, default="30ml")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    olfactory_notes: Mapped[dict[str, list[str]]] = mapped_column(
        JSON,
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    dynamic_slug: Mapped[str] = mapped_column(
        String(140),
        nullable=False,
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
