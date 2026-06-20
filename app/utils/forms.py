from urllib.parse import parse_qs

from fastapi import Request


async def parse_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    form = parse_qs(body, keep_blank_values=True)
    return {key: values[-1].strip() for key, values in form.items() if values}