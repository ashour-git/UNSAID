from datetime import datetime, timezone

from fastapi.templating import Jinja2Templates

from app.core.config import settings


def inject_now_context(request):
    return {"now": datetime.now(timezone.utc)}

def inject_settings_context(request):
    return {"settings": settings}

templates = Jinja2Templates(
    directory=settings.templates_dir,
    context_processors=[inject_now_context, inject_settings_context],
)
