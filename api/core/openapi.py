from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def build_openapi_schema(app: FastAPI) -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    app.openapi_schema = get_openapi(
        title="Scopeform API",
        description="Identity and access management for AI agents",
        version="0.1.0",
        contact={"name": "Scopeform", "url": "https://scopeform.dev"},
        routes=app.routes,
    )
    return app.openapi_schema
