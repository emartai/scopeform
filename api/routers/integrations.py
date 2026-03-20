from __future__ import annotations

import uuid

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.database import get_db
from api.core.deps import get_current_org_id
from api.models.integration import OrgIntegration
from api.schemas.integration import (
    IntegrationListResponse,
    IntegrationResponse,
    IntegrationUpsertRequest,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

SUPPORTED_SERVICES = ("openai", "anthropic", "github")


def _fernet() -> Fernet:
    key = get_settings().encryption_key
    if not key:
        raise HTTPException(503, detail="Encryption key not configured.")
    return Fernet(key.encode())


def _encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as e:
        raise HTTPException(500, detail="Failed to decrypt stored key.") from e


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> IntegrationListResponse:
    rows = (
        await db.execute(
            select(OrgIntegration).where(OrgIntegration.org_id == org_id)
        )
    ).scalars().all()

    configured = {r.service: r for r in rows}
    items = [
        IntegrationResponse(
            service=svc,
            configured=svc in configured,
            updated_at=configured[svc].updated_at.isoformat() if svc in configured else None,
        )
        for svc in SUPPORTED_SERVICES
    ]
    return IntegrationListResponse(items=items)


@router.put("/{service}", response_model=IntegrationResponse)
async def upsert_integration(
    service: str,
    payload: IntegrationUpsertRequest,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> IntegrationResponse:
    if service not in SUPPORTED_SERVICES:
        raise HTTPException(400, detail=f"Unsupported service: {service}")

    existing = await db.scalar(
        select(OrgIntegration).where(
            OrgIntegration.org_id == org_id,
            OrgIntegration.service == service,
        )
    )

    encrypted = _encrypt(payload.api_key)

    if existing:
        existing.encrypted_api_key = encrypted
        from datetime import UTC, datetime
        existing.updated_at = datetime.now(UTC)
    else:
        db.add(OrgIntegration(org_id=org_id, service=service, encrypted_api_key=encrypted))

    await db.commit()

    row = await db.scalar(
        select(OrgIntegration).where(
            OrgIntegration.org_id == org_id,
            OrgIntegration.service == service,
        )
    )
    return IntegrationResponse(
        service=service,
        configured=True,
        updated_at=row.updated_at.isoformat() if row else None,
    )


@router.delete("/{service}")
async def delete_integration(
    service: str,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    row = await db.scalar(
        select(OrgIntegration).where(
            OrgIntegration.org_id == org_id,
            OrgIntegration.service == service,
        )
    )
    if row:
        await db.delete(row)
        await db.commit()
    return Response(status_code=204)
