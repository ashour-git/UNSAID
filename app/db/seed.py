from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


FragranceSeed = dict[str, Any]


FLAGSHIP_FRAGRANCES: tuple[FragranceSeed, ...] = (
    {
        "name": "Unsaid : Apex",
        "subtitle": "The summit of quiet dominance",
        "concentration": "Extrait de Parfum",
        "volume": "30ml",
        "description": (
            "Apex opens with luminous bergamot and saffron before revealing "
            "a sculpted heart of orris and rose over oud and ambergris."
        ),
        "olfactory_notes": {
            "top": ["Bergamot", "Saffron", "Pink Pepper"],
            "heart": ["Orris", "Damask Rose", "Violet Leaf"],
            "base": ["Oud", "Ambergris", "Cashmere Woods"],
        },
        "price": Decimal("245.00"),
        "stock": 42,
        "image_url": "/static/images/fragrances/unsaid-apex.svg",
        "dynamic_slug": "unsaid-apex",
    },
    {
        "name": "Unsaid : Chapter I",
        "subtitle": "The first page of a lasting signature",
        "concentration": "Extrait de Parfum",
        "volume": "30ml",
        "description": (
            "Chapter I pairs polished citrus and black tea with an intimate "
            "iris and jasmine heart, settling into sandalwood and musk."
        ),
        "olfactory_notes": {
            "top": ["Italian Citrus", "Black Tea", "Cardamom"],
            "heart": ["Iris", "Jasmine Sambac", "Cedar Leaf"],
            "base": ["Sandalwood", "White Musk", "Ambrette"],
        },
        "price": Decimal("225.00"),
        "stock": 58,
        "image_url": "/static/images/fragrances/unsaid-chapter-i.svg",
        "dynamic_slug": "unsaid-chapter-i",
    },
    {
        "name": "Unsaid : Pulse",
        "subtitle": "Electric warmth beneath tailored restraint",
        "concentration": "Extrait de Parfum",
        "volume": "30ml",
        "description": (
            "Pulse cuts through the air with grapefruit and pink pepper, "
            "then warms into geranium, cardamom, vetiver, and cedar."
        ),
        "olfactory_notes": {
            "top": ["Pink Pepper", "Grapefruit", "Juniper"],
            "heart": ["Geranium", "Cardamom", "Clary Sage"],
            "base": ["Vetiver", "Cedar", "Mineral Amber"],
        },
        "price": Decimal("215.00"),
        "stock": 64,
        "image_url": "/static/images/fragrances/unsaid-pulse.svg",
        "dynamic_slug": "unsaid-pulse",
    },
    {
        "name": "Unsaid : Aura",
        "subtitle": "Radiance held close to the skin",
        "concentration": "Extrait de Parfum",
        "volume": "30ml",
        "description": (
            "Aura floats from pear and mandarin into tuberose and ylang, "
            "finishing with vanilla, white musk, and soft woods."
        ),
        "olfactory_notes": {
            "top": ["Pear", "Mandarin", "Neroli"],
            "heart": ["Tuberose", "Ylang-Ylang", "Orange Blossom"],
            "base": ["Vanilla", "White Musk", "Blonde Woods"],
        },
        "price": Decimal("235.00"),
        "stock": 37,
        "image_url": "/static/images/fragrances/unsaid-aura.svg",
        "dynamic_slug": "unsaid-aura",
    },
    {
        "name": "Unsaid : Echo",
        "subtitle": "A smoky trace that refuses to fade",
        "concentration": "Extrait de Parfum",
        "volume": "30ml",
        "description": (
            "Echo moves through incense and cypress into violet leaf and "
            "labdanum, leaving patchouli and smoked woods in its wake."
        ),
        "olfactory_notes": {
            "top": ["Incense", "Cypress", "Black Pepper"],
            "heart": ["Violet Leaf", "Labdanum", "Clove Bud"],
            "base": ["Patchouli", "Smoked Woods", "Amber Resin"],
        },
        "price": Decimal("240.00"),
        "stock": 31,
        "image_url": "/static/images/fragrances/unsaid-echo.svg",
        "dynamic_slug": "unsaid-echo",
    },
    {
        "name": "Unsaid : Velvet",
        "subtitle": "Texture, warmth, and after-dark elegance",
        "concentration": "Extrait de Parfum",
        "volume": "30ml",
        "description": (
            "Velvet drapes plum and saffron over rose and suede, then melts "
            "into tonka, amber, and vanilla for a plush final impression."
        ),
        "olfactory_notes": {
            "top": ["Plum", "Saffron", "Cinnamon Bark"],
            "heart": ["Rose", "Suede", "Heliotrope"],
            "base": ["Tonka Bean", "Amber", "Vanilla"],
        },
        "price": Decimal("250.00"),
        "stock": 29,
        "image_url": "/static/images/fragrances/unsaid-velvet.svg",
        "dynamic_slug": "unsaid-velvet",
    },
)


async def seed_flagship_fragrances(session: AsyncSession) -> None:
    result = await session.execute(select(Product))
    existing_products = {product.dynamic_slug: product for product in result.scalars().all()}

    for fragrance in FLAGSHIP_FRAGRANCES:
        slug = fragrance["dynamic_slug"]
        existing = existing_products.get(slug)
        if existing is None:
            session.add(Product(**fragrance))
            continue

        existing.name = str(fragrance["name"])
        existing.subtitle = str(fragrance["subtitle"])
        existing.concentration = str(fragrance["concentration"])
        existing.volume = str(fragrance["volume"])
        existing.description = str(fragrance["description"])
        existing.olfactory_notes = dict(fragrance["olfactory_notes"])
        existing.price = Decimal(str(fragrance["price"]))
        existing.stock = int(fragrance["stock"])
        existing.image_url = str(fragrance["image_url"])

    await session.commit()
