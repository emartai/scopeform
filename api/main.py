from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from api.core.config import get_settings
from api.core.database import check_database_connection, engine
from api.core.openapi import build_openapi_schema
from api.core.redis import check_redis_connection, redis_client
from api.routers import agents, auth, logs, tokens

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_healthy = await check_database_connection()
    app.state.redis_healthy = await check_redis_connection()

    try:
        yield
    finally:
        await engine.dispose()
        close = getattr(redis_client, "aclose", None) or getattr(redis_client, "close", None)
        if close is not None:
            result = close()
            if result is not None:
                await result


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="Scopeform API",
        description="Identity and access management for AI agents",
        version="0.1.0",
        contact={"name": "Scopeform", "url": "https://scopeform.dev"},
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        redoc_url="/api/v1/redoc",
    )
    app.state.limiter = auth.limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    api_router = APIRouter(prefix="/api/v1")

    @api_router.get("/health")
    async def health() -> dict[str, bool | str]:
        return {
            "status": "ok",
            "db": bool(getattr(app.state, "db_healthy", False)),
            "redis": bool(getattr(app.state, "redis_healthy", False)),
        }

    api_router.include_router(auth.router)
    api_router.include_router(agents.router)
    api_router.include_router(tokens.router)
    api_router.include_router(logs.router)
    app.include_router(api_router)
    app.openapi = lambda: build_openapi_schema(app)

    return app


app = create_app()
