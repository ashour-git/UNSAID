from urllib.parse import parse_qs

from fastapi import Request


async def parse_form(request: Request) -> dict[str, str]:
    cached_form = getattr(request.state, "parsed_form", None)
    if isinstance(cached_form, dict) and cached_form:
        return cached_form

    try:
        form = await request.form()
        if form:
            return {
                key: str(value).strip()
                for key, value in form.items()
                if value is not None
            }
    except Exception:
        pass

    body = (await request.body()).decode("utf-8")
    form = parse_qs(body, keep_blank_values=True)
    return {key: values[-1].strip() for key, values in form.items() if values}
