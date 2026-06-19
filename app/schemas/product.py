from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OlfactoryNotes(BaseModel):
    top: list[str] = Field(default_factory=list)
    heart: list[str] = Field(default_factory=list)
    base: list[str] = Field(default_factory=list)


class ProductBase(BaseModel):
    name: str
    subtitle: str
    concentration: str
    volume: str
    description: str
    olfactory_notes: OlfactoryNotes
    price: Decimal
    stock: int
    image_url: str
    dynamic_slug: str


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: list[ProductRead]
    count: int
