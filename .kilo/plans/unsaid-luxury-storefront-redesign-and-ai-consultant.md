# UNSAID Luxury Storefront Redesign + AI Consultant Plan

## Goal
Redesign the UNSAID storefront into a truly high-end perfume e-commerce experience and stabilize the AI consultant so it behaves like a private perfumer rather than a generic chatbot.

## Current Findings
- The storefront direction is not yet premium enough because the visual hierarchy is inconsistent:
  - contrast is too weak in secondary text,
  - the six fragrances are not presented as six distinct collectible objects,
  - campaign mood imagery is overpowering product identity,
  - typography and card composition are not yet senior-level luxury e-commerce.
- The AI consultant failure was real:
  - chat form parsing originally relied on `request.form()` and broke without `python-multipart`,
  - RAG startup was heavier than necessary for a tiny fixed catalog,
  - the chat interaction reads like support software instead of a private perfume consultation.

## Locked Decisions

### Brand + Visual Direction
- Imagery source: commercial-use, logo-free, high-resolution editorial still-life imagery.
- Art direction: **stone + black glass**.
- Homepage hierarchy: **collection-first**.
- First screen: **dominant bottle hero**.
- Collection cards: **structured essentials by default**.
- Consultant interaction: **guided-first, freeform-second**.

### AI + Technical Direction
- AI model provider: Groq.
- Consultant tone: private perfumer / luxury fragrance advisor.
- Retrieval: fast database-backed retrieval, not heavy startup-first embedding flow.
- Fallback: if Groq fails, respond from house knowledge gracefully.
- Consultant UX: guided prompts first, free typing second.

## Target Experience

### Homepage
- First fold must immediately read as perfume authority, not editorial ambiguity.
- One dominant black-glass bottle anchored in stone/still-life composition.
- Editorial copy stays restrained and short.
- Collection appears above the fold or immediately below with strong continuity from hero.

### Collection Grid
Each card should show by default:
- bottle visual,
- product name,
- subtitle,
- concentration + volume,
- price,
- one short architecture line or compact note signal,
- CTA.

Do **not** rely on repeated campaign-image-only tiles. Each of the six SKUs must read as its own object with its own temperature.

### Product Detail
- Strong bottle-led presentation.
- Cleaner hierarchy between hero image, product facts, notes, and purchase CTA.
- Detail page should feel like a private appointment, not a generic product page.

### AI Consultant
- Floating/private consultation UI, not “support widget” styling.
- Start with curated prompt chips, then allow free typing.
- Every reply should feel concise, elegant, and useful.
- Should recommend one lead fragrance and optionally one alternative.

## Implementation Tasks

### 1. Stabilize the AI Consultant Backend
1. Replace any fragile form parsing with body parsing that works reliably with HTMX URL-encoded payloads.
2. Keep Groq access behind configuration.
3. Add graceful fallback when:
   - key is missing,
   - provider fails,
   - network times out,
   - upstream response is empty.
4. Enforce short luxury-consultant answers.
5. Avoid exposing implementation details in AI output.

### 2. Add a Professional Knowledge Base Layer
1. Create a `KnowledgeDocument` model for RAG documents.
2. Seed knowledge for:
   - all 6 fragrances,
   - house philosophy,
   - service / shipping / ordering.
3. Ensure startup seeds both products and knowledge documents.
4. Keep knowledge document categories and tags queryable for future refinement.

### 3. Replace Heavy/Fragile Retrieval with Fast DB Retrieval
1. Use database-backed retrieval over a small curated knowledge corpus.
2. Prefer lightweight lexical or hybrid scoring suitable for a tiny luxury catalog.
3. Keep retrieval fast enough for chat UX without model warmup bottlenecks.
4. Return top relevant documents to the prompt builder.

### 4. Redesign the Global Visual System
1. Rework palette so it is less bright and more sophisticated:
   - darker warm-stone base,
   - stronger charcoal/dark text,
   - more disciplined bronze accent usage,
   - clearer hierarchy between background, border, and content planes.
2. Increase contrast of secondary text and labels.
3. Keep typography elegant but more authoritative:
   - strong display serif for perfume/editorial moments,
   - disciplined sans-serif for UI.
4. Remove any “template-looking” visual patterns.

### 5. Rebuild the Six Fragrance Cards
1. Stop using campaign atmosphere as the main identity layer.
2. Make each product card bottle-led.
3. Ensure all six cards feel like premium objects rather than variants of one tile.
4. Use structured essentials by default.
5. Keep full note breakdown or deeper detail for hover / click / detail page.
6. Ensure the cards remain elegant across mobile, tablet, and desktop.

### 6. Refine the Chat UX
1. Show both user message and AI response.
2. Add tasteful loading state.
3. Improve consultant header copy and trust framing.
4. Make prompt chips the first interaction.
5. Keep the visual styling integrated with the site’s luxury system.

### 7. Refine Conversion UX
1. Keep the order drawer but polish it to match luxury tone.
2. Ensure CTA hierarchy is clear across:
   - hero,
   - product cards,
   - product detail,
   - quiz result,
   - AI consultant outputs when appropriate.
3. Preserve WhatsApp dispatch flow.

## Design Rules To Maintain
- No logos, watermarks, visible IDs, or off-brand commercial imagery.
- No generic startup-chat UI patterns.
- No overuse of bright cream backgrounds.
- No repeated low-identity product cards.
- No heavy AI startup path that delays first response unnecessarily.
- No marketing-cliche copy.

## Risks
- Commercial-use image sourcing must be legally safe and visually consistent.
- Over-indexing on mood imagery can weaken product authority again.
- Groq failures must never break the storefront UX.
- If retrieval quality is weak, the consultant will feel generic even if visually polished.

## Validation Plan

### Backend
- Verify app imports cleanly.
- Verify startup creates/uses both product and knowledge tables.
- Verify `/api/chat/message` returns `200` for valid HTMX-style requests.
- Verify consultant still responds meaningfully when Groq is unavailable.
- Verify `/health` remains healthy.

### Frontend
- Verify hero reads immediately as perfume luxury, not generic editorial.
- Verify all six cards feel distinct and premium.
- Verify text contrast is readable across screens.
- Verify chat widget looks like a private perfumer, not support chat.
- Verify mobile layout remains elegant and conversion-safe.
- Verify product detail page feels stronger than the current collection cards.

## Suggested Implementation Order
1. Fix chat robustness and fallback behavior.
2. Add/seed knowledge documents.
3. Replace retrieval path with fast DB-backed retrieval.
4. Rebuild palette + contrast system.
5. Redesign hero.
6. Redesign six product cards.
7. Refine product detail and chat UI.
8. Run visual + endpoint verification.

## Security Note
The Groq key was provided directly in conversation context. After implementation, rotate that key and move forward using environment-only secret management.
