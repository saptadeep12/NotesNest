import re

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    is_file = re.fullmatch(r"/api/v1/resources/\d+/file", path) is not None
    if (
        request.method == "GET"
        and 200 <= response.status_code < 300
        and path.startswith("/api/v1")
        and path != "/api/v1/health"
        and not is_file
    ):
        response.headers["Cache-Control"] = (
            "public, max-age=0, s-maxage=300, stale-while-revalidate=600"
        )
    return response


app.include_router(api_router)
