"""Main FastAPI app instance declaration."""

from typing import Callable
import logging

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.api import api_router
from app.core import config

DEBUG = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(
    title=config.settings.PROJECT_NAME,
    version=config.settings.VERSION,
    description=config.settings.DESCRIPTION,
    redoc_url=None,
    openapi_url="/openapi.json" if DEBUG else None,
    docs_url="/" if DEBUG else None,
)


@app.get("/health")
async def health_route():
    return "ok"


app.include_router(api_router)


class RouterCacheControlResetMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        response.headers.update({"Cache-Control": "no-cache"})
        return response


app.add_middleware(RouterCacheControlResetMiddleware)

# Sets all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in config.settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Guards against HTTP Host Header attacks
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.settings.ALLOWED_HOSTS)


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url(
        url=f"rediss://{config.settings.CACHE_USER}:"
            f"{config.settings.CACHE_PASSWORD}@"
            f"{config.settings.CACHE_HOST}:"
            f"{config.settings.CACHE_PORT}"
    )
    
    FastAPICache.init(RedisBackend(redis), prefix="")


@app.get("/")
async def get_documentation(password: str | None = None):
    if password == config.settings.DOCS_PASSWORD:
        return get_swagger_ui_html(
            openapi_url=f"/openapi.json?password={password}", title="docs"
        )
    
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Contact support"
    )


@app.get("/openapi.json")
async def openapi(password: str | None = None):
    if password == config.settings.DOCS_PASSWORD:
        return get_openapi(
            title=config.settings.PROJECT_NAME,
            version=config.settings.VERSION,
            routes=app.routes,
        )
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Contact support"
    )


@app.get('/merchant/openapi.json',
         include_in_schema=False)
async def openapi():
    return JSONResponse(
        get_openapi(title='Merchant H2H API',
                    version='2.0.0',
                    description='API using x-token',
                    routes=[i for i in app.routes if i.__getattribute__('path').startswith('/merchant')]))


@app.get("/merchant", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url=f"/merchant/openapi.json", title="H2H Docs"
    )
