from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.media import CAMPAIGN_IMAGES, campaign_image_for_index
from app.core.templates import templates
from app.db.session import get_db
from app.models.product import Product
from app.services.analytics import record_event

router = APIRouter(tags=["Pages"])


def now_context() -> dict[str, object]:
    return {"now": datetime.now(timezone.utc)}


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(select(Product).order_by(Product.id))
    products = list(result.scalars().all())
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "campaign_images": CAMPAIGN_IMAGES,
            "products": products,
            **now_context(),
        },
    )


@router.get("/products/{dynamic_slug}", response_class=HTMLResponse)
async def product_detail(
    dynamic_slug: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(
        select(Product).where(Product.dynamic_slug == dynamic_slug)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found",
        )
    await record_event(
        session,
        "product_view",
        product_id=product.id,
        metadata={"slug": dynamic_slug},
    )
    await session.commit()

    related_result = await session.execute(
        select(Product).where(Product.dynamic_slug != dynamic_slug).order_by(Product.id).limit(3)
    )
    related_products = list(related_result.scalars().all())

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "campaign_image": campaign_image_for_index(product.id - 1),
            "product": product,
            "related_products": related_products,
            **now_context(),
        },
    )


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="legal_page.html",
        context={
            "title": "Privacy",
            "eyebrow": "Legal",
            "sections": [
                {
                    "heading": "Information we collect",
                    "paragraphs": [
                        "UNSAID collects only the information required to process orders, provide customer support, and improve the fragrance consultation experience.",
                        "This may include your name, phone number, shipping address, city, and any messages sent through the consultant or order flows.",
                    ],
                },
                {
                    "heading": "How we use information",
                    "paragraphs": [
                        "Your information is used to fulfill orders, coordinate delivery, and support private consultation services.",
                        "UNSAID does not sell personal data. Communication is limited to order fulfilment, customer care, and optional release updates.",
                    ],
                },
                {
                    "heading": "Data retention",
                    "paragraphs": [
                        "UNSAID retains order and account data for the duration of the customer relationship and for 24 months after the last order. After this period, personal data is anonymised or deleted. Aggregate analytics data is retained indefinitely in anonymised form.",
                    ],
                },
                {
                    "heading": "Your rights",
                    "paragraphs": [
                        "You may request access to, correction of, or deletion of your personal data at any time. Contact UNSAID directly through the contact page. Requests are processed within 30 days. You also have the right to data portability and to withdraw consent for marketing communications.",
                    ],
                },
                {
                    "heading": "Data handling",
                    "paragraphs": [
                        "Reasonable technical and operational safeguards are used to protect order and consultation data.",
                        "If you would like your correspondence deleted or reviewed, contact UNSAID directly through the contact page.",
                    ],
                },
                {
                    "heading": "Third-party services",
                    "paragraphs": [
                        "UNSAID uses Groq for AI consultation services. No personal data is shared with Groq. WhatsApp is used for order confirmation. Please refer to their respective privacy policies. This site does not use third-party tracking or advertising cookies.",
                    ],
                },
            ],
            **now_context(),
        },
    )


@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="legal_page.html",
        context={
            "title": "Terms",
            "eyebrow": "Legal",
            "sections": [
                {
                    "heading": "Orders",
                    "paragraphs": [
                        "Orders placed through the UNSAID site are subject to product availability and confirmation through the order channel.",
                        "Submitting an order request does not create a final sale until availability and fulfilment details are confirmed.",
                    ],
                },
                {
                    "heading": "Refund and return policy",
                    "paragraphs": [
                        "Due to the intimate nature of fragrance products, returns are accepted only for unopened items within 14 days of delivery. Contact the order desk for return authorization. Refunds are processed within 14 business days of receiving the returned item. Shipping costs are non-refundable.",
                    ],
                },
                {
                    "heading": "Product presentation",
                    "paragraphs": [
                        "UNSAID takes care to present each fragrance accurately, but small differences in display color, lighting, or packaging detail may occur.",
                        "All fragrances are sold as 30ml Extrait de Parfum unless otherwise stated.",
                    ],
                },
                {
                    "heading": "Use of the site",
                    "paragraphs": [
                        "The site and its contents are provided for personal, non-commercial browsing and ordering purposes.",
                        "Any misuse of the site, its content, or its ordering systems may result in refusal of service.",
                    ],
                },
                {
                    "heading": "Intellectual property",
                    "paragraphs": [
                        "All content on this site, including fragrance compositions, descriptions, images, and the UNSAID name, is the exclusive intellectual property of UNSAID. Reproduction, distribution, or use without written permission is prohibited.",
                    ],
                },
                {
                    "heading": "Limitation of liability",
                    "paragraphs": [
                        "UNSAID provides this site and its products on an 'as is' basis. UNSAID is not liable for indirect, incidental, or consequential damages arising from the use of this site or its products. Our total liability is limited to the purchase price of the product in question.",
                    ],
                },
                {
                    "heading": "Governing law",
                    "paragraphs": [
                        "These terms are governed by the laws of France. Any disputes shall be resolved in the courts of Paris.",
                    ],
                },
            ],
            **now_context(),
        },
    )


@router.get("/shipping", response_class=HTMLResponse)
async def shipping_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="legal_page.html",
        context={
            "title": "Shipping",
            "eyebrow": "Service",
            "sections": [
                {
                    "heading": "Fulfilment",
                    "paragraphs": [
                        "UNSAID ships orders after direct confirmation through the order channel.",
                        "Standard processing typically begins within 48 hours once the order details are confirmed.",
                    ],
                },
                {
                    "heading": "Delivery",
                    "paragraphs": [
                        "Delivery timing varies by city and region. Customers receive fulfilment guidance during confirmation.",
                        "Shipping support is available through WhatsApp and direct correspondence.",
                    ],
                },
                {
                    "heading": "Address quality",
                    "paragraphs": [
                        "To avoid delays, include a complete shipping address, phone number, and city when ordering.",
                        "UNSAID may request additional delivery details before dispatching a fragrance.",
                    ],
                },
            ],
            **now_context(),
        },
    )


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="contact_page.html",
        context=now_context(),
    )


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt(session: AsyncSession = Depends(get_db)) -> PlainTextResponse:
    sitemap_url = f"{settings.site_url}/sitemap.xml"
    content = f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /account
Disallow: /api/

Sitemap: {sitemap_url}
"""
    return PlainTextResponse(content)


@router.get("/sitemap.xml", response_class=Response)
async def sitemap_xml(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Response:
    result = await session.execute(select(Product).order_by(Product.id))
    products = list(result.scalars().all())

    urls = []
    urls.append(f"  <url><loc>{settings.site_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>")
    urls.append(f"  <url><loc>{settings.site_url}/contact</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>")
    urls.append(f"  <url><loc>{settings.site_url}/privacy</loc><changefreq>yearly</changefreq><priority>0.1</priority></url>")
    urls.append(f"  <url><loc>{settings.site_url}/terms</loc><changefreq>yearly</changefreq><priority>0.1</priority></url>")
    urls.append(f"  <url><loc>{settings.site_url}/shipping</loc><changefreq>yearly</changefreq><priority>0.1</priority></url>")

    for product in products:
        urls.append(
            f"  <url><loc>{settings.site_url}/products/{product.dynamic_slug}</loc>"
            f"<changefreq>weekly</changefreq><priority>0.8</priority></url>"
        )

    content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>"
    return Response(content=content, media_type="application/xml")