from app.main import create_app

# Vercel's Python runtime imports this ASGI app as the serverless entrypoint.
# Vercel serverless should not run startup DB seeding/migrations on every cold start.
app = create_app(enable_lifespan=False)
