from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument

KNOWLEDGE_DOCUMENTS: tuple[dict[str, object], ...] = (
    {
        "document_key": "fragrance-apex",
        "title": "Unsaid : Apex",
        "category": "fragrance",
        "tags": ["apex", "oud", "ambergris", "saffron", "commanding", "formal", "evening"],
        "content": "Apex opens with bergamot, saffron, and pink pepper; moves into orris, Damask rose, and violet leaf; and settles into oud, ambergris, and cashmere woods. It is the most architectural and commanding UNSAID composition, suited to formal evenings, leadership settings, and customers who want presence without loudness.",
    },
    {
        "document_key": "fragrance-chapter-i",
        "title": "Unsaid : Chapter I",
        "category": "fragrance",
        "tags": ["chapter", "citrus", "tea", "iris", "sandalwood", "office", "signature"],
        "content": "Chapter I opens with Italian citrus, black tea, and cardamom; moves into iris, jasmine sambac, and cedar leaf; and settles into sandalwood, white musk, and ambrette. It is polished, intimate, and highly wearable as a refined daily signature for professional settings or first impressions.",
    },
    {
        "document_key": "fragrance-pulse",
        "title": "Unsaid : Pulse",
        "category": "fragrance",
        "tags": ["pulse", "fresh", "grapefruit", "vetiver", "cedar", "daytime", "office"],
        "content": "Pulse opens with pink pepper, grapefruit, and juniper; moves into geranium, cardamom, and clary sage; and settles into vetiver, cedar, and mineral amber. It is electric, fresh, precise, and ideal for daytime performance, office wear, and customers who want clarity with controlled energy.",
    },
    {
        "document_key": "fragrance-aura",
        "title": "Unsaid : Aura",
        "category": "fragrance",
        "tags": ["aura", "pear", "mandarin", "tuberose", "vanilla", "radiant", "soft"],
        "content": "Aura opens with pear, mandarin, and neroli; moves into tuberose, ylang-ylang, and orange blossom; and settles into vanilla, white musk, and blonde woods. It is radiant, soft, and close to the skin, suited to daytime romance, warm weather, and customers who want glow rather than force.",
    },
    {
        "document_key": "fragrance-echo",
        "title": "Unsaid : Echo",
        "category": "fragrance",
        "tags": ["echo", "incense", "smoke", "patchouli", "woods", "nocturnal", "mysterious"],
        "content": "Echo opens with incense, cypress, and black pepper; moves into violet leaf, labdanum, and clove bud; and settles into patchouli, smoked woods, and amber resin. It is smoky, nocturnal, mysterious, and best for evening wear, dates, winter, and customers who want a memorable trace.",
    },
    {
        "document_key": "fragrance-velvet",
        "title": "Unsaid : Velvet",
        "category": "fragrance",
        "tags": ["velvet", "plum", "rose", "suede", "tonka", "amber", "sweet", "date"],
        "content": "Velvet opens with plum, saffron, and cinnamon bark; moves into rose, suede, and heliotrope; and settles into tonka bean, amber, and vanilla. It is sensual, textured, warm, and ideal for after-dark elegance, gifting, romantic evenings, and customers who want magnetic softness.",
    },
    {
        "document_key": "house-philosophy",
        "title": "UNSAID House Philosophy",
        "category": "brand",
        "tags": ["house", "brand", "paris", "extrait", "black glass", "luxury"],
        "content": "UNSAID is an architectural fragrance house. Every composition is Extrait de Parfum, bottled in 30ml black glass, and formulated with a Parisian discipline of restraint, material clarity, and quiet presence. The house avoids spectacle and focuses on texture, atmosphere, and memory.",
    },
    {
        "document_key": "shipping-service",
        "title": "Shipping and Service",
        "category": "service",
        "tags": ["shipping", "delivery", "service", "consultation", "order"],
        "content": "UNSAID provides complimentary shipping, direct WhatsApp ordering, and private fragrance consultation. Orders should include the product slug, concentration, price, customer name, phone, shipping address, and city for fast fulfilment.",
    },
)


async def seed_knowledge_documents(session: AsyncSession) -> None:
    result = await session.execute(select(KnowledgeDocument.document_key))
    existing_keys = set(result.scalars().all())
    documents = [
        KnowledgeDocument(**document)
        for document in KNOWLEDGE_DOCUMENTS
        if str(document["document_key"]) not in existing_keys
    ]
    if not documents:
        return
    session.add_all(documents)
    await session.commit()
